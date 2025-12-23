# 📦 模型权重目录

此目录用于存放训练好的 YOLO-vHeat 模型权重文件。

## 📋 所需文件

请将以下4个模型权重文件放置在此目录：

| 文件名 | 对应模型 | 检测类别 |
|--------|----------|----------|
| `comprehensive_scene_best.pt` | 综合场景模型 | guide, answer, On-stage interaction, blackboard-writing, teacher, stand, screen, blackBoard |
| `student_learning_best.pt` | 学习行为模型 | hand-raising, read, write |
| `student_discussion_best.pt` | 讨论行为模型 | discuss |
| `student_posture_best.pt` | 姿态检测模型 | BowHead, TurnHead |

## 🔧 训练模型

模型使用 `yolo-vheat` 项目进行训练。训练完成后，权重文件位于：

```
yolo-vheat/runs/train/<experiment_name>/weights/best.pt
```

将 `best.pt` 重命名并复制到此目录即可。

## ⚠️ 注意事项

1. 权重文件必须是 PyTorch 格式 (`.pt`)
2. 模型必须基于 YOLOv12-vHeat 架构训练
3. 如果某个模型文件不存在，系统会跳过该模型的加载
4. 开发阶段可以不放置模型文件，系统会使用模拟数据

## 📊 模型性能参考

| 模型 | 训练数据量 | mAP50 参考 |
|------|------------|------------|
| comprehensive_scene | 12,224 张 | ~0.75 |
| student_learning | 6,864 张 | ~0.78 |
| student_discussion | 864 张 | ~0.65 |
| student_posture | 2,410 张 | ~0.72 |





