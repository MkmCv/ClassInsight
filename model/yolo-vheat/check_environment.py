#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
YOLOv12-vHeat 环境检查脚本
检查环境配置是否正确，包括 Python、PyTorch、CUDA 和 vHeat 集成
"""

import sys
import os
from pathlib import Path

def print_header(text):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def print_success(text):
    """打印成功信息"""
    print(f"✅ {text}")

def print_error(text):
    """打印错误信息"""
    print(f"❌ {text}")

def print_warning(text):
    """打印警告信息"""
    print(f"⚠️  {text}")

def print_info(text):
    """打印信息"""
    print(f"ℹ️  {text}")

def check_python_version():
    """检查 Python 版本"""
    print_header("1. Python 版本检查")
    version = sys.version_info
    print_info(f"Python 版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and 8 <= version.minor <= 12:
        print_success(f"Python 版本符合要求 (3.8-3.12)")
        if version.minor == 10:
            print_info("推荐版本 Python 3.10")
        return True
    else:
        print_error(f"Python 版本不符合要求，需要 3.8-3.12，当前: {version.major}.{version.minor}")
        return False

def check_pytorch():
    """检查 PyTorch 安装"""
    print_header("2. PyTorch 检查")
    
    try:
        import torch
        print_success(f"PyTorch 已安装: {torch.__version__}")
        
        # 检查推荐版本
        version_parts = torch.__version__.split('.')
        major, minor = int(version_parts[0]), int(version_parts[1])
        if major == 2 and minor == 1:
            print_success("PyTorch 版本符合推荐 (2.1.x)")
        else:
            print_warning(f"推荐 PyTorch 2.1.0，当前: {torch.__version__}")
        
        # 检查 CUDA
        if torch.cuda.is_available():
            print_success(f"CUDA 可用: {torch.version.cuda}")
            print_info(f"GPU 数量: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                print_info(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
        else:
            print_warning("CUDA 不可用，将使用 CPU（训练会很慢）")
        
        return True
    except ImportError:
        print_error("PyTorch 未安装")
        print_info("安装命令: pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu121")
        return False

def check_torchvision():
    """检查 torchvision 安装"""
    print_header("3. torchvision 检查")
    
    try:
        import torchvision
        print_success(f"torchvision 已安装: {torchvision.__version__}")
        
        # 检查版本匹配
        import torch
        torch_version = torch.__version__.split('.')[:2]
        tv_version = torchvision.__version__.split('.')[:2]
        
        if torch_version == tv_version:
            print_success("torchvision 版本与 PyTorch 匹配")
        else:
            print_warning(f"torchvision 版本可能与 PyTorch 不匹配")
            print_info(f"  PyTorch: {torch.__version__}, torchvision: {torchvision.__version__}")
        
        # 检查是否能正常导入
        try:
            from torchvision import transforms
            print_success("torchvision 模块导入正常")
        except Exception as e:
            print_error(f"torchvision 导入失败: {e}")
            return False
        
        return True
    except ImportError:
        print_error("torchvision 未安装")
        print_info("安装命令: pip install torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu121")
        return False

def check_ultralytics_import():
    """检查 ultralytics 导入"""
    print_header("4. Ultralytics 导入检查")
    
    try:
        from ultralytics import YOLO
        print_success("ultralytics 导入成功")
        return True
    except ImportError as e:
        print_error(f"ultralytics 导入失败: {e}")
        print_info("安装命令: pip install -e .")
        return False

def check_vheat_modules():
    """检查 vHeat 模块"""
    print_header("5. vHeat 模块检查")
    
    modules_to_check = [
        ('FrequencyValueEmbedding', '频率嵌入模块'),
        ('HeatConductionOperator', '热传导算子'),
        ('HeatBottleneck', '热传导瓶颈'),
        ('C2fHeat', 'C2f 热传导模块'),
        ('SPPFHeat', 'SPPF 热传导模块'),
    ]
    
    all_ok = True
    for module_name, description in modules_to_check:
        try:
            from ultralytics.nn.modules import __dict__ as modules_dict
            if module_name in modules_dict:
                print_success(f"{module_name} ({description}) 已导出")
            else:
                print_error(f"{module_name} ({description}) 未在 __init__.py 中导出")
                all_ok = False
        except Exception as e:
            print_error(f"检查 {module_name} 时出错: {e}")
            all_ok = False
    
    # 检查是否能直接导入 C2fHeat
    try:
        from ultralytics.nn.modules import C2fHeat
        print_success("C2fHeat 可以直接导入")
    except ImportError as e:
        print_error(f"C2fHeat 导入失败: {e}")
        all_ok = False
    
    return all_ok

def check_model_config():
    """检查模型配置文件"""
    print_header("6. 模型配置文件检查")
    
    config_path = Path("ultralytics/cfg/models/v12/yolov12.yaml")
    
    if config_path.exists():
        print_success(f"模型配置文件存在: {config_path}")
        
        # 检查是否包含 C2fHeat
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'C2fHeat' in content:
                    count = content.count('C2fHeat')
                    print_success(f"配置文件包含 {count} 个 C2fHeat 层")
                else:
                    print_warning("配置文件中未找到 C2fHeat")
        except Exception as e:
            print_error(f"读取配置文件失败: {e}")
            return False
        
        return True
    else:
        print_error(f"模型配置文件不存在: {config_path}")
        return False

def check_model_loading():
    """检查模型加载"""
    print_header("7. 模型加载检查")
    
    try:
        from ultralytics import YOLO
        
        # 尝试加载模型配置
        try:
            model = YOLO('ultralytics/cfg/models/v12/yolov12.yaml')
            print_success("模型配置加载成功")
            
            # 检查模型结构
            if hasattr(model, 'model'):
                print_success("模型结构已构建")
                return True
            else:
                print_warning("模型结构未构建")
                return False
        except Exception as e:
            print_error(f"模型配置加载失败: {e}")
            return False
            
    except Exception as e:
        print_error(f"模型加载检查失败: {e}")
        return False

def check_tasks_registration():
    """检查 tasks.py 中的注册"""
    print_header("8. 模块注册检查")
    
    tasks_path = Path("ultralytics/nn/tasks.py")
    
    if not tasks_path.exists():
        print_error(f"tasks.py 不存在: {tasks_path}")
        return False
    
    try:
        with open(tasks_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            checks = [
                ('from ultralytics.nn.modules import', '导入语句'),
                ('C2fHeat,', 'C2fHeat 导入'),
                ('C2fHeat', 'C2fHeat 在 parse_model 中'),
            ]
            
            all_ok = True
            for pattern, description in checks:
                if pattern in content:
                    print_success(f"{description} 已注册")
                else:
                    print_error(f"{description} 未找到")
                    all_ok = False
            
            return all_ok
    except Exception as e:
        print_error(f"检查 tasks.py 失败: {e}")
        return False

def check_file_structure():
    """检查文件结构"""
    print_header("9. 文件结构检查")
    
    required_files = [
        Path("ultralytics/__init__.py"),
        Path("ultralytics/nn/modules/block.py"),
        Path("ultralytics/nn/modules/__init__.py"),
        Path("ultralytics/nn/tasks.py"),
        Path("ultralytics/cfg/models/v12/yolov12.yaml"),
        Path("train.py"),
        Path("requirements.txt"),
        Path("pyproject.toml"),
    ]
    
    all_ok = True
    for file_path in required_files:
        if file_path.exists():
            print_success(f"{file_path} 存在")
        else:
            print_error(f"{file_path} 不存在")
            all_ok = False
    
    return all_ok

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("  YOLOv12-vHeat 环境检查")
    print("=" * 60)
    
    results = []
    
    # 执行所有检查
    results.append(("Python 版本", check_python_version()))
    results.append(("PyTorch", check_pytorch()))
    results.append(("torchvision", check_torchvision()))
    results.append(("Ultralytics 导入", check_ultralytics_import()))
    results.append(("vHeat 模块", check_vheat_modules()))
    results.append(("模型配置", check_model_config()))
    results.append(("模块注册", check_tasks_registration()))
    results.append(("文件结构", check_file_structure()))
    results.append(("模型加载", check_model_loading()))
    
    # 总结
    print_header("检查总结")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    print(f"\n总计: {passed}/{total} 项检查通过")
    
    if passed == total:
        print_success("环境配置完全正确！可以开始使用 YOLOv12-vHeat")
        return 0
    else:
        print_warning(f"有 {total - passed} 项检查未通过，请根据上述提示修复")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n检查被用户中断")
        sys.exit(1)
    except Exception as e:
        print_error(f"检查过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

