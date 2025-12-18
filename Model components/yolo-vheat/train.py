from ultralytics import YOLO
import argparse
import os


def parse_args():
    parser = argparse.ArgumentParser(description="YOLOv12 Train/Resume Helper")
    parser.add_argument("--data", type=str, default=r"H:/毕业设计/嵌合/SCB5_Teacher_Behavior_Stand_BlackBoard_Sreen_20250406-2/SCB5_Teacher_Behavior_Stand_BlackBoard_Sreen_20250406.yaml")
    parser.add_argument("--model", type=str, default=os.path.join("ultralytics", "cfg", "models", "v12", "yolov12.yaml"))
    parser.add_argument("--epochs", type=int, default=300)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--project", type=str, default=os.path.join("runs", "train_vheat"))
    parser.add_argument("--name", type=str, default="scb5_vheat_py")
    parser.add_argument("--device", type=str, default="0")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--cache", type=str, default="False")  # 'ram' / 'disk' / 'False'
    parser.add_argument("--deterministic", type=str, default="False")  # 'True' or 'False'
    parser.add_argument("--mosaic", type=float, default=1.0)
    parser.add_argument("--mixup", type=float, default=0.0)
    parser.add_argument("--copy_paste", type=float, default=0.1)
    parser.add_argument("--auto_augment", type=str, default="randaugment")
    parser.add_argument("--val", type=str, default="True")  # 'True' or 'False'
    parser.add_argument("--resume", action="store_true", help="Resume training from last checkpoint")
    parser.add_argument("--resume_from", type=str, default="", help="Path to last.pt to resume from")
    parser.add_argument("--save_period", type=int, default=-1)
    parser.add_argument("--exist_ok", action="store_true")
    return parser.parse_args()


def str2bool(v: str):
    return str(v).lower() in {"1", "true", "t", "yes", "y"}


def main():
    args = parse_args()

    cache = args.cache if args.cache.lower() in {"ram", "disk"} else False
    deterministic = str2bool(args.deterministic)
    do_val = str2bool(args.val)

    # Resolve resume path if requested
    resume_path = args.resume_from
    if args.resume and not resume_path:
        candidate = os.path.join(args.project, args.name, "weights", "last.pt")
        if os.path.exists(candidate):
            resume_path = candidate

    if args.resume:
        model_source = resume_path if resume_path else args.model
        model = YOLO(model_source)
        results = model.train(
            data=args.data,
            epochs=args.epochs,
            batch=args.batch,
            imgsz=args.imgsz,
            device=args.device,
            project=args.project,
            name=args.name,
            workers=args.workers,
            cache=cache,
            deterministic=deterministic,
            mosaic=args.mosaic,
            mixup=args.mixup,
            copy_paste=args.copy_paste,
            auto_augment=args.auto_augment,
            optimizer="auto",
            resume=True,
            save_period=args.save_period,
            exist_ok=args.exist_ok,
            val=do_val,
        )
    else:
        model = YOLO(args.model)
        results = model.train(
            data=args.data,
            epochs=args.epochs,
            batch=args.batch,
            imgsz=args.imgsz,
            device=args.device,
            project=args.project,
            name=args.name,
            workers=args.workers,
            cache=cache,
            deterministic=deterministic,
            mosaic=args.mosaic,
            mixup=args.mixup,
            copy_paste=args.copy_paste,
            auto_augment=args.auto_augment,
            optimizer="auto",
            resume=False,
            save_period=args.save_period,
            exist_ok=args.exist_ok,
            val=do_val,
        )

    if do_val:
        metrics = model.val()


if __name__ == "__main__":
    main()
