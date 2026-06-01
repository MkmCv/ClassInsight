# 课堂行为「时间聚合」说明（答辩/维护）

## 1. 概念

**时间聚合**：将视频抽帧得到的逐帧检测结果，按固定长度的**非重叠时间窗**合并为「每个时间段上的行为计数」，用于时间线图表、汇总统计与相关性分析，避免逐帧数据过密、噪声过大。

## 2. 流程概览

```
视频抽帧 → 每帧得到时间戳 timestamp（秒）→ 映射到窗口键 window_key
→ 在 window_data[window_key] 内累加 behavior_counts / 师生分类计数
→ 写入表 analysis_timeline（每窗一行）→ API 按 video_id 拉取时间线
→ 前端与 behavior_analyzer 将「每一行」视为时间序列上的一个点
```

## 3. 窗口如何对齐

- **窗长**：当前固定 `window_size = 10`（秒）。
- **对齐公式**：`window_key = (timestamp // window_size) * window_size`  
  例如：`timestamp=23` → `window_key=20`（20–29 秒同属一桶）。

实现位置：`backend/app/services/video_processor.py`（抽帧循环内）。

## 4. 窗内聚什么

| 字段 | 含义 |
|------|------|
| `behavior_counts`（窗内） | 该窗内每次检测到的 **YOLO 原始类别**，每出现一次 +1 |
| `student_behaviors` / `teacher_behaviors` | 经 **BehaviorClassifier** 后的业务标签，在窗内累加；**举手**有额外规则（人数阈值、时间/窗口去重） |
| `detections` | 可选保留部分检测框，入库时截断以控制体积 |

持久化：`AnalysisTimeline` 一行对应 `(video_id, timestamp=window_key, window_size)`，`behavior_counts` 为 JSON（可含 `_raw`、`_classified` 等扩展）。

## 5. 数据表与 API

- **模型**：`backend/app/models/analysis.py` → `AnalysisTimeline`
- **写入**：仅 `video_processor.process_video_task` 创建时间线行，且当前 **`window_size` 恒为 10**。
- **读取**：`GET /api/v1/analysis/{video_id}/timeline?window=10|60`（`backend/app/api/v1/endpoints/analysis.py`）按 `window_size` 过滤。  
  **注意**：若库中只有 `window_size=10` 的记录，则 `window=60` 可能无数据；需 60 秒粒度时应对 10 秒行做二次合并或扩展写入逻辑。

## 6. 下游：相关性分析

`backend/app/services/behavior_analyzer.py` 中 `analyze_behavior_correlations` 按时间顺序取出各窗的 `behavior_counts`，构造教师/学生行为序列；`calculate_correlation` 里 **`best_lag * 10` 表示秒**，隐含「每个时间步 = 10 秒窗」。

## 7. 代码索引（已加注释处）

| 文件 | 说明 |
|------|------|
| `backend/app/services/video_processor.py` | 时间窗键、窗内累加、写入 `AnalysisTimeline` |
| `backend/app/models/analysis.py` | `timestamp` 为窗口起点（秒）、`window_size` |
| `backend/app/api/v1/endpoints/analysis.py` | 时间线查询与 `window` 参数 |
| `backend/app/services/behavior_analyzer.py` | 滞后换算为秒（×10） |

## 8. 答辩口述要点（精简）

采用 **10 秒固定、非重叠分桶**；用整数除法对齐边界；桶内对检测类别与分类后行为做计数（举手有业务规则）；每桶一行入库；图表与相关性以桶为时间步，降低噪声并保留课堂节奏。
