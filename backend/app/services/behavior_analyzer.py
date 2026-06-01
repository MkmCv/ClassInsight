"""
行为分析服务 - 真实相关性分析和模式识别
"""
import numpy as np
from scipy.stats import pearsonr
from typing import Dict, List, Tuple, Optional
from collections import Counter

from ..core.config import STUDENT_BEHAVIORS, TEACHER_BEHAVIORS


def calculate_correlation(
    series1: List[float],
    series2: List[float],
    max_lag: int = 10
) -> Tuple[float, int, float]:
    """
    计算两个时间序列的皮尔逊相关系数，考虑滞后时间
    
    Args:
        series1: 第一个时间序列（教师行为）
        series2: 第二个时间序列（学生行为）
        max_lag: 最大滞后「步数」；每步对应时间线一行，当前与 10s 时间窗一致时即最多滞后约 max_lag*10 秒
    
    Returns:
        (correlation_coefficient, lag_time, p_value)
        - correlation_coefficient: 相关系数（-1到1）
        - lag_time: 最佳滞后时间（秒）
        - p_value: 显著性检验p值
    """
    if len(series1) != len(series2) or len(series1) < 3:
        return 0.0, 0, 1.0
    
    best_corr = 0.0
    best_lag = 0
    best_p = 1.0
    
    # 尝试不同的滞后时间
    for lag in range(max_lag + 1):
        if lag == 0:
            # 无滞后
            x = np.array(series1)
            y = np.array(series2)
        else:
            # 滞后lag个窗口
            x = np.array(series1[:-lag] if lag > 0 else series1)
            y = np.array(series2[lag:] if lag > 0 else series2)
        
        if len(x) < 3 or len(y) < 3 or len(x) != len(y):
            continue
        
        # 计算皮尔逊相关系数
        try:
            corr, p_value = pearsonr(x, y)
            
            # 取绝对值最大的相关性
            if abs(corr) > abs(best_corr):
                best_corr = corr
                best_lag = lag * 10  # 与 video_processor 默认 window_size=10 对齐：lag 步 → 秒
                best_p = p_value
        except:
            continue
    
    return best_corr, best_lag, best_p


def analyze_behavior_correlations(
    timeline_data: List[Dict],
    window_size: int = 10
) -> List[Dict]:
    """
    分析教师行为与学生行为的相关性
    
    Args:
        timeline_data: 时间线数据列表，每个元素包含 timestamp 和 behavior_counts
        window_size: 时间窗口大小（秒）
    
    Returns:
        相关性分析结果列表
    """
    if not timeline_data or len(timeline_data) < 3:
        return []
    
    # 提取所有行为类别
    all_behaviors = set()
    for item in timeline_data:
        all_behaviors.update(item.get('behavior_counts', {}).keys())
    
    # 分离教师行为和学生行为
    teacher_behaviors = [b for b in all_behaviors if b in TEACHER_BEHAVIORS]
    student_behaviors = [b for b in all_behaviors if b in STUDENT_BEHAVIORS]
    
    correlations = []
    
    # 对每对教师-学生行为计算相关性
    for teacher_behavior in teacher_behaviors:
        for student_behavior in student_behaviors:
            # 提取时间序列
            teacher_series = [
                item.get('behavior_counts', {}).get(teacher_behavior, 0)
                for item in timeline_data
            ]
            student_series = [
                item.get('behavior_counts', {}).get(student_behavior, 0)
                for item in timeline_data
            ]
            
            # 计算相关性
            corr, lag_time, p_value = calculate_correlation(
                teacher_series,
                student_series,
                max_lag=10
            )
            
            # 只保留显著相关的结果（p < 0.05 且 |corr| > 0.3）
            if p_value < 0.05 and abs(corr) > 0.3:
                # 生成解释文本
                if corr > 0:
                    direction = "正相关"
                    interpretation = f"教师的「{teacher_behavior}」行为与学生「{student_behavior}」行为呈{direction}"
                else:
                    direction = "负相关"
                    interpretation = f"教师的「{teacher_behavior}」行为与学生「{student_behavior}」行为呈{direction}"
                
                if lag_time > 0:
                    interpretation += f"，学生行为滞后{lag_time}秒"
                
                interpretation += f"（相关系数: {corr:.2f}, p={p_value:.3f}）"
                
                correlations.append({
                    "teacher_behavior": teacher_behavior,
                    "student_behavior": student_behavior,
                    "correlation_coefficient": round(corr, 3),
                    "lag_time": lag_time,
                    "p_value": round(p_value, 3),
                    "interpretation": interpretation
                })
    
    # 按相关系数绝对值排序
    correlations.sort(key=lambda x: abs(x["correlation_coefficient"]), reverse=True)
    
    return correlations[:10]  # 返回前10个最强的相关性


def analyze_behavior_overlap(
    timeline_data: List[Dict]
) -> List[Dict]:
    """
    分析行为重叠（学生行为在特定场景下的发生频率）
    
    Args:
        timeline_data: 时间线数据列表
    
    Returns:
        重叠分析结果列表
    """
    if not timeline_data:
        return []
    
    overlap_results = []
    
    # 定义场景-行为映射
    context_behaviors = {
        "screen": ["read", "write"],
        "blackboard-writing": ["write", "read"],
        "guide": ["discuss", "hand-raising"],
        "teacher": ["read", "write"]
    }
    
    for context, related_behaviors in context_behaviors.items():
        for student_behavior in related_behaviors:
            # 统计该行为在场景下的发生次数
            total_behavior_count = 0
            context_behavior_count = 0
            
            for item in timeline_data:
                behavior_counts = item.get('behavior_counts', {})
                student_count = behavior_counts.get(student_behavior, 0)
                context_count = behavior_counts.get(context, 0)
                
                total_behavior_count += student_count
                if context_count > 0:
                    context_behavior_count += student_count
            
            if total_behavior_count > 0:
                overlap_rate = context_behavior_count / total_behavior_count
                
                if overlap_rate > 0.3:  # 只保留重叠率>30%的结果
                    overlap_results.append({
                        "student_behavior": student_behavior,
                        "context": context,
                        "overlap_rate": round(overlap_rate, 2),
                        "description": f"{overlap_rate*100:.0f}%的{student_behavior}行为发生在{context}场景期间"
                    })
    
    return overlap_results


def identify_teaching_mode(
    behavior_counts: Dict[str, int]
) -> str:
    """
    识别单个时间窗口的教学模式
    
    Args:
        behavior_counts: 该窗口的行为计数
    
    Returns:
        教学模式标签
    """
    # 计算各类行为的强度
    interaction = (
        behavior_counts.get('guide', 0) +
        behavior_counts.get('answer', 0) +
        behavior_counts.get('On-stage interaction', 0)
    )
    blackboard = behavior_counts.get('blackboard-writing', 0)
    multimedia = behavior_counts.get('screen', 0)
    lecture = (
        behavior_counts.get('teacher', 0) +
        behavior_counts.get('stand', 0)
    )
    practice = (
        behavior_counts.get('write', 0) +
        behavior_counts.get('read', 0)
    )
    discussion = behavior_counts.get('discuss', 0)
    
    # 根据行为强度判断模式
    if interaction > 0 and (interaction >= lecture or discussion > 0):
        return "互动教学"
    elif blackboard > 0:
        return "板书讲解"
    elif multimedia > 0:
        return "多媒体演示"
    elif practice > lecture and practice > 0:
        return "练习模式"
    elif lecture > 0:
        return "讲授模式"
    else:
        return "其他"


def analyze_teaching_modes(
    timeline_data: List[Dict]
) -> Dict:
    """
    分析教学模式分布和转换
    
    Args:
        timeline_data: 时间线数据列表
    
    Returns:
        教学模式分析结果
    """
    if not timeline_data:
        return {
            "modes": [],
            "mode_distribution": {},
            "transitions": [],
            "mode_timeline": []
        }
    
    # 识别每个窗口的教学模式
    mode_timeline = []
    for item in timeline_data:
        behavior_counts = item.get('behavior_counts', {})
        mode = identify_teaching_mode(behavior_counts)
        mode_timeline.append({
            "timestamp": item.get('timestamp', 0),
            "mode": mode,
            "behavior_counts": behavior_counts
        })
    
    # 统计模式分布
    modes = [item["mode"] for item in mode_timeline]
    mode_distribution = dict(Counter(modes))
    total_windows = len(modes)
    
    # 计算占比
    mode_percentages = {
        mode: round(count / total_windows * 100, 1)
        for mode, count in mode_distribution.items()
    }
    
    # 分析模式转换
    transitions = []
    for i in range(len(modes) - 1):
        from_mode = modes[i]
        to_mode = modes[i + 1]
        if from_mode != to_mode:
            transitions.append({
                "from": from_mode,
                "to": to_mode,
                "timestamp": mode_timeline[i]["timestamp"]
            })
    
    # 统计转换频率
    transition_counts = Counter([
        (t["from"], t["to"]) for t in transitions
    ])
    
    return {
        "modes": list(set(modes)),
        "mode_distribution": mode_distribution,
        "mode_percentages": mode_percentages,
        "transitions": transitions,
        "transition_counts": dict(transition_counts),
        "mode_timeline": mode_timeline,
        "total_windows": total_windows
    }








