# 行为分类器实现说明

## 我实现了什么

### 1. **行为分类器模块** (`backend/app/ml/behavior_classifier.py`)

将检测器的原始输出（如 `read`, `write`, `teacher`, `guide` 等）映射到高级行为类别：

- **学生行为**：读写、台上展示、学生板书、回答问题、朗读、讨论、听讲、学生举手、其它
- **教师行为**：讲授、指导、应答、台上互动、教师板书、巡视、其它

### 2. **集成到视频处理流程** (`backend/app/services/video_processor.py`)

- 在每帧检测后立即进行分类
- 同时保存原始检测结果和分类后的行为
- 统计分类后的行为数据

### 3. **API 数据返回** (`backend/app/api/v1/endpoints/analysis.py`)

- 优先返回分类后的行为数据
- 同时保留原始数据用于兼容性

### 4. **前端页面更新** (`System/frontend/pages/3_📈_行为分析.py`)

- 兼容显示分类后的行为（中文类别名）
- 向后兼容原始数据

## 可能导致数据不正常的原因

### 问题1：数据格式变更

**原因**：我修改了 `behavior_counts` 的存储格式，从简单的字典变成了嵌套字典：

```python
# 旧格式（前端期望的）
behavior_counts = {"discuss": 3, "read": 5, "teacher": 1}

# 新格式（我实现的）
behavior_counts = {
    "raw_behavior_counts": {"discuss": 3, "read": 5},
    "student_behaviors": {"讨论": 3, "读写": 5},
    "teacher_behaviors": {"讲授": 1}
}
```

**影响**：前端代码期望简单的字典格式，但收到了嵌套字典，导致无法正确解析。

### 问题2：关键指标计算错误

**原因**：关键指标（互动率、专注度等）的计算仍然使用原始类别名（`discuss`, `BowHead`），但如果只有分类后的数据，这些字段不存在。

### 问题3：时间线数据格式不一致

**原因**：时间线数据的 `behavior_counts` 格式变化，前端无法正确解析。

## 修复方案

我已经修复了以下问题：

1. ✅ **时间线数据格式**：同时保存原始和分类后的数据，API 会合并返回
2. ✅ **关键指标计算**：兼容原始和分类后的数据
3. ✅ **API 响应格式**：同时返回原始和分类后的数据，确保兼容性

## 当前数据格式

### 时间线数据 (`behavior_counts`)

```json
{
    "raw_behavior_counts": {"discuss": 3, "read": 5, "teacher": 1},
    "student_behaviors": {"讨论": 3, "读写": 5},
    "teacher_behaviors": {"讲授": 1},
    // 同时展开合并后的数据用于兼容性
    "discuss": 3,
    "read": 5,
    "teacher": 1,
    "讨论": 3,
    "读写": 5,
    "讲授": 1
}
```

### 汇总数据 (`behavior_summary`)

```json
{
    "discuss": {"count": 45, "total_duration": 1200, "percentage": 33.3},
    "read": {...},
    "_classified": {
        "student_behaviors": {
            "讨论": {"count": 45, "total_duration": 1200, "percentage": 33.3},
            "读写": {...}
        },
        "teacher_behaviors": {
            "讲授": {...}
        }
    }
}
```

## 如果数据仍然不正常

### 检查点1：确认是新视频还是旧视频

- **新视频**：应该同时有原始和分类后的数据
- **旧视频**：只有原始数据，应该正常显示

### 检查点2：查看数据库中的实际数据

检查 `analysis_timeline` 和 `analysis_summary` 表中的数据格式。

### 检查点3：临时禁用分类器

如果需要快速恢复，可以临时注释掉分类器的调用：

```python
# 在 video_processor.py 中
# student_behavior, teacher_behavior = behavior_classifier.classify_frame(detections)
student_behavior, teacher_behavior = None, None  # 临时禁用
```

## 建议

1. **先测试新上传的视频**：确认分类功能是否正常工作
2. **检查旧视频**：确认向后兼容是否正常
3. **如果仍有问题**：提供具体的错误信息或数据示例，我可以进一步修复



