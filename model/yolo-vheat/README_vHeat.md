# YOLOv12-vHeat

YOLOv12 集成 vHeat（基于热传导算子的视觉模型）的目标检测框架。

## 📋 目录

- [特性](#特性)
- [环境配置](#环境配置)
- [数据集准备](#数据集准备)
- [训练](#训练)
- [评估](#评估)
- [使用示例](#使用示例)
- [常见问题](#常见问题)

---

## ✨ 特性

- ✅ **vHeat 完整集成**：基于热传导算子的全局感受野增强
- ✅ **即插即用**：可直接替换标准 YOLOv12 模型
- ✅ **灵活配置**：支持通过 YAML 调整热传导参数
- ✅ **完整工具链**：训练、验证、推理一体化

---

## 🔧 环境配置

### 1. Python 环境

- **Python 版本：** 3.8 - 3.12（推荐 3.10）
- **创建虚拟环境：**

```bash
# 使用 conda（推荐）
conda create -n yolov12-vheat python=3.10
conda activate yolov12-vheat

# 或使用 venv
python -m venv yolov12-vheat
# Windows
yolov12-vheat\Scripts\activate
# Linux/Mac
source yolov12-vheat/bin/activate
```

### 2. 安装 PyTorch

**CUDA 12.1（推荐）：**
```bash
pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu121
```

**CUDA 11.8：**
```bash
pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu118
```

**CPU 版本：**
```bash
pip install torch==2.1.0 torchvision==0.16.0
```

### 3. 安装项目依赖

```bash
# 进入项目目录
cd yolov12-vheat

# 安装项目（推荐）
pip install -e .

# 或手动安装依赖
pip install -r requirements.txt
```

### 4. 验证安装

```bash
# 运行环境检查脚本
python check_environment.py

# 或快速验证
python -c "from ultralytics import YOLO; from ultralytics.nn.modules import C2fHeat; print('✅ 安装成功！')"
```

---

## 📁 数据集准备

### 1. 数据集目录结构

YOLOv12-vHeat 使用 YOLO 格式的数据集。推荐的数据集目录结构如下：

```
your_dataset/
├── images/
│   ├── train/          # 训练图片
│   │   ├── img1.jpg
│   │   ├── img2.jpg
│   │   └── ...
│   └── val/            # 验证图片
│       ├── img1.jpg
│       ├── img2.jpg
│       └── ...
└── labels/
    ├── train/          # 训练标签（与图片同名，.txt 格式）
    │   ├── img1.txt
    │   ├── img2.txt
    │   └── ...
    └── val/            # 验证标签
        ├── img1.txt
        ├── img2.txt
        └── ...
```

### 2. 标签格式（YOLO 格式）

每个 `.txt` 文件对应一张图片，格式为：

```
class_id center_x center_y width height
```

**注意：**
- 所有坐标值必须是**归一化到 0-1 之间**的浮点数
- 每行一个目标
- `class_id` 从 0 开始

**示例：**
```
0 0.5 0.5 0.3 0.4
1 0.2 0.3 0.1 0.2
```

### 3. 创建数据集配置文件

在项目根目录或 `ultralytics/cfg/datasets/` 目录下创建数据集 YAML 文件，例如 `my_dataset.yaml`：

```yaml
# 数据集路径（绝对路径或相对路径）
path: /path/to/your_dataset  # 或相对路径: ../datasets/my_dataset

# 训练和验证图片路径（相对于 path）
train: images/train
val: images/val
test: images/val  # 可选，测试集

# 类别数量
nc: 8

# 类别名称
names:
  0: class1
  1: class2
  2: class3
  3: class4
  4: class5
  5: class6
  6: class7
  7: class8
```

**完整示例：**

```yaml
path: /home/user/datasets/my_dataset
train: images/train
val: images/val
test: images/val

nc: 3
names:
  0: person
  1: car
  2: bicycle
```

### 4. 数据集放置建议

**方式 1：放在项目外（推荐）**
```
/home/user/
├── yolov12-vheat/          # 项目目录
└── datasets/               # 数据集目录
    └── my_dataset/
        ├── images/
        └── labels/
```

YAML 配置：
```yaml
path: /home/user/datasets/my_dataset
```

**方式 2：放在项目内**
```
yolov12-vheat/
├── ultralytics/
├── datasets/                # 数据集目录
│   └── my_dataset/
│       ├── images/
│       └── labels/
└── my_dataset.yaml
```

YAML 配置：
```yaml
path: datasets/my_dataset
```

### 5. 数据集检查

在训练前，建议检查数据集：

```bash
# 检查图片和标签是否匹配
python -c "
from pathlib import Path
train_img_dir = Path('your_dataset/images/train')
train_label_dir = Path('your_dataset/labels/train')
imgs = {f.stem for f in train_img_dir.glob('*.jpg')}
labels = {f.stem for f in train_label_dir.glob('*.txt')}
missing_labels = imgs - labels
missing_imgs = labels - imgs
if missing_labels:
    print(f'⚠️  缺少标签: {len(missing_labels)} 张图片')
if missing_imgs:
    print(f'⚠️  缺少图片: {len(missing_imgs)} 个标签文件')
if not missing_labels and not missing_imgs:
    print('✅ 数据集检查通过')
"
```

---

## 🚀 训练

### 方法 1：使用命令行（推荐）

#### 基础训练

```bash
yolo detect train \
  data=my_dataset.yaml \
  model=ultralytics/cfg/models/v12/yolov12.yaml \
  epochs=300 \
  batch=16 \
  imgsz=640 \
  device=0
```

#### 完整参数训练

```bash
yolo detect train \
  data=my_dataset.yaml \
  model=ultralytics/cfg/models/v12/yolov12.yaml \
  epochs=300 \
  batch=16 \
  imgsz=640 \
  device=0 \
  project=runs/train \
  name=my_experiment \
  workers=8 \
  cache=ram \
  deterministic=False
```

#### 使用不同模型规模

```bash
# 使用 s 规模（需要先创建 yolov12s.yaml 或使用 scale 参数）
yolo detect train \
  data=my_dataset.yaml \
  model=ultralytics/cfg/models/v12/yolov12.yaml \
  epochs=300 \
  batch=16 \
  imgsz=640 \
  device=0
```

### 方法 2：使用 Python 脚本

#### 基础训练

```bash
python train.py \
  --data my_dataset.yaml \
  --epochs 300 \
  --batch 16 \
  --imgsz 640 \
  --device 0
```

#### 完整参数训练

```bash
python train.py \
  --data my_dataset.yaml \
  --model ultralytics/cfg/models/v12/yolov12.yaml \
  --epochs 300 \
  --batch 16 \
  --imgsz 640 \
  --device 0 \
  --project runs/train \
  --name my_experiment \
  --workers 8 \
  --cache ram \
  --deterministic False
```

#### 断点续训

```bash
# 自动从上次训练继续
python train.py --resume --project runs/train --name my_experiment --device 0

# 指定权重文件继续
python train.py \
  --resume \
  --resume_from runs/train/my_experiment/weights/last.pt \
  --device 0
```

### 训练参数说明

| 参数 | 说明 | 默认值 | 推荐值 |
|------|------|--------|--------|
| `data` | 数据集 YAML 文件路径 | - | 必需 |
| `model` | 模型配置文件 | `yolov12.yaml` | - |
| `epochs` | 训练轮数 | 300 | 100-500 |
| `batch` | 批次大小 | 16 | 根据显存调整 |
| `imgsz` | 输入图片尺寸 | 640 | 640/768/800 |
| `device` | 设备（GPU ID 或 cpu） | 0 | 0/1/2... |
| `workers` | 数据加载线程数 | 8 | 4-8 |
| `cache` | 数据缓存（ram/disk/False） | False | ram（显存够） |
| `project` | 项目保存目录 | `runs/train` | - |
| `name` | 实验名称 | `exp` | - |

### 训练输出

训练结果保存在 `runs/train/<name>/` 目录下：

```
runs/train/my_experiment/
├── weights/
│   ├── best.pt          # 最佳模型权重
│   └── last.pt          # 最新模型权重
├── results.csv          # 训练指标
├── args.yaml            # 训练参数
├── labels.jpg           # 标签可视化
└── train_batch*.jpg     # 训练批次可视化
```

### 训练监控

训练过程中会显示：
- **损失值：** `box_loss`（边界框损失）、`cls_loss`（分类损失）、`dfl_loss`（分布焦点损失）
- **验证指标：** `P`（精确率）、`R`（召回率）、`mAP50`、`mAP50-95`

**好的指标参考：**
- `mAP50` ≥ 0.70
- `mAP50-95` ≥ 0.40
- `P` 和 `R` 平衡（根据任务需求调整）

---

## 📊 评估

### 方法 1：使用命令行

#### 基础评估

```bash
yolo detect val \
  model=runs/train/my_experiment/weights/best.pt \
  data=my_dataset.yaml \
  imgsz=640 \
  device=0
```

#### 完整参数评估

```bash
yolo detect val \
  model=runs/train/my_experiment/weights/best.pt \
  data=my_dataset.yaml \
  imgsz=640 \
  device=0 \
  conf=0.001 \
  iou=0.7 \
  project=runs/val \
  name=my_evaluation
```

### 方法 2：使用 Python 脚本

创建 `eval.py`：

```python
from ultralytics import YOLO

# 加载模型
model = YOLO('runs/train/my_experiment/weights/best.pt')

# 评估
metrics = model.val(
    data='my_dataset.yaml',
    imgsz=640,
    device=0,
    conf=0.001,
    iou=0.7,
    project='runs/val',
    name='my_evaluation'
)

# 打印结果
print(f"mAP50: {metrics.box.map50}")
print(f"mAP50-95: {metrics.box.map}")
```

运行：
```bash
python eval.py
```

### 评估参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `model` | 模型权重文件路径 | - |
| `data` | 数据集 YAML 文件 | - |
| `imgsz` | 输入图片尺寸 | 640 |
| `conf` | 置信度阈值 | 0.001 |
| `iou` | NMS IoU 阈值 | 0.7 |
| `project` | 结果保存目录 | `runs/val` |
| `name` | 评估名称 | `val` |

### 评估输出

评估结果保存在 `runs/val/<name>/` 目录下：

```
runs/val/my_evaluation/
├── confusion_matrix.png           # 混淆矩阵
├── confusion_matrix_normalized.png # 归一化混淆矩阵
├── F1_curve.png                   # F1 曲线
├── P_curve.png                    # 精确率曲线
├── PR_curve.png                   # PR 曲线
├── R_curve.png                    # 召回率曲线
└── val_batch*.jpg                 # 验证批次可视化
```

### 评估指标说明

- **P (Precision)：** 精确率，预测为正的样本中真正为正的比例
- **R (Recall)：** 召回率，所有正样本中被正确预测的比例
- **mAP50：** IoU=0.5 时的平均精度
- **mAP50-95：** IoU 从 0.5 到 0.95 的平均精度（更严格）

---

## 💡 使用示例

### 示例 1：完整训练流程

```bash
# 1. 准备数据集（按照上述数据集准备步骤）

# 2. 创建数据集 YAML 文件
# 编辑 my_dataset.yaml

# 3. 开始训练
yolo detect train \
  data=my_dataset.yaml \
  model=ultralytics/cfg/models/v12/yolov12.yaml \
  epochs=300 \
  batch=16 \
  imgsz=640 \
  device=0 \
  project=runs/train \
  name=my_first_training

# 4. 评估模型
yolo detect val \
  model=runs/train/my_first_training/weights/best.pt \
  data=my_dataset.yaml \
  imgsz=640 \
  device=0
```

### 示例 2：使用 Python API

```python
from ultralytics import YOLO

# 加载模型配置
model = YOLO('ultralytics/cfg/models/v12/yolov12.yaml')

# 训练
results = model.train(
    data='my_dataset.yaml',
    epochs=300,
    batch=16,
    imgsz=640,
    device=0,
    project='runs/train',
    name='my_training'
)

# 评估
metrics = model.val(
    data='my_dataset.yaml',
    imgsz=640,
    device=0
)

# 推理
results = model.predict('path/to/image.jpg', save=True)
```

### 示例 3：断点续训

```bash
# 训练中断后继续
python train.py \
  --resume \
  --resume_from runs/train/my_training/weights/last.pt \
  --epochs 400 \
  --device 0
```

---

## ❓ 常见问题

### Q1: 训练时出现 "KeyError: 'C2fHeat'"

**原因：** 模块未正确注册

**解决：**
1. 检查 `ultralytics/nn/modules/__init__.py` 是否导出 `C2fHeat`
2. 检查 `ultralytics/nn/tasks.py` 是否导入和注册 `C2fHeat`
3. 运行 `python check_environment.py` 检查环境

### Q2: 训练时显存不足

**解决：**
- 减小 `batch` 大小（如 8 或 4）
- 减小 `imgsz`（如 512）
- 使用 `batch=-1` 让系统自动选择最大批次

### Q3: 训练速度很慢

**解决：**
- 使用 `cache=ram` 缓存数据到内存
- 增加 `workers` 数量（但不要超过 CPU 核心数）
- 使用 `deterministic=False` 关闭确定性模式
- 检查 GPU 是否被正确使用

### Q4: 评估时找不到模型文件

**解决：**
- 检查权重文件路径是否正确
- 确认训练已完成并保存了权重
- 使用绝对路径或相对于项目根目录的路径

### Q5: 数据集标签格式错误

**解决：**
- 确保所有坐标值在 0-1 之间（归一化）
- 检查标签文件与图片文件是否一一对应
- 使用数据集检查脚本验证

### Q6: 如何调整 vHeat 参数

**方法：** 编辑 `ultralytics/cfg/models/v12/yolov12.yaml`，修改 `C2fHeat` 的参数：

```yaml
- [-1, 2, C2fHeat, [512, False, 1, 1.0, 0.25, 40]]
# 参数说明: [c2, shortcut, n, time_step, e, base_size]
```

- `time_step`: 热扩散强度（0.5-1.5）
- `base_size`: 频率嵌入基础尺寸（浅层 40，深层 20）
- `e`: 扩展比（0.25-0.5）

---

## 📚 相关文档

- [vHeat 集成文档](vHeat_Integration_Documentation.md) - vHeat 集成详细说明
- [迁移指南](MIGRATION_GUIDE.md) - 从旧仓库迁移的指南
- [环境检查脚本](check_environment.py) - 环境配置检查工具

---

## 📝 许可证

本项目遵循 AGPL-3.0 许可证。

---

## 🙏 致谢

- [YOLOv12](https://github.com/sunsmarterjie/yolov12) - 基础检测框架
- [vHeat](https://github.com/OpenGVLab/vHeat) - 热传导算子实现

---

*最后更新：2025年*

