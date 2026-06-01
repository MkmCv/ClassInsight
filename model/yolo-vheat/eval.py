#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
YOLOv12-vHeat 评估脚本
用于评估训练好的模型在验证集上的性能
"""

from ultralytics import YOLO
import argparse
import os


def parse_args():
    parser = argparse.ArgumentParser(description="YOLOv12-vHeat Evaluation Script")
    parser.add_argument("--model", type=str, required=True, help="模型权重文件路径 (.pt)")
    parser.add_argument("--data", type=str, required=True, help="数据集 YAML 文件路径")
    parser.add_argument("--imgsz", type=int, default=640, help="输入图片尺寸")
    parser.add_argument("--conf", type=float, default=0.001, help="置信度阈值")
    parser.add_argument("--iou", type=float, default=0.7, help="NMS IoU 阈值")
    parser.add_argument("--device", type=str, default="0", help="设备 (GPU ID 或 'cpu')")
    parser.add_argument("--project", type=str, default=os.path.join("runs", "val"), help="结果保存目录")
    parser.add_argument("--name", type=str, default="eval", help="评估名称")
    parser.add_argument("--split", type=str, default="val", choices=["train", "val", "test"], help="数据集划分")
    parser.add_argument("--save_json", action="store_true", help="保存 JSON 格式结果")
    parser.add_argument("--save_hybrid", action="store_true", help="保存混合标签")
    parser.add_argument("--plots", action="store_true", default=True, help="生成可视化图表")
    return parser.parse_args()


def main():
    args = parse_args()
    
    # 检查模型文件是否存在
    if not os.path.exists(args.model):
        print(f"❌ 错误: 模型文件不存在: {args.model}")
        return 1
    
    # 检查数据集文件是否存在
    if not os.path.exists(args.data):
        print(f"❌ 错误: 数据集配置文件不存在: {args.data}")
        return 1
    
    print("=" * 60)
    print("  YOLOv12-vHeat 模型评估")
    print("=" * 60)
    print(f"模型: {args.model}")
    print(f"数据集: {args.data}")
    print(f"图片尺寸: {args.imgsz}")
    print(f"置信度阈值: {args.conf}")
    print(f"IoU 阈值: {args.iou}")
    print(f"设备: {args.device}")
    print(f"数据集划分: {args.split}")
    print("=" * 60)
    print()
    
    try:
        # 加载模型
        print("📦 加载模型...")
        model = YOLO(args.model)
        print("✅ 模型加载成功")
        
        # 执行评估
        print("\n📊 开始评估...")
        metrics = model.val(
            data=args.data,
            imgsz=args.imgsz,
            conf=args.conf,
            iou=args.iou,
            device=args.device,
            project=args.project,
            name=args.name,
            split=args.split,
            save_json=args.save_json,
            save_hybrid=args.save_hybrid,
            plots=args.plots,
        )
        
        # 打印结果
        print("\n" + "=" * 60)
        print("  评估结果")
        print("=" * 60)
        
        if hasattr(metrics, 'box'):
            print(f"mAP50:     {metrics.box.map50:.4f}")
            print(f"mAP50-95:  {metrics.box.map:.4f}")
            print(f"Precision: {metrics.box.mp:.4f}")
            print(f"Recall:    {metrics.box.mr:.4f}")
        
        print(f"\n结果保存在: {os.path.join(args.project, args.name)}")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 评估失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    exit_code = main()
    sys.exit(exit_code)

