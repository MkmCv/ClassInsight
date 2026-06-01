### vHeat 知识文档（Windows 友好）

本页汇总项目结构、依赖、配置与常用任务入口，配合 `Windows-Setup.md` 完成环境与运行。

#### 目录结构
```
vHeat/
  classification/        # 分类训练与评测入口
    main.py              # 训练/验证主脚本（默认 DDP）
    data/                # ImageNet/IN22K 数据构建
    models/              # vHeat 模型实现
    configs/             # 分类配置（yacs yaml）
    interpolate4downstream.py  # 下游任务权重插值

  detection/             # 基于 MMDetection 的检测
    tools/train.py       # 训练入口（Runner）
    tools/test.py        # 评测入口
    configs/             # 检测配置（包含 vheat 配置）

  segmentation/          # 基于 MMSegmentation 的分割
    tools/train.py
    tools/test.py
    configs/             # 分割配置（包含 vheat 配置）

  requirements.txt       # 基础依赖（分类）
  README.md              # 官方说明与命令示例
  docs/
    Windows-Setup.md     # Windows 环境配置与速查
    Knowledge-Base.md    # 本页
```

#### 关键依赖与版本建议
- PyTorch 2.2+、CUDA 12.1（按本机选择，见 PyTorch 官网安装指令）
- timm、yacs、tensorboardX、fvcore（见 `requirements.txt`）
- 可选：mmengine==0.10.1、mmcv==2.1.0、mmdet==3.3.0、mmsegmentation==1.2.2、mmpretrain==1.2.0

Windows 原生环境推荐先跑分类；检测/分割如遇编译/算子问题，使用 WSL2。

#### 配置与数据
- 配置文件：`classification/configs/vHeat/*.yaml`，通过 `--cfg` 传入。
- 数据路径：配置键 `DATA.DATA_PATH` 指向 ImageNet 根目录（见 Windows-Setup 的目录结构）。
- 批大小/线程数：`DATA.BATCH_SIZE`、`DATA.NUM_WORKERS`；Windows 下若卡顿可将 `NUM_WORKERS` 降到 0/2/4。

#### 分类任务常用命令（单卡）
评测：
```bash
cd classification
python main.py --cfg configs/vHeat/vHeat_tiny_224.yaml --data-path <DATA_PATH> --batch-size 64 --output outputs --resume <CKPT_PATH> --eval --model_ema False --local_rank 0
```

训练（单卡简化，必要时将 backend 改为 gloo）：
```bash
set WORLD_SIZE=1 & set RANK=0 & set LOCAL_RANK=0
python main.py --cfg configs/vHeat/vHeat_tiny_224.yaml --data-path <DATA_PATH> --batch-size 32 --output outputs --local_rank 0
```

多卡与更高性能建议使用 WSL2/Linux + NCCL。

#### 检测 / 分割（推荐 WSL2）
示例命令（Linux/WSL2）：
```bash
bash detection/tools/dist_train.sh detection/configs/vheat/mask_rcnn_fpn_coco_tiny.py 8
bash detection/tools/dist_test.sh  detection/configs/vheat/mask_rcnn_fpn_coco_tiny.py <CKPT> 1

bash segmentation/tools/dist_train.sh segmentation/configs/vheat/upernet_vheat_160k_ade20k_512x512_tiny.py 8
bash segmentation/tools/dist_test.sh  segmentation/configs/vheat/upernet_vheat_160k_ade20k_512x512_tiny.py <CKPT> 1
```

Windows 原生如需运行，可直接调用 Python 入口：
```bash
python detection/tools/train.py detection/configs/vheat/mask_rcnn_fpn_coco_tiny.py --work-dir work_dirs/vheat_tiny
python segmentation/tools/train.py segmentation/configs/vheat/upernet_vheat_160k_ade20k_512x512_tiny.py --work-dir work_dirs/vheat_tiny
```

若遇到 mmcv/cuda 相关错误，优先切换到 WSL2。

#### 下游任务权重插值
将 224 的分类权重插值到 512（供分割/检测）：
```bash
python classification/interpolate4downstream.py --pt_pth <CLS_CKPT> --pt_size 224 --tg_pth <OUT_PTH> --tg_size 512
```

#### 日志、输出与断点
- 分类输出目录：`--output`（默认 `output/`），脚本会保存 `config.json`、日志与权重。
- 断点恢复：`--resume` 传入权重路径；分类脚本支持自动从输出目录找到最新断点。

#### 性能与稳定性建议
- 降低 `batch-size` 以缓解显存压力；开启 AMP（默认已支持）。
- `NUM_WORKERS` 适配 Windows；必要时关闭 `pin_memory`。
- 在评测模式下可用 `--model_ema False` 缩短推理时间。

#### 常见问题快速定位
- NCCL 报错：Windows 不支持，单卡使用 gloo 或 WSL2。
- mmcv 安装失败：核对 PyTorch/CUDA 版本；使用预编译轮子；不行则 WSL2。
- 数据加载慢/卡：降低 `NUM_WORKERS`；磁盘 I/O 受限时避免 zip 模式。




