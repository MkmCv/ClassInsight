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

    时间聚合（详见仓库 docs/TIME_AGGREGATION.md）:
    固定 window_size 秒的非重叠窗，window_key = (timestamp // window_size) * window_size；
    每窗内累加原始类别与分类后师生行为，最后每窗写入一条 AnalysisTimeline。
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
            
            # 初始化行为分类器
            from ..ml.behavior_classifier import get_classifier
            behavior_classifier = get_classifier()
            
            # 抽帧分析（仅对采样帧做检测；聚合只影响「每窗计数」，不强制每秒钟都有样本）
            frame_interval = int(fps / settings.VIDEO_PROCESS_FPS) if fps > 0 else 30
            current_frame = 0
            # 时间窗长度（秒）；与 behavior_analyzer 中 lag*10 的「秒」约定一致
            window_size = 10
            # key = 窗起点秒数，value = 该窗内累加的计数与检测列表
            window_data = {}
            all_behavior_counts = {}  # 全局统计（原始类别）
            classified_behaviors = []  # 分类后的行为序列
            student_behavior_counts = {}  # 学生行为统计
            teacher_behavior_counts = {}  # 教师行为统计
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if current_frame % frame_interval == 0:
                    # 当前帧在视频中的时间（秒）→ 对齐到非重叠时间桶的起点，例如 23s → 20
                    timestamp = int(current_frame / fps) if fps > 0 else 0
                    window_key = (timestamp // window_size) * window_size
                    
                    if detector:
                        detections = await detector.detect(frame)
                    else:
                        # 如果没有检测器，生成模拟数据
                        detections = generate_mock_detections(timestamp)
                    
                    # 使用行为分类器进行分类
                    student_behavior, teacher_behavior = behavior_classifier.classify_frame(detections)
                    
                    # 存储分类结果
                    classified_behaviors.append({
                        "timestamp": timestamp,
                        "student_behavior": student_behavior,
                        "teacher_behavior": teacher_behavior,
                        "raw_detections": detections
                    })
                    
                    # 统计分类后的行为
                    if student_behavior:
                        if student_behavior not in student_behavior_counts:
                            student_behavior_counts[student_behavior] = {"count": 0, "frames": set(), "last_event_time": -10}
                        
                        # 特殊处理：学生举手需要3人及以上才算1次举手事件
                        if student_behavior == "学生举手":
                            # 统计该帧中实际检测到的举手人数
                            hand_raising_count = sum(1 for det in detections if det.get("category", "").lower() == "hand-raising")
                            if hand_raising_count >= 3:
                                # 3人及以上算1次举手事件
                                # 检查是否是新的事件（与上一事件间隔超过5秒算新事件，避免连续帧重复计数）
                                last_event_time = student_behavior_counts[student_behavior]["last_event_time"]
                                if timestamp - last_event_time > 5:  # 间隔超过5秒算新事件
                                    student_behavior_counts[student_behavior]["count"] += 1
                                    student_behavior_counts[student_behavior]["last_event_time"] = timestamp
                                # 记录该帧（用于时长统计）
                                student_behavior_counts[student_behavior]["frames"].add(timestamp)
                            # 如果少于3人，不计数（虽然分类器可能已经分类为"学生举手"，但统计时不计数）
                        else:
                            # 其他行为正常计数（按帧）
                            student_behavior_counts[student_behavior]["count"] += 1
                            student_behavior_counts[student_behavior]["frames"].add(timestamp)
                    
                    if teacher_behavior:
                        if teacher_behavior not in teacher_behavior_counts:
                            teacher_behavior_counts[teacher_behavior] = {"count": 0, "frames": set()}
                        teacher_behavior_counts[teacher_behavior]["count"] += 1
                        teacher_behavior_counts[teacher_behavior]["frames"].add(timestamp)
                    
                    # 时间聚合：同一 window_key 下跨多帧累加，得到「该 10s 段」的统计
                    if window_key not in window_data:
                        window_data[window_key] = {
                            "behavior_counts": {},
                            "detections": [],
                            "student_behaviors": {},
                            "teacher_behaviors": {}
                        }
                    
                    # 更新原始类别计数（用于兼容性）
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
                    
                    # 更新分类后的行为计数（按窗口）
                    if student_behavior:
                        if student_behavior not in window_data[window_key]["student_behaviors"]:
                            window_data[window_key]["student_behaviors"][student_behavior] = 0
                        
                        # 特殊处理：学生举手需要3人及以上才算1次
                        if student_behavior == "学生举手":
                            hand_raising_count = sum(1 for det in detections if det.get("category", "").lower() == "hand-raising")
                            if hand_raising_count >= 3:
                                # 检查窗口内是否已经计数过（避免同一窗口内重复计数）
                                # 每窗口最多计数1次举手事件
                                if window_data[window_key]["student_behaviors"][student_behavior] == 0:
                                    window_data[window_key]["student_behaviors"][student_behavior] = 1
                        else:
                            window_data[window_key]["student_behaviors"][student_behavior] += 1
                    
                    if teacher_behavior:
                        if teacher_behavior not in window_data[window_key]["teacher_behaviors"]:
                            window_data[window_key]["teacher_behaviors"][teacher_behavior] = 0
                        window_data[window_key]["teacher_behaviors"][teacher_behavior] += 1
                    
                    # 更新进度
                    video.progress = current_frame / total_frames
                    video.current_frame = current_frame
                    await db.commit()
                
                current_frame += 1
            
            cap.release()
            
            # 每窗一行入库：timestamp 即为 window_key（窗左端，单位秒）
            for timestamp, data in window_data.items():
                # 保持原有格式：直接使用原始 behavior_counts（确保前端兼容）
                behavior_counts = data["behavior_counts"].copy()
                
                # 如果有分类后的数据，添加到额外字段中（不影响原有格式）
                if data.get("student_behaviors") or data.get("teacher_behaviors"):
                    # 将分类后的数据也添加到主字典中（用于前端展示分类后的行为）
                    behavior_counts.update(data.get("student_behaviors", {}))
                    behavior_counts.update(data.get("teacher_behaviors", {}))
                    # 同时保存原始数据用于API选择
                    behavior_counts["_raw"] = data["behavior_counts"]
                    behavior_counts["_classified"] = {
                        "student_behaviors": data.get("student_behaviors", {}),
                        "teacher_behaviors": data.get("teacher_behaviors", {})
                    }
                
                timeline_entry = AnalysisTimeline(
                    video_id=video_id,
                    timestamp=timestamp,
                    window_size=window_size,
                    behavior_counts=behavior_counts,  # 保持原有格式，添加分类数据
                    detections=data.get("detections")[:10] if data.get("detections") else None  # 限制存储量
                )
                db.add(timeline_entry)
            
            # 计算汇总统计（包含原始和分类后的行为）
            behavior_summary = {}
            
            # 原始类别统计（用于兼容性）
            for category, data in all_behavior_counts.items():
                count = data["count"]
                total_duration = len(data["frames"])
                percentage = (total_duration / duration * 100) if duration > 0 else 0
                
                behavior_summary[category] = {
                    "count": count,
                    "total_duration": total_duration,
                    "percentage": round(percentage, 1),
                    "type": "raw"  # 标记为原始类别
                }
            
            # 分类后的学生行为统计
            student_behavior_summary = {}
            for behavior, data in student_behavior_counts.items():
                count = data["count"]
                total_duration = len(data["frames"])
                percentage = (total_duration / duration * 100) if duration > 0 else 0
                
                student_behavior_summary[behavior] = {
                    "count": count,
                    "total_duration": total_duration,
                    "percentage": round(percentage, 1)
                }
            
            # 分类后的教师行为统计
            teacher_behavior_summary = {}
            for behavior, data in teacher_behavior_counts.items():
                count = data["count"]
                total_duration = len(data["frames"])
                percentage = (total_duration / duration * 100) if duration > 0 else 0
                
                teacher_behavior_summary[behavior] = {
                    "count": count,
                    "total_duration": total_duration,
                    "percentage": round(percentage, 1)
                }
            
            # 合并到汇总数据
            behavior_summary["_classified"] = {
                "student_behaviors": student_behavior_summary,
                "teacher_behaviors": teacher_behavior_summary
            }
            
            # 计算关键指标（兼容原始和分类后的数据）
            # 讨论/互动时长：优先使用分类后的"讨论"，否则使用原始的"discuss"
            discuss_duration = (
                student_behavior_summary.get("讨论", {}).get("total_duration", 0) or
                behavior_summary.get("discuss", {}).get("total_duration", 0)
            )
            # 低头时长：使用原始数据（分类后可能包含在"其它"中）
            bowhead_duration = behavior_summary.get("BowHead", {}).get("total_duration", 0)
            # 举手次数：优先使用分类后的"学生举手"，否则使用原始的"hand-raising"
            handraising_count = (
                student_behavior_summary.get("学生举手", {}).get("count", 0) or
                behavior_summary.get("hand-raising", {}).get("count", 0)
            )
            
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



















