# -*- coding: utf-8 -*-
"""
课堂行为检测可视化脚本

功能：
1. 加载所有4个YOLO-vHeat模型
2. 对视频进行逐帧检测
3. 在视频上绘制检测框和标签
4. 输出带标注的可视化视频

使用方法：
    python visualize_detection.py [视频路径] [--output 输出路径] [--skip 跳帧数]
"""

import os
import sys
import cv2
import argparse
from pathlib import Path
from datetime import datetime
import numpy as np

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 颜色配置（BGR格式）
COLORS = {
    # 学生姿态 - 红色系
    'BowHead': (0, 0, 255),        # 红色 - 低头
    'TurnHead': (0, 100, 255),     # 橙红色 - 转头
    
    # 学习行为 - 绿色系
    'hand-raising': (0, 255, 0),   # 绿色 - 举手
    'read': (0, 200, 100),         # 青绿色 - 阅读
    'write': (0, 255, 200),        # 浅绿色 - 书写
    
    # 讨论 - 黄色
    'discuss': (0, 255, 255),      # 黄色 - 讨论
    
    # 教师行为 - 蓝色系
    'teacher': (255, 100, 0),      # 蓝色 - 教师
    'guide': (255, 200, 0),        # 浅蓝色 - 引导
    'answer': (255, 150, 100),     # 天蓝色 - 回答
    'On-stage interaction': (255, 0, 255),  # 紫色 - 上台互动
    'blackboard-writing': (200, 100, 50),   # 深蓝色 - 板书
    'stand': (255, 150, 0),        # 蓝绿色 - 站立
    
    # 场景元素 - 灰色系
    'screen': (200, 200, 0),       # 青色 - 屏幕
    'blackBoard': (100, 100, 100), # 灰色 - 黑板
}

# 中文标签映射
LABEL_CN = {
    'BowHead': '低头',
    'TurnHead': '转头',
    'hand-raising': '举手',
    'read': '阅读',
    'write': '书写',
    'discuss': '讨论',
    'teacher': '教师',
    'guide': '引导',
    'answer': '回答',
    'On-stage interaction': '上台互动',
    'blackboard-writing': '板书',
    'stand': '站立',
    'screen': '屏幕',
    'blackBoard': '黑板',
}

# 模型配置
MODEL_CONFIGS = {
    'comprehensive': {
        'weight_file': 'comprehensive_scene_best.pt',
        'classes': ['guide', 'answer', 'On-stage interaction', 'blackboard-writing', 
                   'teacher', 'stand', 'screen', 'blackBoard'],
    },
    'learning': {
        'weight_file': 'student_learning_best.pt',
        'classes': ['hand-raising', 'read', 'write'],
    },
    'discussion': {
        'weight_file': 'student_discussion_best.pt',
        'classes': ['discuss'],
    },
    'posture': {
        'weight_file': 'student_posture_best.pt',
        'classes': ['BowHead', 'TurnHead'],
    }
}


class DetectionVisualizer:
    """检测可视化器"""
    
    def __init__(self, weights_dir: str, confidence: float = 0.3):
        self.weights_dir = Path(weights_dir)
        self.confidence = confidence
        self.models = {}
        self._load_models()
    
    def _load_models(self):
        """加载所有模型"""
        try:
            from ultralytics import YOLO
            
            for model_key, config in MODEL_CONFIGS.items():
                weight_path = self.weights_dir / config['weight_file']
                
                if weight_path.exists():
                    print(f"✅ 加载模型: {model_key} ({config['weight_file']})")
                    model = YOLO(str(weight_path))
                    self.models[model_key] = {
                        'model': model,
                        'classes': config['classes']
                    }
                else:
                    print(f"⚠️ 模型不存在: {weight_path}")
            
            print(f"\n共加载 {len(self.models)} 个模型")
            
        except ImportError:
            print("❌ 请安装 ultralytics: pip install ultralytics")
            sys.exit(1)
    
    def detect_frame(self, frame: np.ndarray) -> list:
        """对单帧进行检测"""
        all_detections = []
        
        for model_key, model_info in self.models.items():
            model = model_info['model']
            classes = model_info['classes']
            
            try:
                results = model(frame, conf=self.confidence, verbose=False)
                
                for result in results:
                    boxes = result.boxes
                    if boxes is None:
                        continue
                    
                    for i in range(len(boxes)):
                        xyxy = boxes.xyxy[i].cpu().numpy()
                        conf = float(boxes.conf[i].cpu().numpy())
                        cls_id = int(boxes.cls[i].cpu().numpy())
                        
                        if cls_id < len(classes):
                            category = classes[cls_id]
                            all_detections.append({
                                'category': category,
                                'bbox': xyxy.tolist(),
                                'confidence': conf,
                                'model': model_key
                            })
            except Exception as e:
                print(f"⚠️ {model_key} 检测失败: {e}")
        
        return all_detections
    
    def draw_detections(self, frame: np.ndarray, detections: list) -> np.ndarray:
        """在帧上绘制检测结果"""
        frame = frame.copy()
        
        for det in detections:
            category = det['category']
            bbox = det['bbox']
            conf = det['confidence']
            
            x1, y1, x2, y2 = map(int, bbox)
            color = COLORS.get(category, (128, 128, 128))
            
            # 绘制边界框
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # 准备标签文本
            label_cn = LABEL_CN.get(category, category)
            label = f"{label_cn} {conf:.2f}"
            
            # 计算文本大小
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            thickness = 2
            (text_width, text_height), baseline = cv2.getTextSize(label, font, font_scale, thickness)
            
            # 绘制标签背景
            cv2.rectangle(frame, (x1, y1 - text_height - 10), (x1 + text_width + 10, y1), color, -1)
            
            # 绘制标签文本（使用英文，因为OpenCV对中文支持有限）
            label_en = f"{category} {conf:.2f}"
            cv2.putText(frame, label_en, (x1 + 5, y1 - 5), font, font_scale, (255, 255, 255), thickness)
        
        return frame
    
    def draw_info_panel(self, frame: np.ndarray, frame_idx: int, fps: float, 
                        detections: list, total_frames: int) -> np.ndarray:
        """绘制信息面板"""
        h, w = frame.shape[:2]
        
        # 统计各类别检测数量
        category_counts = {}
        for det in detections:
            cat = det['category']
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        # 绘制半透明信息面板
        overlay = frame.copy()
        panel_height = 120
        cv2.rectangle(overlay, (0, 0), (w, panel_height), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)
        
        # 标题
        cv2.putText(frame, "ClassInsight AI - Detection Visualization", 
                   (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # 进度信息
        progress = frame_idx / total_frames * 100 if total_frames > 0 else 0
        time_sec = frame_idx / fps if fps > 0 else 0
        info_text = f"Frame: {frame_idx}/{total_frames} | Time: {time_sec:.1f}s | Progress: {progress:.1f}%"
        cv2.putText(frame, info_text, (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        
        # 检测统计
        det_text = f"Detections: {len(detections)} | "
        det_text += " ".join([f"{k}:{v}" for k, v in list(category_counts.items())[:5]])
        cv2.putText(frame, det_text, (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 255, 150), 1)
        
        # 绘制进度条
        bar_width = w - 40
        bar_height = 8
        bar_y = panel_height - 15
        cv2.rectangle(frame, (20, bar_y), (20 + bar_width, bar_y + bar_height), (50, 50, 50), -1)
        progress_width = int(bar_width * progress / 100)
        cv2.rectangle(frame, (20, bar_y), (20 + progress_width, bar_y + bar_height), (0, 255, 0), -1)
        
        return frame
    
    def process_video(self, video_path: str, output_path: str, skip_frames: int = 1,
                      max_frames: int = None, show_preview: bool = False):
        """处理视频并生成可视化结果"""
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"❌ 无法打开视频: {video_path}")
            return
        
        # 获取视频信息
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"\n📹 视频信息:")
        print(f"   - 分辨率: {width}x{height}")
        print(f"   - 帧率: {fps:.2f} FPS")
        print(f"   - 总帧数: {total_frames}")
        print(f"   - 时长: {total_frames/fps:.1f} 秒")
        print(f"   - 跳帧: 每 {skip_frames} 帧检测一次")
        
        # 创建输出视频
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps / skip_frames, (width, height))
        
        print(f"\n🎬 开始处理...")
        
        frame_idx = 0
        processed = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if max_frames and frame_idx >= max_frames:
                break
            
            if frame_idx % skip_frames == 0:
                # 检测
                detections = self.detect_frame(frame)
                
                # 绘制检测结果
                frame = self.draw_detections(frame, detections)
                
                # 绘制信息面板
                frame = self.draw_info_panel(frame, frame_idx, fps, detections, total_frames)
                
                # 写入输出
                out.write(frame)
                processed += 1
                
                # 显示进度
                if processed % 10 == 0:
                    progress = frame_idx / total_frames * 100
                    print(f"   处理进度: {progress:.1f}% ({frame_idx}/{total_frames})")
                
                # 预览
                if show_preview:
                    preview = cv2.resize(frame, (width // 2, height // 2))
                    cv2.imshow('Detection Preview', preview)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
            
            frame_idx += 1
        
        cap.release()
        out.release()
        if show_preview:
            cv2.destroyAllWindows()
        
        print(f"\n✅ 处理完成!")
        print(f"   - 处理帧数: {processed}")
        print(f"   - 输出文件: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='课堂行为检测可视化')
    parser.add_argument('video', nargs='?', help='输入视频路径')
    parser.add_argument('--output', '-o', help='输出视频路径')
    parser.add_argument('--skip', '-s', type=int, default=5, help='跳帧数（默认5）')
    parser.add_argument('--max-frames', '-m', type=int, help='最大处理帧数')
    parser.add_argument('--confidence', '-c', type=float, default=0.3, help='置信度阈值')
    parser.add_argument('--preview', '-p', action='store_true', help='显示实时预览')
    parser.add_argument('--list', '-l', action='store_true', help='列出可用视频')
    
    args = parser.parse_args()
    
    # 路径配置（脚本位于 backend/scripts/，项目根为其上一级 backend/）
    script_dir = Path(__file__).parent.parent
    weights_dir = script_dir / 'app' / 'ml' / 'weights'
    videos_dir = script_dir / 'storage' / 'videos'
    output_dir = script_dir / 'storage' / 'visualization'
    
    # 列出可用视频
    if args.list or not args.video:
        print("\n📂 可用视频:")
        videos = list(videos_dir.glob('*.mp4'))
        if videos:
            for i, v in enumerate(videos, 1):
                size_mb = v.stat().st_size / 1024 / 1024
                print(f"   {i}. {v.name} ({size_mb:.1f} MB)")
            
            if not args.video:
                print(f"\n使用方法: python {Path(__file__).name} <视频文件名或编号>")
                print(f"示例: python {Path(__file__).name} 1")
                print(f"      python {Path(__file__).name} {videos[0].name}")
                
                # 交互式选择
                try:
                    choice = input("\n请选择视频编号 (直接回车使用第一个): ").strip()
                    if choice == '':
                        choice = '1'
                    idx = int(choice) - 1
                    if 0 <= idx < len(videos):
                        args.video = str(videos[idx])
                    else:
                        print("无效的选择")
                        return
                except (ValueError, KeyboardInterrupt):
                    return
        else:
            print("   暂无视频文件")
            return
    
    # 处理视频路径
    video_path = Path(args.video)
    if not video_path.exists():
        # 尝试在 videos_dir 中查找
        video_path = videos_dir / args.video
        if not video_path.exists():
            # 尝试作为编号
            try:
                idx = int(args.video) - 1
                videos = list(videos_dir.glob('*.mp4'))
                if 0 <= idx < len(videos):
                    video_path = videos[idx]
                else:
                    print(f"❌ 视频不存在: {args.video}")
                    return
            except ValueError:
                print(f"❌ 视频不存在: {args.video}")
                return
    
    # 输出路径
    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = output_dir / f"detection_{video_path.stem}_{timestamp}.mp4"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"\n🎯 ClassInsight AI - 检测可视化")
    print(f"=" * 50)
    print(f"输入视频: {video_path}")
    print(f"输出路径: {output_path}")
    print(f"置信度阈值: {args.confidence}")
    
    # 创建可视化器
    visualizer = DetectionVisualizer(str(weights_dir), confidence=args.confidence)
    
    # 处理视频
    visualizer.process_video(
        str(video_path),
        str(output_path),
        skip_frames=args.skip,
        max_frames=args.max_frames,
        show_preview=args.preview
    )
    
    print(f"\n📁 输出文件位置:")
    print(f"   {output_path}")


if __name__ == '__main__':
    main()


















