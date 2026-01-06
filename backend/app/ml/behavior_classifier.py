"""
行为分类器 - 将检测器的原始输出映射到高级行为类别

根据用户定义的行为分类规则，将检测到的原始类别（如 'read', 'write', 'teacher' 等）
映射到标准化的学生行为和教师行为类别。
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter

logger = logging.getLogger(__name__)

# 学生行为类别
STUDENT_BEHAVIOR_CATEGORIES = [
    "读写",
    "台上展示",
    "学生板书",
    "回答问题",
    "朗读",
    "讨论",
    "听讲",
    "学生举手",
    "其它"
]

# 教师行为类别
TEACHER_BEHAVIOR_CATEGORIES = [
    "讲授",
    "指导",
    "应答",
    "台上互动",
    "教师板书",
    "巡视",
    "其它"
]

# 原始检测类别到学生行为的映射规则
STUDENT_BEHAVIOR_MAPPING = {
    # 读写：学生在读书或者写字
    "读写": {
        "required": ["read", "write"],
        "exclude": ["discuss", "hand-raising"],  # 排除讨论和举手
        "priority": 1
    },
    
    # 朗读：学生齐声朗读，在读写的基础上有张开嘴或张开的趋势
    "朗读": {
        "required": ["read"],  # 需要read，但可能需要额外的嘴部检测
        "exclude": ["write", "discuss"],
        "priority": 2,  # 优先级高于读写
        "note": "需要检测嘴部动作，当前基于read推断"
    },
    
    # 讨论：学生在课堂中进行讨论
    "讨论": {
        "required": ["discuss"],
        "exclude": ["teacher", "stand"],  # 排除教师和站立（可能是回答问题）
        "priority": 3
    },
    
    # 学生举手：学生举手，一般举手的学生超过3个才算举手
    "学生举手": {
        "required": ["hand-raising"],
        "min_count": 3,  # 至少3个学生举手
        "exclude": ["teacher"],
        "priority": 4
    },
    
    # 听讲：学生抬头听教师讲课
    "听讲": {
        "required": ["TurnHead"],  # 抬头
        "exclude": ["BowHead", "read", "write", "discuss"],  # 排除低头和读写讨论
        "context_required": ["teacher"],  # 需要教师在场
        "priority": 5
    },
    
    # 回答问题：学生站立起来，回答问题，画面中只有学生，没有教师
    # 注意：与"应答"的区别是，回答问题是画面中只有学生，没有教师
    "回答问题": {
        "required": ["stand"],
        "exclude": ["teacher", "guide", "answer"],  # 排除教师、指导、应答（这些是教师行为）
        "context_exclude": ["teacher"],  # 明确排除教师在场
        "priority": 6
    },
    
    # 学生板书：学生在黑板上板书
    # 注意：区分学生板书与教师板书，学生板书需要学生站立且没有教师
    "学生板书": {
        "required": ["blackboard-writing"],
        "exclude": ["teacher"],  # 排除教师板书
        "context_required": ["stand"],  # 需要学生站立
        "context_exclude": ["teacher"],  # 明确排除教师在场
        "priority": 7
    },
    
    # 台上展示：学生在台上展示，没有教师
    "台上展示": {
        "required": ["On-stage interaction"],
        "exclude": ["teacher"],  # 排除教师（如果有教师则是"台上互动"）
        "priority": 8
    },
}

# 原始检测类别到教师行为的映射规则
TEACHER_BEHAVIOR_MAPPING = {
    # 讲授：教师通常站在讲台上，讲解课堂上的知识点，只有教师一人站立
    # 注意：区分教师讲授与师生互动，教师讲授没有学生站立回答问题
    "讲授": {
        "required": ["teacher", "stand"],
        "exclude": ["answer", "guide", "On-stage interaction", "blackboard-writing"],  # 排除其他教师行为
        "context_exclude": ["answer"],  # 排除应答行为（如果有answer可能是应答）
        "note": "需要进一步判断是否有学生站立，如果有学生站立且没有answer，可能是应答",
        "priority": 1
    },
    
    # 指导：教师走下讲台，针对某位学生进行个别指导
    "指导": {
        "required": ["guide"],
        "exclude": ["stand", "answer"],  # 排除站立和应答
        "priority": 2
    },
    
    # 应答：学生回答教师的问题，通常教师与学生都站立
    "应答": {
        "required": ["answer", "teacher"],
        "context_required": ["stand"],  # 需要学生站立
        "exclude": ["guide", "On-stage interaction"],
        "priority": 3
    },
    
    # 台上互动：教师邀请学生上台进行活动
    "台上互动": {
        "required": ["On-stage interaction", "teacher"],
        "exclude": ["guide", "answer"],
        "priority": 4
    },
    
    # 教师板书：教师在黑板上进行书写
    "教师板书": {
        "required": ["blackboard-writing", "teacher"],
        "exclude": ["guide", "answer", "On-stage interaction"],
        "priority": 5
    },
    
    # 巡视：教师不在讲台上，而是在教室内走动
    "巡视": {
        "required": ["teacher"],
        "exclude": ["stand", "blackboard-writing", "guide", "answer", "On-stage interaction"],
        "priority": 6
    },
}


class BehaviorClassifier:
    """
    行为分类器
    
    将检测器的原始输出映射到标准化的学生行为和教师行为类别。
    遵循单一行为优先原则：每帧只输出一个主导行为。
    """
    
    def __init__(self):
        """初始化分类器"""
        self.student_mapping = STUDENT_BEHAVIOR_MAPPING
        self.teacher_mapping = TEACHER_BEHAVIOR_MAPPING
    
    def classify_frame(
        self, 
        detections: List[Dict[str, Any]]
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        对单帧检测结果进行分类
        
        Args:
            detections: 检测结果列表，每个元素包含 category, score, bbox 等
            
        Returns:
            (student_behavior, teacher_behavior): 
            - student_behavior: 学生行为类别（如果存在）
            - teacher_behavior: 教师行为类别（如果存在）
            每个值可能为 None（表示该帧没有对应的行为）
        """
        if not detections:
            return None, None
        
        # 统计检测到的类别及其数量（统一转换为小写）
        category_counts = Counter()
        categories_present = set()
        
        # 类别名称映射（处理可能的变体）
        category_mapping = {
            "on-stage interaction": "on-stage interaction",
            "blackboard-writing": "blackboard-writing",
            "hand-raising": "hand-raising",
            "bowhead": "bowhead",
            "turnhead": "turnhead"
        }
        
        for det in detections:
            category = det.get("category", "").strip()
            if not category:
                continue
            
            # 统一转换为小写并处理映射
            category_lower = category.lower()
            category_normalized = category_mapping.get(category_lower, category_lower)
            
            category_counts[category_normalized] += 1
            categories_present.add(category_normalized)
        
        # 分类学生行为和教师行为
        student_behavior = self._classify_student_behavior(categories_present, category_counts, detections)
        teacher_behavior = self._classify_teacher_behavior(categories_present, category_counts, detections)
        
        return student_behavior, teacher_behavior
    
    def _classify_student_behavior(
        self,
        categories_present: set,
        category_counts: Counter,
        detections: List[Dict]
    ) -> Optional[str]:
        """分类学生行为"""
        candidates = []
        
        for behavior_name, rules in self.student_mapping.items():
            score = 0
            matched = True
            
            # 检查必需类别
            required = rules.get("required", [])
            if not all(cat.lower() in categories_present for cat in required):
                continue
            
            # 检查排除类别
            exclude = rules.get("exclude", [])
            if any(cat.lower() in categories_present for cat in exclude):
                continue
            
            # 检查上下文要求（可选）
            context_required = [cat.lower() for cat in rules.get("context_required", [])]
            if context_required:
                if not any(cat in categories_present for cat in context_required):
                    continue
            
            # 检查最小数量要求
            min_count = rules.get("min_count", 0)
            if min_count > 0:
                # 对于学生举手，需要至少3个
                if behavior_name == "学生举手":
                    hand_raising_count = category_counts.get("hand-raising", 0)
                    if hand_raising_count < min_count:
                        continue
            
            # 计算匹配分数（基于优先级和检测数量）
            priority = rules.get("priority", 999)
            score = 1000 - priority  # 优先级越高，分数越高
            
            # 根据检测数量调整分数
            for req_cat in required:
                count = category_counts.get(req_cat.lower(), 0)
                score += count * 10
            
            candidates.append((behavior_name, score, priority))
        
        # 按分数排序，选择最高分的（单一行为优先）
        if candidates:
            candidates.sort(key=lambda x: (x[1], -x[2]), reverse=True)
            return candidates[0][0]
        
        # 如果没有匹配，检查是否有学生相关的基础行为
        student_base_categories = ["read", "write", "discuss", "hand-raising", "TurnHead", "BowHead", "stand"]
        if any(cat.lower() in categories_present for cat in student_base_categories):
            # 如果有学生行为但无法精确分类，返回"其它"
            return "其它"
        
        return None
    
    def _classify_teacher_behavior(
        self,
        categories_present: set,
        category_counts: Counter,
        detections: List[Dict]
    ) -> Optional[str]:
        """分类教师行为"""
        candidates = []
        
        # 首先检查是否有教师
        if "teacher" not in categories_present:
            return None
        
        for behavior_name, rules in self.teacher_mapping.items():
            score = 0
            matched = True
            
            # 检查必需类别（统一转换为小写比较）
            required = [cat.lower() for cat in rules.get("required", [])]
            if not all(cat in categories_present for cat in required):
                continue
            
            # 检查排除类别
            exclude = [cat.lower() for cat in rules.get("exclude", [])]
            if any(cat in categories_present for cat in exclude):
                continue
            
            # 检查上下文排除（明确排除某些类别）
            context_exclude = [cat.lower() for cat in rules.get("context_exclude", [])]
            if context_exclude:
                if any(cat in categories_present for cat in context_exclude):
                    continue
            
            # 检查上下文要求
            context_required = [cat.lower() for cat in rules.get("context_required", [])]
            if context_required:
                if not any(cat in categories_present for cat in context_required):
                    continue
            
            # 特殊处理：讲授 vs 应答的区别
            # 讲授：只有教师一人站立，没有学生站立回答问题
            # 应答：教师和学生都站立，且有answer行为
            if behavior_name == "讲授":
                # 如果有stand（可能是学生站立）且有answer，应该是应答而不是讲授
                if "stand" in categories_present and "answer" in categories_present:
                    continue
                # 如果有answer，应该是应答而不是讲授
                if "answer" in categories_present:
                    continue
            
            # 特殊处理：应答需要确保有学生站立
            if behavior_name == "应答":
                # 应答需要：teacher + answer + 学生stand
                # 如果只有teacher和answer，但没有stand，可能不是应答
                if "stand" not in categories_present:
                    continue
            
            # 计算匹配分数
            priority = rules.get("priority", 999)
            score = 1000 - priority
            
            # 根据检测数量调整分数
            for req_cat in required:
                count = category_counts.get(req_cat.lower(), 0)
                score += count * 10
            
            candidates.append((behavior_name, score, priority))
        
        # 按分数排序，选择最高分的
        if candidates:
            candidates.sort(key=lambda x: (x[1], -x[2]), reverse=True)
            return candidates[0][0]
        
        # 如果有教师但无法精确分类，返回"其它"
        return "其它"
    
    def classify_batch(
        self,
        frames_detections: List[List[Dict[str, Any]]]
    ) -> List[Tuple[Optional[str], Optional[str]]]:
        """
        批量分类多帧检测结果
        
        Args:
            frames_detections: 每帧的检测结果列表
            
        Returns:
            每帧的分类结果列表
        """
        return [self.classify_frame(detections) for detections in frames_detections]
    
    def get_behavior_statistics(
        self,
        classification_results: List[Tuple[Optional[str], Optional[str]]]
    ) -> Dict[str, Any]:
        """
        统计行为分类结果
        
        Args:
            classification_results: 分类结果列表
            
        Returns:
            统计信息字典
        """
        student_behaviors = Counter()
        teacher_behaviors = Counter()
        
        for student_behavior, teacher_behavior in classification_results:
            if student_behavior:
                student_behaviors[student_behavior] += 1
            if teacher_behavior:
                teacher_behaviors[teacher_behavior] += 1
        
        return {
            "student_behaviors": dict(student_behaviors),
            "teacher_behaviors": dict(teacher_behaviors),
            "total_frames": len(classification_results),
            "frames_with_student_behavior": sum(1 for s, _ in classification_results if s),
            "frames_with_teacher_behavior": sum(1 for _, t in classification_results if t)
        }


# 全局分类器实例
_classifier_instance = None

def get_classifier() -> BehaviorClassifier:
    """获取全局分类器实例"""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = BehaviorClassifier()
    return _classifier_instance

