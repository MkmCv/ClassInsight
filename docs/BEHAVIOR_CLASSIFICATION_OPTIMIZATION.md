# 行为分类优化文档

## 概述

本文档描述了行为分析模块的优化方案，将检测器的原始输出映射到标准化的学生行为和教师行为类别，提高识别精度和可解释性。

## 行为分类体系

### 学生行为类别（9类）

1. **读写** - 学生在读书或者写字
2. **台上展示** - 学生在台上展示（无教师参与）
3. **学生板书** - 学生在黑板上板书
4. **回答问题** - 学生站立起来回答问题（画面中只有学生，没有教师）
5. **朗读** - 学生齐声朗读（在读写的基础上有张开嘴或张开的趋势）
6. **讨论** - 学生在课堂中进行讨论（同桌或前后排）
7. **听讲** - 学生抬头听教师讲课
8. **学生举手** - 学生举手（一般举手的学生超过3个才算举手）
9. **其它** - 不属于上述任何一种行为

### 教师行为类别（7类）

1. **讲授** - 教师通常站在讲台上，讲解课堂上的知识点（只有教师一人站立）
2. **指导** - 教师走下讲台，针对某位学生进行个别指导（通常伴随弯腰、驻足等动作）
3. **应答** - 学生回答教师的问题（通常教师与学生都站立，教师提问，学生回答）
4. **台上互动** - 教师邀请学生上台进行活动（包括做游戏、完成任务或学生上台板书）
5. **教师板书** - 教师在黑板上进行书写
6. **巡视** - 教师不在讲台上，而是在教室内走动，观察学生或巡视教室
7. **其它** - 不属于上述任何一种行为

## 识别规则

### 核心原则

1. **单一行为优先**：每张图片只识别一个主导行为，如果存在复合动作，按主导行为进行分类
2. **唯一输出**：每次识别只输出一种行为类别（学生行为和教师行为分别输出）

### 分类逻辑

#### 学生行为分类流程

1. 检查必需类别是否存在
2. 排除冲突类别
3. 验证上下文要求（如"听讲"需要教师在场）
4. 检查数量要求（如"学生举手"需要至少3个）
5. 计算匹配分数（基于优先级和检测数量）
6. 选择最高分的行为类别

#### 教师行为分类流程

1. 首先检查是否有教师在场
2. 检查必需类别是否存在
3. 排除冲突类别
4. 验证上下文要求（如"应答"需要学生站立）
5. 计算匹配分数
6. 选择最高分的行为类别

## 实现细节

### 文件结构

```
backend/app/ml/
├── detector.py              # 原始检测器（YOLO-vHeat）
└── behavior_classifier.py   # 行为分类器（新增）
```

### 核心类：BehaviorClassifier

```python
class BehaviorClassifier:
    def classify_frame(detections) -> (student_behavior, teacher_behavior)
    def classify_batch(frames_detections) -> List[(student_behavior, teacher_behavior)]
    def get_behavior_statistics(classification_results) -> Dict
```

### 映射规则示例

#### 学生行为映射

```python
"读写": {
    "required": ["read", "write"],
    "exclude": ["discuss", "hand-raising"],
    "priority": 1
}

"学生举手": {
    "required": ["hand-raising"],
    "min_count": 3,  # 至少3个学生举手
    "exclude": ["teacher"],
    "priority": 4
}
```

#### 教师行为映射

```python
"讲授": {
    "required": ["teacher", "stand"],
    "exclude": ["answer", "guide", "On-stage interaction"],
    "context_exclude": ["stand"],  # 排除学生站立
    "priority": 1
}

"应答": {
    "required": ["answer", "teacher"],
    "context_required": ["stand"],  # 需要学生站立
    "exclude": ["guide", "On-stage interaction"],
    "priority": 3
}
```

## 集成到视频处理流程

### 修改点

1. **video_processor.py**
   - 在检测后立即进行分类
   - 同时保存原始检测结果和分类结果
   - 更新统计逻辑以包含分类后的行为

2. **数据存储**
   - `behavior_counts`: 包含原始类别和分类后的行为
   - `student_behaviors`: 分类后的学生行为统计
   - `teacher_behaviors`: 分类后的教师行为统计

### 数据格式

#### 时间线数据

```json
{
    "timestamp": 10,
    "window_size": 10,
    "behavior_counts": {
        "raw_behavior_counts": {
            "read": 5,
            "write": 3,
            "teacher": 1
        },
        "student_behaviors": {
            "读写": 8
        },
        "teacher_behaviors": {
            "讲授": 1
        }
    }
}
```

#### 汇总数据

```json
{
    "read": {
        "count": 100,
        "total_duration": 50,
        "percentage": 20.5,
        "type": "raw"
    },
    "_classified": {
        "student_behaviors": {
            "读写": {
                "count": 150,
                "total_duration": 80,
                "percentage": 32.8
            }
        },
        "teacher_behaviors": {
            "讲授": {
                "count": 200,
                "total_duration": 120,
                "percentage": 49.2
            }
        }
    }
}
```

## 优化建议

### 当前实现

- ✅ 单一行为优先原则
- ✅ 基于规则的分类逻辑
- ✅ 优先级和分数机制
- ✅ 上下文验证

### 未来改进方向

1. **机器学习增强**
   - 使用历史数据训练分类模型
   - 结合时序信息（前后帧）进行判断
   - 使用注意力机制识别关键特征

2. **规则细化**
   - 添加更多上下文规则（如位置信息）
   - 优化优先级设置
   - 处理边界情况

3. **多模态融合**
   - 结合音频信息（如朗读检测）
   - 使用姿态估计（如弯腰、驻足检测）
   - 融合场景理解（如讲台位置）

4. **实时优化**
   - 缓存分类结果
   - 批量处理优化
   - 并行分类

## 使用示例

### 基本使用

```python
from app.ml.behavior_classifier import get_classifier

classifier = get_classifier()

# 单帧分类
detections = [
    {"category": "read", "score": 0.9, "bbox": [...]},
    {"category": "write", "score": 0.8, "bbox": [...]}
]

student_behavior, teacher_behavior = classifier.classify_frame(detections)
# 返回: ("读写", None)
```

### 批量分类

```python
# 批量处理多帧
frames_detections = [
    [{"category": "read", ...}, {"category": "write", ...}],
    [{"category": "teacher", ...}, {"category": "stand", ...}],
    ...
]

results = classifier.classify_batch(frames_detections)
# 返回: [("读写", None), (None, "讲授"), ...]

# 统计
stats = classifier.get_behavior_statistics(results)
```

## 测试与验证

### 测试用例

1. **单一行为测试**
   - 只有read -> 应该分类为"读写"
   - 只有teacher + stand -> 应该分类为"讲授"

2. **复合行为测试**
   - read + write -> 应该分类为"读写"（优先级1）
   - teacher + answer + stand -> 应该分类为"应答"（优先级3）

3. **上下文测试**
   - hand-raising < 3 -> 不应该分类为"学生举手"
   - teacher + stand + 学生stand -> 应该分类为"应答"而不是"讲授"

4. **边界情况**
   - 无检测结果 -> 返回 (None, None)
   - 无法匹配任何规则 -> 返回"其它"

## 注意事项

1. **模型精度限制**
   - 当前分类基于检测器的输出，检测精度直接影响分类精度
   - 建议持续优化检测模型

2. **规则维护**
   - 随着使用经验积累，需要不断调整规则
   - 建议建立规则版本管理机制

3. **性能考虑**
   - 分类器本身计算开销很小
   - 主要瓶颈在检测器推理

4. **数据兼容性**
   - 保留原始检测数据以确保向后兼容
   - 新功能使用分类后的数据

## 更新日志

- **2025-01-XX**: 初始实现
  - 创建 BehaviorClassifier 类
  - 集成到视频处理流程
  - 添加学生和教师行为映射规则



