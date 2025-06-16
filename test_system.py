#!/usr/bin/env python3
"""
系统测试脚本 - 验证PDF到Markdown转换系统的功能
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_converter import EnhancedPDFToMarkdownConverter
from evaluation_utils import MarkdownEvaluator
from config import ConfigManager


class TestPDFToMarkdownSystem(unittest.TestCase):
    """PDF到Markdown转换系统测试"""
    
    def setUp(self):
        """测试初始化"""
        self.converter = EnhancedPDFToMarkdownConverter()
        self.evaluator = MarkdownEvaluator()
        self.config = ConfigManager()
        
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """测试清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_config_manager(self):
        """测试配置管理器"""
        # 测试默认配置
        self.assertIsNotNone(self.config.model_config)
        self.assertIsNotNone(self.config.processing_config)
        self.assertIsNotNone(self.config.markdown_config)
        
        # 测试配置保存和加载
        config_file = os.path.join(self.temp_dir, "test_config.json")
        self.config.save_to_file(config_file)
        self.assertTrue(os.path.exists(config_file))
        
        # 加载配置
        new_config = ConfigManager(config_file)
        self.assertEqual(
            new_config.model_config.confidence_threshold,
            self.config.model_config.confidence_threshold
        )
    
    def test_markdown_evaluator(self):
        """测试Markdown评估器"""
        # 测试文本
        predicted = """
# Introduction
This is a test document with $x = y + z$ formula.

## Method
The equation is:
$$
E = mc^2
$$

| Name | Age |
|------|-----|
| John | 25  |
"""
        
        ground_truth = """
# Introduction
This is a test document with $x = y + z$ formula.

## Methodology  
The equation is:
$$
E = mc^2
$$

| Name | Age |
|------|-----|
| John | 25  |
"""
        
        # 计算评估指标
        metrics = self.evaluator.evaluate_all_metrics(predicted, ground_truth)
        
        # 验证指标存在
        expected_metrics = [
            'text_eds', 'text_f1', 'heading_eds', 'heading_teds',
            'inline_formula_eds', 'block_formula_eds', 'table_eds', 'table_teds',
            'reading_order_block_ktds', 'reading_order_token_ktds', 'average_score'
        ]
        
        for metric in expected_metrics:
            self.assertIn(metric, metrics)
            self.assertIsInstance(metrics[metric], float)
            self.assertGreaterEqual(metrics[metric], 0.0)
            self.assertLessEqual(metrics[metric], 1.0)
    
    def test_text_extraction(self):
        """测试文本提取功能"""
        markdown = """
# Title
This is **bold** and *italic* text.
Some `code` and normal text.
"""
        
        plain_text = self.evaluator._extract_plain_text(markdown)
        self.assertIn("Title", plain_text)
        self.assertIn("bold", plain_text)
        self.assertIn("italic", plain_text)
        self.assertNotIn("#", plain_text)
        self.assertNotIn("**", plain_text)
        self.assertNotIn("*", plain_text)
    
    def test_heading_extraction(self):
        """测试标题提取功能"""
        markdown = """
# Main Title
## Subtitle
### Sub-subtitle
Normal text
#### Another heading
"""
        
        headings = self.evaluator._extract_headings(markdown)
        expected_headings = ["Main Title", "Subtitle", "Sub-subtitle", "Another heading"]
        
        self.assertEqual(len(headings), 4)
        for expected in expected_headings:
            self.assertIn(expected, headings)
    
    def test_formula_extraction(self):
        """测试公式提取功能"""
        markdown = """
Inline formula $x = y + z$ in text.
Block formula:
$$
E = mc^2
$$
Another inline $a + b = c$ formula.
"""
        
        inline_formulas = self.evaluator._extract_inline_formulas(markdown)
        block_formulas = self.evaluator._extract_block_formulas(markdown)
        
        self.assertEqual(len(inline_formulas), 2)
        self.assertIn("x = y + z", inline_formulas)
        self.assertIn("a + b = c", inline_formulas)
        
        self.assertEqual(len(block_formulas), 1)
        self.assertIn("E = mc^2", block_formulas[0])
    
    def test_table_extraction(self):
        """测试表格提取功能"""
        markdown = """
Some text before table.

| Name | Age | City |
|------|-----|------|
| John | 25  | NYC  |
| Jane | 30  | LA   |

Text after table.

| A | B |
|---|---|
| 1 | 2 |
"""
        
        tables = self.evaluator._extract_tables(markdown)
        self.assertEqual(len(tables), 2)
        
        # 检查第一个表格
        self.assertIn("Name", tables[0])
        self.assertIn("John", tables[0])
        self.assertIn("Jane", tables[0])
        
        # 检查第二个表格
        self.assertIn("A", tables[1])
        self.assertIn("B", tables[1])
    
    def test_reading_order_blocks(self):
        """测试阅读顺序块分割"""
        markdown = """
# Title

First paragraph.

Second paragraph.

## Subtitle

Third paragraph.
"""
        
        blocks = self.evaluator._split_into_blocks(markdown)
        
        self.assertGreater(len(blocks), 0)
        self.assertIn("Title", blocks[0])
        
        # 检查是否包含所有主要内容
        all_text = " ".join(blocks)
        self.assertIn("First paragraph", all_text)
        self.assertIn("Second paragraph", all_text)
        self.assertIn("Third paragraph", all_text)
    
    def test_similarity_calculations(self):
        """测试相似度计算"""
        # 测试完全相同
        similarity = self.evaluator._edit_distance_similarity("hello", "hello")
        self.assertEqual(similarity, 1.0)
        
        # 测试完全不同
        similarity = self.evaluator._edit_distance_similarity("hello", "world")
        self.assertLess(similarity, 1.0)
        self.assertGreater(similarity, 0.0)
        
        # 测试空字符串
        similarity = self.evaluator._edit_distance_similarity("", "")
        self.assertEqual(similarity, 1.0)
    
    def test_document_type_optimization(self):
        """测试文档类型优化"""
        # 测试科技文献配置
        sci_config = self.config.get_document_type_config('scientific')
        self.assertIn('formula_confidence_threshold', sci_config)
        
        # 测试开发文档配置
        dev_config = self.config.get_document_type_config('development')
        self.assertIn('code_block_detection', dev_config)
        
        # 测试通用文档配置
        gen_config = self.config.get_document_type_config('general')
        self.assertIn('balanced_detection', gen_config)
    
    def test_metric_optimization(self):
        """测试评估指标优化"""
        # 测试文本EDS优化
        text_opt = self.config.optimize_for_metric('text_eds')
        self.assertIsInstance(text_opt, dict)
        
        # 测试公式EDS优化
        formula_opt = self.config.optimize_for_metric('formula_eds')
        self.assertIsInstance(formula_opt, dict)
    
    @patch('pymupdf.open')
    def test_converter_error_handling(self, mock_open):
        """测试转换器错误处理"""
        # 模拟PDF打开失败
        mock_open.side_effect = Exception("File not found")
        
        result = self.converter.convert_pdf_to_markdown("nonexistent.pdf")
        self.assertEqual(result, "")
    
    def test_table_structure_similarity(self):
        """测试表格结构相似度"""
        table1 = [["A", "B"], ["1", "2"], ["3", "4"]]
        table2 = [["A", "B"], ["1", "2"], ["3", "4"]]
        table3 = [["X", "Y"], ["5", "6"]]
        
        # 相同表格
        similarity = self.evaluator._table_structure_similarity(table1, table2)
        self.assertEqual(similarity, 1.0)
        
        # 不同表格
        similarity = self.evaluator._table_structure_similarity(table1, table3)
        self.assertLess(similarity, 1.0)
    
    def test_heading_tree_building(self):
        """测试标题树构建"""
        markdown = """
# Chapter 1
## Section 1.1
### Subsection 1.1.1
## Section 1.2
# Chapter 2
"""
        
        tree = self.evaluator._build_heading_tree(markdown)
        
        # 检查树结构
        self.assertEqual(tree['title'], 'root')
        self.assertGreater(len(tree['children']), 0)
        
        # 检查第一个章节
        chapter1 = tree['children'][0]
        self.assertEqual(chapter1['level'], 1)
        self.assertIn('Chapter 1', chapter1['title'])
        self.assertGreater(len(chapter1['children']), 0)


def create_sample_pdf():
    """创建示例PDF文件用于测试"""
    try:
        import pymupdf as fitz
        
        # 创建简单的PDF文档
        doc = fitz.open()
        page = doc.new_page()
        
        # 添加文本
        text = """
        Test Document
        
        This is a sample PDF document for testing.
        
        It contains multiple paragraphs and some basic formatting.
        """
        
        page.insert_text((50, 50), text)
        
        # 保存到临时文件
        temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        doc.save(temp_file.name)
        doc.close()
        
        return temp_file.name
    
    except ImportError:
        print("PyMuPDF not available, skipping PDF creation")
        return None


def run_integration_test():
    """运行集成测试"""
    print("运行PDF到Markdown转换系统集成测试...")
    
    # 创建示例PDF
    pdf_file = create_sample_pdf()
    if pdf_file:
        try:
            # 测试转换
            converter = EnhancedPDFToMarkdownConverter()
            markdown_result = converter.convert_pdf_to_markdown(pdf_file)
            
            print(f"转换结果长度: {len(markdown_result)} 字符")
            if markdown_result:
                print("✅ PDF转换成功")
            else:
                print("❌ PDF转换失败")
            
            # 清理临时文件
            os.unlink(pdf_file)
            
        except Exception as e:
            print(f"❌ 集成测试失败: {e}")
    else:
        print("⚠️  跳过PDF转换测试（缺少依赖）")


if __name__ == "__main__":
    # 运行单元测试
    print("运行单元测试...")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    print("\n" + "="*50)
    
    # 运行集成测试
    run_integration_test()
