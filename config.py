#!/usr/bin/env python3
"""
配置文件 - PDF到Markdown转换器的参数配置
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class ModelConfig:
    """模型配置"""
    # DocLayout-YOLO模型配置
    model_repo: str = "wybxc/DocLayout-YOLO-DocStructBench-onnx"
    model_filename: str = "doclayout_yolo_docstructbench_imgsz1024.onnx"
    confidence_threshold: float = 0.25
    input_size: int = 1024
    
    # 类别映射
    class_names: Dict[int, str] = None
    
    def __post_init__(self):
        if self.class_names is None:
            self.class_names = {
                0: 'text',
                1: 'title', 
                2: 'list',
                3: 'table',
                4: 'figure',
                5: 'formula'
            }


@dataclass
class ProcessingConfig:
    """处理配置"""
    # 并行处理
    max_workers: int = 4
    
    # 图像处理
    image_scale_factor: float = 2.0  # PDF转图像的缩放因子
    
    # 文本处理
    min_text_length: int = 3  # 最小文本长度
    max_line_gap: float = 5.0  # 最大行间距
    
    # 表格处理
    table_confidence_threshold: float = 0.8
    min_table_rows: int = 2
    min_table_cols: int = 2


@dataclass
class MarkdownConfig:
    """Markdown输出配置"""
    # 标题配置
    max_heading_level: int = 6
    heading_size_thresholds: List[float] = None
    
    # 公式配置
    inline_formula_patterns: List[str] = None
    block_formula_patterns: List[str] = None
    
    # 表格配置
    table_alignment: str = "left"  # left, center, right
    max_table_width: int = 100
    
    # 格式化选项
    add_line_breaks: bool = True
    preserve_whitespace: bool = False
    clean_formulas: bool = True
    
    def __post_init__(self):
        if self.heading_size_thresholds is None:
            self.heading_size_thresholds = [20.0, 16.0, 14.0, 12.0, 10.0, 8.0]
        
        if self.inline_formula_patterns is None:
            self.inline_formula_patterns = [
                r'\$[^$\n]+\$',  # 标准行内公式
                r'\\([^)]+\\)',  # LaTeX行内公式
            ]
        
        if self.block_formula_patterns is None:
            self.block_formula_patterns = [
                r'\$\$[^$]+\$\$',  # 标准块级公式
                r'\\begin\{[^}]+\}.*?\\end\{[^}]+\}',  # LaTeX环境
                r'\\\\[.*?\\\\]',  # LaTeX显示公式
            ]


@dataclass
class EvaluationConfig:
    """评估配置"""
    # 文本相似度阈值
    text_similarity_threshold: float = 0.8
    
    # 标题识别关键词
    title_keywords: List[str] = None
    
    # 公式识别配置
    formula_confidence_threshold: float = 0.7
    
    # 表格评估配置
    table_structure_weight: float = 0.6
    table_content_weight: float = 0.4
    
    # 阅读顺序配置
    block_split_patterns: List[str] = None
    
    def __post_init__(self):
        if self.title_keywords is None:
            self.title_keywords = [
                'abstract', 'introduction', 'conclusion', 'references',
                'method', 'methodology', 'result', 'results', 'discussion', 
                'experiment', 'experiments', 'evaluation', 'related work',
                'background', 'literature review', 'future work',
                'chapter', 'section', 'subsection', 'appendix'
            ]
        
        if self.block_split_patterns is None:
            self.block_split_patterns = [
                r'\n\s*\n',  # 空行
                r'^\s*#+\s',  # 标题
                r'^\s*\$\$',  # 块级公式
                r'^\s*\|.*\|',  # 表格
            ]


@dataclass
class OptimizationConfig:
    """优化配置"""
    # 内存管理
    max_memory_usage: int = 2048  # MB
    clear_cache_interval: int = 100  # 处理多少个文件后清理缓存
    
    # 性能优化
    use_gpu: bool = False
    batch_size: int = 1
    prefetch_count: int = 2
    
    # 质量优化
    enable_post_processing: bool = True
    enable_spell_check: bool = False
    enable_grammar_check: bool = False


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = None):
        self.model_config = ModelConfig()
        self.processing_config = ProcessingConfig()
        self.markdown_config = MarkdownConfig()
        self.evaluation_config = EvaluationConfig()
        self.optimization_config = OptimizationConfig()
        
        if config_file and os.path.exists(config_file):
            self.load_from_file(config_file)
    
    def load_from_file(self, config_file: str):
        """从文件加载配置"""
        import json
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 更新配置
            if 'model' in config_data:
                self._update_config(self.model_config, config_data['model'])
            
            if 'processing' in config_data:
                self._update_config(self.processing_config, config_data['processing'])
            
            if 'markdown' in config_data:
                self._update_config(self.markdown_config, config_data['markdown'])
            
            if 'evaluation' in config_data:
                self._update_config(self.evaluation_config, config_data['evaluation'])
            
            if 'optimization' in config_data:
                self._update_config(self.optimization_config, config_data['optimization'])
                
        except Exception as e:
            print(f"配置文件加载失败: {e}")
    
    def save_to_file(self, config_file: str):
        """保存配置到文件"""
        import json
        
        config_data = {
            'model': self._config_to_dict(self.model_config),
            'processing': self._config_to_dict(self.processing_config),
            'markdown': self._config_to_dict(self.markdown_config),
            'evaluation': self._config_to_dict(self.evaluation_config),
            'optimization': self._config_to_dict(self.optimization_config),
        }
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"配置文件保存失败: {e}")
    
    def _update_config(self, config_obj, config_dict):
        """更新配置对象"""
        for key, value in config_dict.items():
            if hasattr(config_obj, key):
                setattr(config_obj, key, value)
    
    def _config_to_dict(self, config_obj):
        """将配置对象转换为字典"""
        result = {}
        for key, value in config_obj.__dict__.items():
            if not key.startswith('_'):
                result[key] = value
        return result
    
    def get_document_type_config(self, doc_type: str):
        """获取特定文档类型的配置"""
        configs = {
            'scientific': {
                'formula_confidence_threshold': 0.6,
                'table_confidence_threshold': 0.7,
                'heading_size_thresholds': [22.0, 18.0, 15.0, 13.0, 11.0, 9.0],
            },
            'development': {
                'code_block_detection': True,
                'preserve_indentation': True,
                'heading_size_thresholds': [18.0, 16.0, 14.0, 12.0, 10.0, 8.0],
            },
            'general': {
                'balanced_detection': True,
                'heading_size_thresholds': [20.0, 16.0, 14.0, 12.0, 10.0, 8.0],
            }
        }
        
        return configs.get(doc_type, configs['general'])
    
    def optimize_for_metric(self, metric_name: str):
        """针对特定评估指标优化配置"""
        optimizations = {
            'text_eds': {
                'clean_text_aggressive': True,
                'normalize_whitespace': True,
            },
            'text_f1': {
                'preserve_word_boundaries': True,
                'enhance_tokenization': True,
            },
            'heading_eds': {
                'improve_heading_detection': True,
                'heading_confidence_threshold': 0.8,
            },
            'heading_teds': {
                'build_accurate_tree': True,
                'preserve_hierarchy': True,
            },
            'formula_eds': {
                'enhance_formula_extraction': True,
                'clean_formula_notation': True,
            },
            'table_eds': {
                'improve_table_extraction': True,
                'preserve_table_structure': True,
            },
            'table_teds': {
                'accurate_cell_detection': True,
                'preserve_table_relationships': True,
            },
            'reading_order_ktds': {
                'optimize_sorting_algorithm': True,
                'preserve_logical_flow': True,
            }
        }
        
        return optimizations.get(metric_name, {})


# 全局配置实例
config_manager = ConfigManager()

# 便捷访问
MODEL_CONFIG = config_manager.model_config
PROCESSING_CONFIG = config_manager.processing_config
MARKDOWN_CONFIG = config_manager.markdown_config
EVALUATION_CONFIG = config_manager.evaluation_config
OPTIMIZATION_CONFIG = config_manager.optimization_config


def load_config(config_file: str = None):
    """加载配置文件"""
    global config_manager
    config_manager = ConfigManager(config_file)
    return config_manager


def get_config():
    """获取当前配置"""
    return config_manager


if __name__ == "__main__":
    # 测试配置管理器
    config = ConfigManager()
    
    # 保存默认配置
    config.save_to_file("default_config.json")
    print("默认配置已保存到 default_config.json")
    
    # 显示当前配置
    print("\n当前配置:")
    print(f"模型置信度阈值: {config.model_config.confidence_threshold}")
    print(f"最大工作线程: {config.processing_config.max_workers}")
    print(f"最大标题级别: {config.markdown_config.max_heading_level}")
    print(f"文本相似度阈值: {config.evaluation_config.text_similarity_threshold}")
    print(f"使用GPU: {config.optimization_config.use_gpu}")
