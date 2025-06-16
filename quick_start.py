#!/usr/bin/env python3
"""
快速开始脚本 - PDF到Markdown转换比赛解决方案
"""

import os
import sys
import argparse
import logging
from pathlib import Path
import subprocess

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_dependencies():
    """检查依赖是否安装"""
    required_packages = [
        'pymupdf', 'numpy', 'opencv-python', 'onnx', 'onnxruntime', 
        'huggingface_hub', 'pandas', 'tqdm'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"缺少以下依赖包: {', '.join(missing_packages)}")
        logger.info("请运行: pip install -r requirements.txt")
        return False
    
    logger.info("✅ 所有依赖包已安装")
    return True


def download_model():
    """下载预训练模型"""
    try:
        from huggingface_hub import hf_hub_download
        
        logger.info("正在下载DocLayout-YOLO模型...")
        model_path = hf_hub_download(
            repo_id="wybxc/DocLayout-YOLO-DocStructBench-onnx",
            filename="doclayout_yolo_docstructbench_imgsz1024.onnx"
        )
        logger.info(f"✅ 模型下载完成: {model_path}")
        return model_path
    
    except Exception as e:
        logger.error(f"❌ 模型下载失败: {e}")
        return None


def create_sample_data():
    """创建示例数据"""
    sample_dir = Path("sample_data")
    sample_dir.mkdir(exist_ok=True)
    
    # 创建示例配置文件
    config_content = """
{
  "model": {
    "confidence_threshold": 0.25,
    "input_size": 1024
  },
  "processing": {
    "max_workers": 4,
    "image_scale_factor": 2.0
  },
  "markdown": {
    "max_heading_level": 6,
    "add_line_breaks": true,
    "clean_formulas": true
  },
  "evaluation": {
    "text_similarity_threshold": 0.8
  },
  "optimization": {
    "use_gpu": false,
    "batch_size": 1
  }
}
"""
    
    config_file = sample_dir / "config.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    logger.info(f"✅ 示例配置文件已创建: {config_file}")
    
    # 创建示例Markdown文件用于测试评估
    sample_markdown = """
# 示例文档

## 介绍
这是一个示例文档，包含各种Markdown元素。

### 数学公式
行内公式：$E = mc^2$

块级公式：
$$
\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}
$$

### 表格
| 姓名 | 年龄 | 城市 |
|------|------|------|
| 张三 | 25   | 北京 |
| 李四 | 30   | 上海 |

### 列表
1. 第一项
2. 第二项
   - 子项目A
   - 子项目B

## 结论
这是文档的结论部分。
"""
    
    sample_md_file = sample_dir / "sample.md"
    with open(sample_md_file, 'w', encoding='utf-8') as f:
        f.write(sample_markdown)
    
    logger.info(f"✅ 示例Markdown文件已创建: {sample_md_file}")
    
    return sample_dir


def run_demo():
    """运行演示"""
    logger.info("🚀 运行PDF到Markdown转换演示...")
    
    try:
        # 导入模块
        from evaluation_utils import MarkdownEvaluator
        from config import ConfigManager
        
        # 创建评估器
        evaluator = MarkdownEvaluator()
        
        # 示例文档
        predicted = """
# Introduction
This document contains $x = y + z$ formula.

## Method
$$
E = mc^2
$$

| Name | Age |
|------|-----|
| John | 25  |
"""
        
        ground_truth = """
# Introduction  
This document contains $x = y + z$ formula.

## Methodology
$$
E = mc^2
$$

| Name | Age |
|------|-----|
| John | 25  |
"""
        
        # 计算评估指标
        logger.info("计算评估指标...")
        metrics = evaluator.evaluate_all_metrics(predicted, ground_truth)
        
        # 显示结果
        logger.info("📊 评估结果:")
        for metric, score in metrics.items():
            logger.info(f"  {metric}: {score:.4f}")
        
        # 测试配置管理器
        logger.info("测试配置管理器...")
        config = ConfigManager()
        logger.info(f"  模型置信度阈值: {config.model_config.confidence_threshold}")
        logger.info(f"  最大工作线程: {config.processing_config.max_workers}")
        
        logger.info("✅ 演示完成!")
        
    except Exception as e:
        logger.error(f"❌ 演示失败: {e}")


def install_package():
    """安装包"""
    logger.info("安装PDF到Markdown转换包...")
    
    try:
        # 安装依赖
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True)
        
        # 安装当前包
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], 
                      check=True)
        
        logger.info("✅ 包安装完成")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ 包安装失败: {e}")


def run_tests():
    """运行测试"""
    logger.info("运行系统测试...")
    
    try:
        # 运行测试脚本
        subprocess.run([sys.executable, "test_system.py"], check=True)
        logger.info("✅ 测试完成")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ 测试失败: {e}")
    except FileNotFoundError:
        logger.error("❌ 测试脚本未找到")


def show_usage():
    """显示使用说明"""
    usage_text = """
🎯 PDF到Markdown转换比赛解决方案 - 快速开始指南

📋 基本使用:
  1. 检查依赖: python quick_start.py --check-deps
  2. 下载模型: python quick_start.py --download-model  
  3. 运行演示: python quick_start.py --demo
  4. 运行测试: python quick_start.py --test

🔧 安装和配置:
  - 安装包: python quick_start.py --install
  - 创建示例: python quick_start.py --create-sample

📁 处理PDF文件:
  # 单个文件转换
  python enhanced_converter.py input.pdf -o output.md
  
  # 批量处理（比赛格式）
  python pdf_to_markdown_contest.py /path/to/pdfs/ -o result.csv -t 8

📊 评估质量:
  python evaluation_utils.py

⚙️ 配置文件:
  使用 config.json 自定义参数设置

📚 更多信息请查看 README_contest.md
"""
    print(usage_text)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="PDF到Markdown转换比赛解决方案 - 快速开始")
    
    parser.add_argument("--check-deps", action="store_true", help="检查依赖")
    parser.add_argument("--download-model", action="store_true", help="下载预训练模型")
    parser.add_argument("--create-sample", action="store_true", help="创建示例数据")
    parser.add_argument("--demo", action="store_true", help="运行演示")
    parser.add_argument("--install", action="store_true", help="安装包")
    parser.add_argument("--test", action="store_true", help="运行测试")
    parser.add_argument("--usage", action="store_true", help="显示使用说明")
    
    args = parser.parse_args()
    
    if args.check_deps:
        check_dependencies()
    
    elif args.download_model:
        download_model()
    
    elif args.create_sample:
        create_sample_data()
    
    elif args.demo:
        if check_dependencies():
            run_demo()
    
    elif args.install:
        install_package()
    
    elif args.test:
        if check_dependencies():
            run_tests()
    
    elif args.usage:
        show_usage()
    
    else:
        # 默认显示使用说明
        show_usage()
        
        # 自动检查环境
        logger.info("\n🔍 自动检查环境...")
        if check_dependencies():
            logger.info("✅ 环境检查通过，可以开始使用!")
            logger.info("💡 运行 'python quick_start.py --demo' 查看演示")
        else:
            logger.info("❌ 环境检查失败，请先安装依赖")
            logger.info("💡 运行 'python quick_start.py --install' 自动安装")


if __name__ == "__main__":
    main()
