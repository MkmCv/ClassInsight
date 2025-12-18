import os
import torch
import torch.nn.functional as F

from functools import partial

from .vHeat import vHeat

# =============================================================
# 模型装配入口
# - 依据 config 中的 MODEL.TYPE/ VHEAT 子配置，实例化对应模型（当前只支持 vHeat）
# - 将通用配置（如 IMG_SIZE/ NUM_CLASSES/ DROP_PATH_RATE）映射到模型构造参数
# - 当处于吞吐测试模式时，调用 model.infer_init() 预计算频域衰减因子以提升速度
# =============================================================


def build_vHeat_model(config, is_pretrain=False):
    model_type = config.MODEL.TYPE
    
    if model_type in ["vHeat"]:
        model = vHeat(
            in_chans=config.MODEL.VHEAT.IN_CHANS, 
            patch_size=config.MODEL.VHEAT.PATCH_SIZE, 
            num_classes=config.MODEL.NUM_CLASSES, 
            depths=config.MODEL.VHEAT.DEPTHS, 
            dims=config.MODEL.VHEAT.EMBED_DIM, 
            drop_path_rate=config.MODEL.DROP_PATH_RATE,
            mlp_ratio=config.MODEL.VHEAT.MLP_RATIO,
            post_norm=config.MODEL.VHEAT.POST_NORM,
            layer_scale=config.MODEL.VHEAT.LAYER_SCALE,
            img_size=config.DATA.IMG_SIZE,
            # infer_mode 开启时 forward_features 不再传递 freq_embed，
            # 转而使用预计算的 k_exp，加速吞吐/纯推理测试。
            infer_mode=config.EVAL_MODE or config.THROUGHPUT_MODE,
        )
        if config.THROUGHPUT_MODE:
            # 预计算每个 Heat2D 的频域衰减系数，以避免前向时重复映射
            model.infer_init()
        return model
    
    
def build_model(config, is_pretrain=False):
    # 目前仅有 vHeat，一个中转以便后续扩展其它骨干
    model = build_vHeat_model(config, is_pretrain)
    return model
