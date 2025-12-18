# YOLOv12-vHeat 迁移指南

本文档说明如何将集成好的 YOLOv12-vHeat 转移到新仓库，包括文件清单和环境配置。

---

## 一、必须转移的文件（核心代码）

### 1.1 核心代码目录

```
yolov12/yolov12/
├── ultralytics/                    # ✅ 必须 - 核心代码库
│   ├── __init__.py
│   ├── cfg/                        # ✅ 必须 - 配置文件（包含 yolov12.yaml）
│   │   ├── __init__.py
│   │   ├── datasets/               # 可选 - 数据集配置示例
│   │   └── models/
│   │       └── v12/
│   │           └── yolov12.yaml    # ✅ 必须 - vHeat 集成配置
│   ├── nn/                         # ✅ 必须 - 神经网络模块
│   │   ├── __init__.py
│   │   ├── modules/
│   │   │   ├── __init__.py         # ✅ 必须 - 导出 C2fHeat 等
│   │   │   ├── block.py            # ✅ 必须 - vHeat 核心实现
│   │   │   ├── conv.py
│   │   │   ├── head.py
│   │   │   └── ...
│   │   └── tasks.py                # ✅ 必须 - 模型构建（已注册 C2fHeat）
│   ├── engine/                     # ✅ 必须 - 训练/验证引擎
│   ├── data/                       # ✅ 必须 - 数据处理
│   ├── models/                     # ✅ 必须 - 模型定义
│   ├── utils/                      # ✅ 必须 - 工具函数
│   └── ...
├── train.py                        # ✅ 必须 - 训练/续训脚本
├── requirements.txt                 # ✅ 必须 - 依赖列表
├── pyproject.toml                   # ✅ 必须 - 项目配置
├── README.md                       # 可选 - 项目说明
└── vHeat_Integration_Documentation.md  # ✅ 推荐 - 集成文档
```

### 1.2 关键文件清单

**必须转移的文件：**

| 文件/目录 | 路径 | 说明 |
|---------|------|------|
| 核心代码 | `yolov12/yolov12/ultralytics/` | 整个目录，包含所有 Python 代码 |
| 模型配置 | `yolov12/yolov12/ultralytics/cfg/models/v12/yolov12.yaml` | vHeat 集成的模型配置 |
| 训练脚本 | `yolov12/yolov12/train.py` | 支持续训的训练脚本 |
| 依赖文件 | `yolov12/yolov12/requirements.txt` | Python 依赖 |
| 项目配置 | `yolov12/yolov12/pyproject.toml` | 包构建配置 |
| 集成文档 | `yolov12/yolov12/vHeat_Integration_Documentation.md` | vHeat 集成说明 |

**vHeat 核心实现位置：**
- `ultralytics/nn/modules/block.py` - 包含所有 vHeat 模块（第 84-260 行）
- `ultralytics/nn/modules/__init__.py` - 导出 C2fHeat 等模块
- `ultralytics/nn/tasks.py` - 注册 C2fHeat 到模型构建系统

---

## 二、可选转移的文件

### 2.1 文档和示例

```
yolov12/yolov12/
├── README.md                       # 可选 - 项目说明
├── examples/                       # 可选 - 示例代码
│   ├── *.ipynb
│   └── ...
├── tests/                          # 可选 - 测试代码
└── docker/                         # 可选 - Docker 配置
```

### 2.2 预训练权重（可选）

```
yolov12/yolov12/
└── yolov12n.pt                     # 可选 - 预训练权重（会自动下载）
```

**注意：** 预训练权重可以从官方源自动下载，无需手动转移。

---

## 三、不需要转移的文件

### 3.1 训练结果和缓存

```
runs/                               # ❌ 不需要 - 训练结果
├── train_vheat/                    # 训练输出
├── eval_vheat/                     # 评估结果
└── predict_vheat/                  # 预测结果

*.cache                            # ❌ 不需要 - 缓存文件
__pycache__/                       # ❌ 不需要 - Python 缓存
*.pyc                              # ❌ 不需要 - 编译文件
```

### 3.2 数据集

```
SCB5_Teacher_Behavior_Stand_BlackBoard_Sreen_20250406-2/  # ❌ 不需要
SCB5-Handrise-Read-write-2024-9-17/                        # ❌ 不需要
```

### 3.3 构建产物

```
ultralytics.egg-info/              # ❌ 不需要 - 安装信息
dist/                              # ❌ 不需要 - 构建产物
build/                             # ❌ 不需要 - 构建临时文件
```

### 3.4 其他项目文件

```
vHeat-main/                        # ❌ 不需要 - 原始 vHeat 代码（已集成）
评估与测试.py                      # ❌ 不需要 - 个人测试脚本
export_onnx.py                     # ❌ 不需要 - 个人导出脚本
*.whl                              # ❌ 不需要 - 本地 wheel 包
*.pdf                              # ❌ 不需要 - 论文等文档
```

---

## 四、快速迁移脚本

### 4.1 Windows PowerShell 脚本

创建 `migrate.ps1`：

```powershell
# YOLOv12-vHeat 迁移脚本
$sourceDir = "H:\毕业设计\嵌合\yolov12\yolov12"
$targetDir = "新仓库路径\yolov12-vheat"

# 创建目标目录
New-Item -ItemType Directory -Path $targetDir -Force

# 复制核心代码
Copy-Item -Path "$sourceDir\ultralytics" -Destination "$targetDir\ultralytics" -Recurse -Force

# 复制配置文件
Copy-Item -Path "$sourceDir\train.py" -Destination "$targetDir\train.py" -Force
Copy-Item -Path "$sourceDir\requirements.txt" -Destination "$targetDir\requirements.txt" -Force
Copy-Item -Path "$sourceDir\pyproject.toml" -Destination "$targetDir\pyproject.toml" -Force
Copy-Item -Path "$sourceDir\README.md" -Destination "$targetDir\README.md" -Force
Copy-Item -Path "$sourceDir\vHeat_Integration_Documentation.md" -Destination "$targetDir\vHeat_Integration_Documentation.md" -Force

# 清理不需要的文件
Get-ChildItem -Path $targetDir -Recurse -Include __pycache__,*.pyc,*.cache | Remove-Item -Recurse -Force

Write-Host "迁移完成！目标目录: $targetDir"
```

### 4.2 Linux/Mac Bash 脚本

创建 `migrate.sh`：

```bash
#!/bin/bash
# YOLOv12-vHeat 迁移脚本

SOURCE_DIR="yolov12/yolov12"
TARGET_DIR="新仓库路径/yolov12-vheat"

# 创建目标目录
mkdir -p "$TARGET_DIR"

# 复制核心代码
cp -r "$SOURCE_DIR/ultralytics" "$TARGET_DIR/"

# 复制配置文件
cp "$SOURCE_DIR/train.py" "$TARGET_DIR/"
cp "$SOURCE_DIR/requirements.txt" "$TARGET_DIR/"
cp "$SOURCE_DIR/pyproject.toml" "$TARGET_DIR/"
cp "$SOURCE_DIR/README.md" "$TARGET_DIR/"
cp "$SOURCE_DIR/vHeat_Integration_Documentation.md" "$TARGET_DIR/"

# 清理不需要的文件
find "$TARGET_DIR" -type d -name __pycache__ -exec rm -r {} + 2>/dev/null
find "$TARGET_DIR" -name "*.pyc" -delete
find "$TARGET_DIR" -name "*.cache" -delete

echo "迁移完成！目标目录: $TARGET_DIR"
```

---

## 五、环境配置

### 5.1 Python 环境要求

- **Python 版本：** 3.8 - 3.12
- **推荐版本：** Python 3.10

### 5.2 CUDA 环境（GPU 训练）

- **CUDA 版本：** 11.8 或 12.1（推荐）
- **cuDNN：** 与 CUDA 版本匹配

### 5.3 安装步骤

#### 步骤 1：创建虚拟环境

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

#### 步骤 2：安装 PyTorch（根据 CUDA 版本选择）

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

#### 步骤 3：安装项目依赖

```bash
cd yolov12-vheat
pip install -e .
```

或手动安装依赖：

```bash
pip install -r requirements.txt
```

**注意：** `requirements.txt` 中可能包含特定平台的包（如 flash_attn），如果安装失败可以跳过或使用对应平台的版本。

#### 步骤 4：验证安装

```bash
python -c "from ultralytics import YOLO; from ultralytics.nn.modules import C2fHeat; print('✅ vHeat 集成成功！')"
```

---

## 六、环境配置详细说明

### 6.1 依赖包说明

**核心依赖（requirements.txt）：**
- `torch>=2.1.0` - PyTorch 深度学习框架
- `torchvision>=0.16.0` - 计算机视觉工具
- `numpy>=1.23.0` - 数值计算
- `opencv-python>=4.6.0` - 图像处理
- `pyyaml>=5.3.1` - YAML 解析
- `ultralytics-thop>=2.0.0` - FLOPs 计算

**可选依赖：**
- `flash-attn` - Flash Attention（需要 CUDA 11.8+ 和特定 GPU）
- `albumentations` - 数据增强
- `onnx`, `onnxruntime` - ONNX 导出和推理
- `tensorboard` - 训练可视化

### 6.2 常见问题解决

#### 问题 1：torchvision 导入错误

**错误：** `AttributeError: partially initialized module 'torchvision'`

**解决：**
```bash
pip uninstall -y torchvision
pip install --index-url https://download.pytorch.org/whl/cu121 torchvision==0.16.0
```

#### 问题 2：CUDA 版本不匹配

**检查 CUDA 版本：**
```bash
nvidia-smi  # 查看驱动支持的 CUDA 版本
python -c "import torch; print(torch.version.cuda)"  # 查看 PyTorch 的 CUDA 版本
```

**解决：** 安装与系统 CUDA 版本匹配的 PyTorch

#### 问题 3：flash-attn 安装失败

**解决：** flash-attn 是可选的，如果安装失败可以跳过。vHeat 不依赖 flash-attn。

---

## 七、验证迁移

### 7.1 检查文件完整性

```bash
# 检查核心文件是否存在
ls ultralytics/nn/modules/block.py      # vHeat 实现
ls ultralytics/nn/modules/__init__.py   # 模块导出
ls ultralytics/nn/tasks.py              # 模型构建
ls ultralytics/cfg/models/v12/yolov12.yaml  # 模型配置
ls train.py                             # 训练脚本
```

### 7.2 测试模型加载

```python
from ultralytics import YOLO

# 测试加载模型配置
model = YOLO('ultralytics/cfg/models/v12/yolov12.yaml')
print("✅ 模型配置加载成功！")

# 检查 C2fHeat 是否注册
from ultralytics.nn.modules import C2fHeat
print("✅ C2fHeat 模块导入成功！")
```

### 7.3 测试训练（可选）

```bash
# 使用示例数据集测试
yolo detect train \
  data=coco8.yaml \
  model=ultralytics/cfg/models/v12/yolov12.yaml \
  epochs=1 \
  imgsz=640 \
  batch=1
```

---

## 八、新仓库结构建议

```
yolov12-vheat/
├── ultralytics/                    # 核心代码
│   └── ...
├── train.py                        # 训练脚本
├── requirements.txt                # 依赖
├── pyproject.toml                  # 项目配置
├── README.md                       # 项目说明
├── vHeat_Integration_Documentation.md  # 集成文档
├── MIGRATION_GUIDE.md              # 本文档
├── .gitignore                      # Git 忽略文件
└── LICENSE                         # 许可证
```

### 8.1 推荐的 .gitignore

```
# Python
__pycache__/
*.py[cod]
*.so
*.egg-info/
dist/
build/

# 训练结果
runs/
*.pt
*.onnx

# 数据集
data/
datasets/

# IDE
.vscode/
.idea/
*.swp

# 系统
.DS_Store
Thumbs.db
```

---

## 九、迁移检查清单

- [ ] 复制 `ultralytics/` 整个目录
- [ ] 复制 `train.py`
- [ ] 复制 `requirements.txt`
- [ ] 复制 `pyproject.toml`
- [ ] 复制 `vHeat_Integration_Documentation.md`
- [ ] 创建虚拟环境
- [ ] 安装 PyTorch（匹配 CUDA 版本）
- [ ] 安装项目依赖
- [ ] 验证 `C2fHeat` 导入
- [ ] 测试模型配置加载
- [ ] 清理 `__pycache__` 和缓存文件

---

## 十、快速开始

迁移完成后，在新仓库中：

```bash
# 1. 激活环境
conda activate yolov12-vheat

# 2. 进入项目目录
cd yolov12-vheat

# 3. 安装依赖
pip install -e .

# 4. 验证安装
python -c "from ultralytics import YOLO; from ultralytics.nn.modules import C2fHeat; print('✅ 安装成功！')"

# 5. 开始训练
python train.py --data your_dataset.yaml --epochs 300 --batch 16 --device 0
```

---

## 十一、总结

**必须转移：**
- `ultralytics/` 整个目录（核心代码）
- `train.py`（训练脚本）
- `requirements.txt`（依赖）
- `pyproject.toml`（项目配置）
- `vHeat_Integration_Documentation.md`（集成文档）

**环境配置：**
- Python 3.8-3.12（推荐 3.10）
- PyTorch 2.1.0 + torchvision 0.16.0
- CUDA 11.8 或 12.1（GPU 训练）

**验证：**
- 检查文件完整性
- 测试模块导入
- 测试模型加载

---

*文档生成时间：2025年*
*YOLOv12-vHeat 迁移指南 v1.0*

