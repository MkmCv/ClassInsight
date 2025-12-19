"""
YOLO-vHeat 多模型检测器封装

这个模块封装了4个YOLO-vHeat模型的加载和推理逻辑，
提供统一的检测接口供视频处理服务调用。
"""
import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)

# 全局类别映射
GLOBAL_CATEGORY_MAPPING = {
    # posture (1-2)
    'BowHead': 1,
    'TurnHead': 2,
    
    # learning (3-5)
    'hand-raising': 3,
    'read': 4,
    'write': 5,
    
    # discussion (6)
    'discuss': 6,
    
    # comprehensive (7-14)
    'guide': 7,
    'answer': 8,
    'On-stage interaction': 9,
    'teacher': 10,
    'blackboard-writing': 11,
    'stand': 12,
    'screen': 13,
    'blackBoard': 14
}

# 模型配置
MODEL_CONFIGS = {
    'comprehensive': {
        'name': 'comprehensive_scene',
        'weight_file': 'comprehensive_scene_best.pt',
        'classes': ['guide', 'answer', 'On-stage interaction', 'blackboard-writing', 
                   'teacher', 'stand', 'screen', 'blackBoard'],
    },
    'learning': {
        'name': 'student_learning',
        'weight_file': 'student_learning_best.pt',
        'classes': ['hand-raising', 'read', 'write'],
    },
    'discussion': {
        'name': 'student_discussion',
        'weight_file': 'student_discussion_best.pt',
        'classes': ['discuss'],
    },
    'posture': {
        'name': 'student_posture',
        'weight_file': 'student_posture_best.pt',
        'classes': ['BowHead', 'TurnHead'],
    }
}


class MultiModelDetector:
    """
    多模型检测器
    
    加载4个YOLO-vHeat模型并提供统一的检测接口。
    支持并行推理和结果融合。
    """
    
    def __init__(
        self,
        weights_dir: Optional[str] = None,
        confidence_threshold: float = 0.3,
        nms_iou_threshold: float = 0.5,
        device: str = "auto"
    ):
        """
        初始化检测器
        
        Args:
            weights_dir: 模型权重目录路径
            confidence_threshold: 置信度阈值
            nms_iou_threshold: NMS IoU 阈值
            device: 运行设备 ("auto", "cuda", "cpu")
        """
        self.confidence_threshold = confidence_threshold
        self.nms_iou_threshold = nms_iou_threshold
        self.device = device
        self.models = {}
        self.is_loaded = False
        
        # 设置权重目录
        if weights_dir is None:
            weights_dir = Path(__file__).parent / "weights"
        else:
            weights_dir = Path(weights_dir)
        
        self.weights_dir = weights_dir
        
        # 尝试加载模型
        self._load_models()
    
    def _load_models(self):
        """加载所有模型"""
        try:
            # 尝试导入 ultralytics
            from ultralytics import YOLO
            
            loaded_count = 0
            
            for model_key, config in MODEL_CONFIGS.items():
                weight_path = self.weights_dir / config['weight_file']
                
                if weight_path.exists():
                    try:
                        logger.info(f"加载模型: {config['name']} from {weight_path}")
                        model = YOLO(str(weight_path))
                        
                        # 设置设备
                        if self.device != "auto":
                            model.to(self.device)
                        
                        self.models[model_key] = {
                            "model": model,
                            "classes": config['classes'],
                            "name": config['name']
                        }
                        loaded_count += 1
                        logger.info(f"模型 {config['name']} 加载成功")
                        
                    except Exception as e:
                        logger.warning(f"加载模型 {config['name']} 失败: {e}")
                else:
                    logger.warning(f"模型权重文件不存在: {weight_path}")
            
            self.is_loaded = loaded_count > 0
            logger.info(f"成功加载 {loaded_count}/{len(MODEL_CONFIGS)} 个模型")
            
        except ImportError:
            logger.error("无法导入 ultralytics 库，请确保已安装")
            self.is_loaded = False
        except Exception as e:
            logger.error(f"加载模型时发生错误: {e}")
            self.is_loaded = False
    
    async def detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        对单帧图像进行检测
        
        Args:
            frame: 输入图像 (BGR格式的numpy数组)
            
        Returns:
            检测结果列表，每个元素包含:
            - category: 类别名称
            - global_id: 全局类别ID
            - bbox: 边界框 [x1, y1, x2, y2]
            - score: 置信度
            - model: 来源模型
        """
        if not self.is_loaded:
            return []
        
        all_detections = []
        
        # 对每个模型进行推理
        for model_key, model_info in self.models.items():
            try:
                model = model_info["model"]
                classes = model_info["classes"]
                
                # 运行推理
                results = model(frame, conf=self.confidence_threshold, verbose=False)
                
                # 解析结果
                for result in results:
                    boxes = result.boxes
                    
                    if boxes is None:
                        continue
                    
                    for i in range(len(boxes)):
                        # 获取边界框
                        xyxy = boxes.xyxy[i].cpu().numpy()
                        conf = float(boxes.conf[i].cpu().numpy())
                        cls_id = int(boxes.cls[i].cpu().numpy())
                        
                        # 映射类别名称
                        if cls_id < len(classes):
                            category = classes[cls_id]
                            global_id = GLOBAL_CATEGORY_MAPPING.get(category, 0)
                            
                            all_detections.append({
                                "category": category,
                                "global_id": global_id,
                                "bbox": xyxy.tolist(),
                                "score": conf,
                                "model": model_key
                            })
                            
            except Exception as e:
                logger.warning(f"模型 {model_key} 推理失败: {e}")
                continue
        
        # 跨模型NMS去重
        if len(all_detections) > 1:
            all_detections = self._cross_model_nms(all_detections)
        
        return all_detections
    
    def _cross_model_nms(self, detections: List[Dict]) -> List[Dict]:
        """
        跨模型NMS去重
        
        当同一目标被多个模型检测到时，保留置信度最高的结果
        """
        if len(detections) <= 1:
            return detections
        
        # 按置信度排序
        detections = sorted(detections, key=lambda x: x["score"], reverse=True)
        
        keep = []
        for det in detections:
            is_duplicate = False
            bbox1 = det["bbox"]
            
            for kept in keep:
                bbox2 = kept["bbox"]
                iou = self._calculate_iou(bbox1, bbox2)
                
                if iou > self.nms_iou_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                keep.append(det)
        
        return keep
    
    @staticmethod
    def _calculate_iou(bbox1: List[float], bbox2: List[float]) -> float:
        """计算两个边界框的IoU"""
        x1 = max(bbox1[0], bbox2[0])
        y1 = max(bbox1[1], bbox2[1])
        x2 = min(bbox1[2], bbox2[2])
        y2 = min(bbox1[3], bbox2[3])
        
        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        
        area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
        area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
        
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0
    
    def batch_detect(self, frames: List[np.ndarray]) -> List[List[Dict[str, Any]]]:
        """
        批量检测
        
        Args:
            frames: 帧列表
            
        Returns:
            每帧的检测结果列表
        """
        import asyncio
        
        async def detect_all():
            return [await self.detect(frame) for frame in frames]
        
        return asyncio.run(detect_all())
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取已加载模型的信息"""
        return {
            "loaded_models": list(self.models.keys()),
            "total_models": len(MODEL_CONFIGS),
            "is_loaded": self.is_loaded,
            "confidence_threshold": self.confidence_threshold,
            "nms_iou_threshold": self.nms_iou_threshold,
            "weights_dir": str(self.weights_dir)
        }


