"""
视频处理服务 - 后台异步处理视频分析任务
"""
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import cv2
import json

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from ..core.config import settings, STUDENT_BEHAVIORS, TEACHER_BEHAVIORS, SCENE_ELEMENTS
from ..core.database import engine
from ..models.video import Video, VideoStatus
from ..models.analysis import AnalysisTimeline, AnalysisSummary, AnalysisAnomaly

logger = logging.getLogger(__name__)


async def process_video_task(video_id: int, video_path: str):
    """
    后台视频处理任务
    
    流程:
    1. 读取视频元数据
    2. 抽帧并进行 AI 检测
    3. 聚合检测结果
    4. 存储分析数据
    5. 更新视频状态
    """
    # 创建新的数据库会话
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as db:
        try:
            # 获取视频记录
            result = await db.execute(select(Video).where(Video.id == video_id))
            video = result.scalar_one_or_none()
            
            if not video:
                logger.error(f"视频 {video_id} 不存在")
                return
            
            # 更新状态为处理中
            video.status = VideoStatus.PROCESSING.value
            await db.commit()
            
            # 读取视频元数据
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise Exception(f"无法打开视频文件: {video_path}")
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = total_frames / fps if fps > 0 else 0
            
            # 更新视频元数据
            video.fps = fps
            video.total_frames = total_frames
            video.duration = duration
            video.resolution = f"{width}x{height}"
            await db.commit()
            
            # 初始化检测器（延迟导入避免启动时加载模型）
            detector = await get_detector()
            
            # 抽帧分析
            frame_interval = int(fps / settings.VIDEO_PROCESS_FPS) if fps > 0 else 30
            current_frame = 0
            window_size = 10  # 10秒窗口
            window_data = {}  # 按时间窗口聚合的数据
            all_behavior_counts = {}  # 全局统计
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if current_frame % frame_interval == 0:
                    # 进行检测
                    timestamp = int(current_frame / fps) if fps > 0 else 0
                    window_key = (timestamp // window_size) * window_size
                    
                    if detector:
                        detections = await detector.detect(frame)
                    else:
                        # 如果没有检测器，生成模拟数据
                        detections = generate_mock_detections(timestamp)
                    
                    # 聚合到时间窗口
                    if window_key not in window_data:
                        window_data[window_key] = {
                            "behavior_counts": {},
                            "detections": []
                        }
                    
                    for det in detections:
                        category = det.get("category", "unknown")
                        
                        # 更新窗口内计数
                        if category not in window_data[window_key]["behavior_counts"]:
                            window_data[window_key]["behavior_counts"][category] = 0
                        window_data[window_key]["behavior_counts"][category] += 1
                        
                        # 更新全局计数
                        if category not in all_behavior_counts:
                            all_behavior_counts[category] = {"count": 0, "frames": set()}
                        all_behavior_counts[category]["count"] += 1
                        all_behavior_counts[category]["frames"].add(timestamp)
                        
                        # 存储检测详情（可选）
                        window_data[window_key]["detections"].append(det)
                    
                    # 更新进度
                    video.progress = current_frame / total_frames
                    video.current_frame = current_frame
                    await db.commit()
                
                current_frame += 1
            
            cap.release()
            
            # 存储时间线数据
            for timestamp, data in window_data.items():
                timeline_entry = AnalysisTimeline(
                    video_id=video_id,
                    timestamp=timestamp,
                    window_size=window_size,
                    behavior_counts=data["behavior_counts"],
                    detections=data.get("detections")[:10] if data.get("detections") else None  # 限制存储量
                )
                db.add(timeline_entry)
            
            # 计算汇总统计
            behavior_summary = {}
            for category, data in all_behavior_counts.items():
                count = data["count"]
                # 估算时长：出现的独立秒数
                total_duration = len(data["frames"])
                percentage = (total_duration / duration * 100) if duration > 0 else 0
                
                behavior_summary[category] = {
                    "count": count,
                    "total_duration": total_duration,
                    "percentage": round(percentage, 1)
                }
            
            # 计算关键指标
            discuss_duration = behavior_summary.get("discuss", {}).get("total_duration", 0)
            bowhead_duration = behavior_summary.get("BowHead", {}).get("total_duration", 0)
            handraising_count = behavior_summary.get("hand-raising", {}).get("count", 0)
            
            interaction_rate = discuss_duration / duration if duration > 0 else 0
            attention_rate = 1 - (bowhead_duration / duration) if duration > 0 else 1
            engagement_score = min(1.0, (interaction_rate + (handraising_count / 50)) / 2)
            
            # 存储汇总数据
            summary = AnalysisSummary(
                video_id=video_id,
                summary_json={"behavior_summary": behavior_summary},
                total_detections=sum(d["count"] for d in all_behavior_counts.values()),
                interaction_rate=interaction_rate,
                attention_rate=attention_rate,
                engagement_score=engagement_score
            )
            db.add(summary)
            
            # 检测异常时段
            anomalies = detect_anomalies(window_data, window_size, duration)
            for anomaly in anomalies:
                anomaly_entry = AnalysisAnomaly(
                    video_id=video_id,
                    start_time=anomaly["start_time"],
                    end_time=anomaly["end_time"],
                    anomaly_type=anomaly["type"],
                    severity=anomaly["severity"],
                    description=anomaly["description"],
                    behavior_stats=anomaly.get("behavior_stats")
                )
                db.add(anomaly_entry)
            
            # 更新视频状态为完成
            video.status = VideoStatus.COMPLETED.value
            video.progress = 1.0
            video.processed_at = datetime.utcnow()
            await db.commit()
            
            logger.info(f"视频 {video_id} 处理完成")
            
        except Exception as e:
            logger.exception(f"视频 {video_id} 处理失败: {e}")
            
            # 更新状态为失败
            try:
                video.status = VideoStatus.FAILED.value
                video.error_message = str(e)
                await db.commit()
            except:
                pass


async def get_detector():
    """获取检测器实例（延迟加载）"""
    try:
        from ..ml.detector import MultiModelDetector
        detector = MultiModelDetector()
        if detector.is_loaded:
            return detector
        return None
    except ImportError:
        logger.warning("检测器模块未找到，将使用模拟数据")
        return None
    except Exception as e:
        logger.warning(f"检测器加载失败: {e}，将使用模拟数据")
        return None


def generate_mock_detections(timestamp: int) -> List[Dict[str, Any]]:
    """生成模拟检测数据（用于开发和测试）"""
    import random
    
    detections = []
    
    # 根据时间段生成不同的模拟数据
    # 模拟课堂的自然变化
    if timestamp < 300:  # 前5分钟：开课阶段
        behaviors = [("teacher", 0.9), ("stand", 0.3), ("read", 0.2)]
    elif timestamp < 1200:  # 5-20分钟：授课阶段
        behaviors = [("teacher", 0.9), ("read", 0.4), ("write", 0.3), ("hand-raising", 0.1)]
    elif timestamp < 1800:  # 20-30分钟：互动阶段
        behaviors = [("teacher", 0.9), ("discuss", 0.5), ("guide", 0.3), ("hand-raising", 0.2)]
    elif timestamp < 2400:  # 30-40分钟：练习阶段
        behaviors = [("teacher", 0.8), ("write", 0.5), ("read", 0.3), ("BowHead", 0.2)]
    else:  # 40分钟后：总结阶段
        behaviors = [("teacher", 0.9), ("blackboard-writing", 0.3), ("read", 0.2)]
    
    for category, prob in behaviors:
        if random.random() < prob:
            # 随机数量
            count = random.randint(1, 5) if category in STUDENT_BEHAVIORS else 1
            for _ in range(count):
                detections.append({
                    "category": category,
                    "bbox": [random.randint(0, 800), random.randint(0, 600), 
                             random.randint(50, 150), random.randint(50, 150)],
                    "score": random.uniform(0.5, 0.95)
                })
    
    return detections


def detect_anomalies(window_data: Dict, window_size: int, duration: float) -> List[Dict]:
    """检测异常时段"""
    anomalies = []
    
    # 检测持续低头的时段
    consecutive_high_bowhead = 0
    bowhead_start = None
    
    for timestamp in sorted(window_data.keys()):
        data = window_data[timestamp]
        counts = data.get("behavior_counts", {})
        
        bowhead_count = counts.get("BowHead", 0)
        total_student_behaviors = sum(counts.get(b, 0) for b in STUDENT_BEHAVIORS)
        
        if total_student_behaviors > 0:
            bowhead_rate = bowhead_count / total_student_behaviors
            
            if bowhead_rate > 0.3:  # 低头率超过30%
                if bowhead_start is None:
                    bowhead_start = timestamp
                consecutive_high_bowhead += 1
            else:
                if consecutive_high_bowhead >= 3:  # 持续3个窗口以上
                    anomalies.append({
                        "start_time": bowhead_start,
                        "end_time": timestamp,
                        "type": "high_bowhead_rate",
                        "severity": "high" if consecutive_high_bowhead >= 6 else "medium",
                        "description": f"低头率持续偏高（>{30}%），持续{consecutive_high_bowhead * window_size}秒",
                        "behavior_stats": {"BowHead": {"rate": bowhead_rate}}
                    })
                bowhead_start = None
                consecutive_high_bowhead = 0
    
    # 检测互动不足的时段
    no_interaction_start = None
    no_interaction_count = 0
    
    for timestamp in sorted(window_data.keys()):
        data = window_data[timestamp]
        counts = data.get("behavior_counts", {})
        
        discuss_count = counts.get("discuss", 0)
        handraising_count = counts.get("hand-raising", 0)
        
        if discuss_count == 0 and handraising_count == 0:
            if no_interaction_start is None:
                no_interaction_start = timestamp
            no_interaction_count += 1
        else:
            if no_interaction_count >= 6:  # 持续6个窗口（60秒）以上没有互动
                anomalies.append({
                    "start_time": no_interaction_start,
                    "end_time": timestamp,
                    "type": "low_interaction_rate",
                    "severity": "medium",
                    "description": f"连续{no_interaction_count * window_size}秒无课堂互动",
                    "behavior_stats": None
                })
            no_interaction_start = None
            no_interaction_count = 0
    
    return anomalies





