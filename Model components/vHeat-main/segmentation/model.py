from mmdet.models.backbones.swin import BaseModule, MODELS
from mmseg.models.backbones.swin import MODELS as MODELS_mmseg
from vHeat.vHeat import vHeat
from torch import nn
import os
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils import checkpoint
from functools import partial


@MODELS.register_module()
class MMDET_VHEAT(BaseModule, vHeat):
    """
    在 MMSegmentation 中作为 backbone 的 vHeat 封装：
      - 与 detection 封装基本一致；差异主要在默认 img_size 与下游 head 的使用
      - 输出 out_indices 指定的多尺度特征
    """
    def __init__(self, patch_size=4, in_chans=3, num_classes=1000, depths=[2, 2, 9, 2], 
                 dims=[96, 192, 384, 768], drop_rate=0., attn_drop_rate=0., drop_path_rate=0.1,
                 norm_layer=nn.LayerNorm, patch_norm=True, post_norm=True, layer_scale=None,
                 use_checkpoint=False, out_indices=(0, 1, 2, 3), pretrained=None, img_size=512,
                 **kwargs,
        ):
        BaseModule.__init__(self)
        vHeat.__init__(self, patch_size=patch_size, in_chans=in_chans, num_classes=num_classes, depths=depths, 
                 dims=dims, drop_rate=drop_rate, attn_drop_rate=attn_drop_rate, drop_path_rate=drop_path_rate,
                 norm_layer=norm_layer, patch_norm=patch_norm, post_norm=post_norm, layer_scale=layer_scale, img_size=img_size,
                 use_checkpoint=use_checkpoint, **kwargs)
        
        # add norm ===========================
        self.out_indices = out_indices
        for i in out_indices:
            layer = nn.LayerNorm(self.dims[i])
            layer_name = f'outnorm{i}'
            self.add_module(layer_name, layer)
        
        # modify layer ========================
        # 同检测：将每个 stage 的 forward 改造成 (当前输出, 下采样输出)
        def layer_forward(self: nn.Sequential, x, *args, **kwargs):
            for blk in self[:-1]:
                if isinstance(blk, nn.Module):
                    if blk.use_checkpoint:
                        x = checkpoint.checkpoint(blk, x, *args, **kwargs)
                    else:
                        x = blk(x, *args, **kwargs)
                else:
                    if blk.use_checkpoint:
                        x = checkpoint.checkpoint(blk, x)
                    else:
                        x = blk(x)
            # y = None
            # if self.downsample is not None:
            y = self[-1](x)

            return x, y

        for l in self.layers:
            l.forward = partial(layer_forward, l)

        # delete head ===-======================
#         del self.head
#         del self.avgpool
#         del self.norm
        del self.classifier

        # load pretrained ======================
        if pretrained is not None:
            assert os.path.exists(pretrained)
            self.load_pretrained(pretrained)

    def load_pretrained(self, ckpt=""):
        _ckpt = torch.load(open(ckpt, "rb"), map_location=torch.device("cpu"))
        print(f"Successfully load ckpt {ckpt}")
        incompatibleKeys = self.load_state_dict(_ckpt['model'], strict=False)
        print(incompatibleKeys)

    def forward(self, x):
        # 导出多尺度特征；freq_embed 与分辨率不一致时，先插值
        x = self.patch_embed(x)
        outs = []
        y = x
        for i, layer in enumerate(self.layers):
        
            if y.shape[2:] != self.freq_embed[i].shape[:2]:
                #print(y.shape[2:])
                tmp = self.freq_embed[i].permute(2, 0, 1).contiguous().unsqueeze(0)
                tmp = F.interpolate(tmp, size=(y.shape[2], y.shape[3]), mode='bicubic').squeeze().permute(1, 2, 0).contiguous()
                x, y = layer(y, tmp) # (B, C, H, W)
            else:
                x, y = layer(y, self.freq_embed[i])
            if i in self.out_indices:
                norm_layer: nn.LayerNorm = getattr(self, f'outnorm{i}')
                out = norm_layer(x.permute(0, 2, 3, 1))
                out = out.permute(0, 3, 1, 2).contiguous()
            outs.append(out)
        return outs

    
@MODELS_mmseg.register_module()
class MMSEG_VHEAT(MMDET_VHEAT):
    ...