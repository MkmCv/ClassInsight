# 视觉算法

本目录存放系统所依赖的视觉算法。

## yolo-vheat（git 子模块）

`yolo-vheat/` 是一个 **git 子模块**，指向独立维护的算法仓库 [YOLO12-vHeat](https://github.com/MkmCv/YOLO12-vHeat)：YOLOv12 集成 vHeat（热传导算子骨干）的目标检测框架，提供后端所用的定制版 `ultralytics` 包。

### 拉取子模块

```bash
# 克隆主仓库时一并拉取
git clone --recurse-submodules <ClassInsight 仓库地址>

# 或在已有克隆中补拉
git submodule update --init --recursive
```

### 安装（供后端使用）

```bash
# 按 CUDA 版本安装 PyTorch（示例 CUDA 12.1）
pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu121

# 以可编辑模式安装定制版 ultralytics（含 vHeat 模块）
cd model/yolo-vheat
pip install -e .

# 验证
python -c "from ultralytics import YOLO; from ultralytics.nn.modules import C2fHeat; print('OK')"
```

算法本身的训练 / 评估 / 集成说明见子模块仓库的文档。

## dataset/

`dataset/` 用于本地存放训练 / 评估数据集，**不纳入版本控制**（见根目录 `.gitignore`）。
