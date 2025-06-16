#!/usr/bin/env python3
"""
增强版PDF到Markdown转换器
针对比赛评估指标进行优化
"""

import re
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import numpy as np
import pymupdf as fitz
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class TextElement:
    """文本元素"""
    text: str
    bbox: Tuple[float, float, float, float]
    font_size: float
    font_name: str
    page_num: int
    is_bold: bool = False
    is_italic: bool = False


@dataclass
class TableElement:
    """表格元素"""
    rows: List[List[str]]
    bbox: Tuple[float, float, float, float]
    page_num: int


@dataclass
class FormulaElement:
    """公式元素"""
    content: str
    bbox: Tuple[float, float, float, float]
    page_num: int
    is_inline: bool = False


class EnhancedPDFToMarkdownConverter:
    """增强版PDF到Markdown转换器"""
    
    def __init__(self):
        # 公式识别模式
        self.formula_patterns = [
            r'\$[^$]+\$',  # 行内公式
            r'\$\$[^$]+\$\$',  # 块级公式
            r'\\begin\{[^}]+\}.*?\\end\{[^}]+\}',  # LaTeX环境
            r'\\[a-zA-Z]+\{[^}]*\}',  # LaTeX命令
        ]
        
        # 标题识别关键词
        self.title_keywords = [
            'abstract', 'introduction', 'conclusion', 'references',
            'method', 'result', 'discussion', 'experiment',
            'chapter', 'section', 'subsection'
        ]
    
    def convert_pdf_to_markdown(self, pdf_path: str) -> str:
        """将PDF转换为高质量Markdown"""
        try:
            doc = fitz.open(pdf_path)
            
            # 提取所有元素
            text_elements = []
            table_elements = []
            formula_elements = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # 提取文本元素
                page_texts = self._extract_text_elements(page, page_num)
                text_elements.extend(page_texts)
                
                # 提取表格
                page_tables = self._extract_tables(page, page_num)
                table_elements.extend(page_tables)
                
                # 提取公式
                page_formulas = self._extract_formulas(page, page_num)
                formula_elements.extend(page_formulas)
            
            doc.close()
            
            # 生成Markdown
            markdown = self._generate_markdown(text_elements, table_elements, formula_elements)
            
            return markdown
            
        except Exception as e:
            logger.error(f"PDF转换失败 {pdf_path}: {e}")
            return ""
    
    def _extract_text_elements(self, page, page_num: int) -> List[TextElement]:
        """提取文本元素"""
        elements = []
        
        # 获取文本块
        text_dict = page.get_text("dict")
        
        for block in text_dict["blocks"]:
            if "lines" not in block:
                continue
                
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    if not text:
                        continue
                    
                    element = TextElement(
                        text=text,
                        bbox=tuple(span["bbox"]),
                        font_size=span["size"],
                        font_name=span["font"],
                        page_num=page_num,
                        is_bold="Bold" in span["font"] or span["flags"] & 2**4,
                        is_italic="Italic" in span["font"] or span["flags"] & 2**1
                    )
                    elements.append(element)
        
        return elements
    
    def _extract_tables(self, page, page_num: int) -> List[TableElement]:
        """提取表格"""
        tables = []
        
        try:
            # 使用PyMuPDF的表格提取功能
            page_tables = page.find_tables()
            
            for table in page_tables:
                # 提取表格数据
                table_data = table.extract()
                if table_data:
                    table_element = TableElement(
                        rows=table_data,
                        bbox=table.bbox,
                        page_num=page_num
                    )
                    tables.append(table_element)
        
        except Exception as e:
            logger.warning(f"表格提取失败 page {page_num}: {e}")
        
        return tables
    
    def _extract_formulas(self, page, page_num: int) -> List[FormulaElement]:
        """提取数学公式"""
        formulas = []
        
        # 获取页面文本
        page_text = page.get_text()
        
        # 使用正则表达式查找公式
        for pattern in self.formula_patterns:
            matches = re.finditer(pattern, page_text, re.DOTALL)
            for match in matches:
                formula_text = match.group()
                
                # 判断是否为行内公式
                is_inline = formula_text.startswith('$') and not formula_text.startswith('$$')
                
                # 创建公式元素（这里简化处理，实际需要更精确的位置信息）
                formula = FormulaElement(
                    content=formula_text,
                    bbox=(0, 0, 0, 0),  # 需要更精确的位置计算
                    page_num=page_num,
                    is_inline=is_inline
                )
                formulas.append(formula)
        
        return formulas
    
    def _generate_markdown(self, text_elements: List[TextElement], 
                          table_elements: List[TableElement],
                          formula_elements: List[FormulaElement]) -> str:
        """生成Markdown内容"""
        
        # 按页面和位置排序
        all_elements = []
        
        # 添加文本元素
        for elem in text_elements:
            all_elements.append(('text', elem))
        
        # 添加表格元素
        for elem in table_elements:
            all_elements.append(('table', elem))
        
        # 添加公式元素
        for elem in formula_elements:
            all_elements.append(('formula', elem))
        
        # 排序：按页面、Y坐标、X坐标
        all_elements.sort(key=lambda x: (
            x[1].page_num,
            -x[1].bbox[1] if hasattr(x[1], 'bbox') else 0,
            x[1].bbox[0] if hasattr(x[1], 'bbox') else 0
        ))
        
        # 生成Markdown
        markdown_lines = []
        current_paragraph = []
        
        for elem_type, elem in all_elements:
            if elem_type == 'text':
                if self._is_heading(elem):
                    # 处理标题
                    if current_paragraph:
                        markdown_lines.append(' '.join(current_paragraph))
                        markdown_lines.append('')
                        current_paragraph = []
                    
                    level = self._determine_heading_level(elem)
                    markdown_lines.append(f"{'#' * level} {elem.text}")
                    markdown_lines.append('')
                    
                else:
                    # 普通文本
                    current_paragraph.append(elem.text)
                    
            elif elem_type == 'table':
                # 处理表格
                if current_paragraph:
                    markdown_lines.append(' '.join(current_paragraph))
                    markdown_lines.append('')
                    current_paragraph = []
                
                table_md = self._table_to_markdown(elem)
                if table_md:
                    markdown_lines.append(table_md)
                    markdown_lines.append('')
                    
            elif elem_type == 'formula':
                # 处理公式
                if elem.is_inline:
                    current_paragraph.append(elem.content)
                else:
                    if current_paragraph:
                        markdown_lines.append(' '.join(current_paragraph))
                        markdown_lines.append('')
                        current_paragraph = []
                    
                    # 清理公式内容
                    formula_content = self._clean_formula(elem.content)
                    markdown_lines.append(f"$${formula_content}$$")
                    markdown_lines.append('')
        
        # 处理剩余段落
        if current_paragraph:
            markdown_lines.append(' '.join(current_paragraph))
        
        return '\n'.join(markdown_lines).strip()
    
    def _is_heading(self, elem: TextElement) -> bool:
        """判断是否为标题"""
        # 基于字体大小
        if elem.font_size > 14:
            return True
        
        # 基于粗体
        if elem.is_bold and elem.font_size > 12:
            return True
        
        # 基于关键词
        text_lower = elem.text.lower()
        for keyword in self.title_keywords:
            if keyword in text_lower:
                return True
        
        # 基于格式（数字开头等）
        if re.match(r'^\d+\.?\s+[A-Z]', elem.text):
            return True
        
        return False
    
    def _determine_heading_level(self, elem: TextElement) -> int:
        """确定标题级别"""
        if elem.font_size > 20:
            return 1
        elif elem.font_size > 16:
            return 2
        elif elem.font_size > 14:
            return 3
        else:
            return 4
    
    def _table_to_markdown(self, table: TableElement) -> str:
        """将表格转换为Markdown格式"""
        if not table.rows:
            return ""
        
        markdown_lines = []
        
        # 处理表头
        if table.rows:
            header = table.rows[0]
            header_line = "| " + " | ".join(str(cell).strip() for cell in header) + " |"
            markdown_lines.append(header_line)
            
            # 分隔符
            separator = "| " + " | ".join(["---"] * len(header)) + " |"
            markdown_lines.append(separator)
            
            # 数据行
            for row in table.rows[1:]:
                if row:  # 跳过空行
                    row_line = "| " + " | ".join(str(cell).strip() for cell in row) + " |"
                    markdown_lines.append(row_line)
        
        return '\n'.join(markdown_lines)
    
    def _clean_formula(self, formula: str) -> str:
        """清理公式内容"""
        # 移除外层的$符号
        if formula.startswith('$$') and formula.endswith('$$'):
            formula = formula[2:-2]
        elif formula.startswith('$') and formula.endswith('$'):
            formula = formula[1:-1]
        
        # 清理多余空格
        formula = re.sub(r'\s+', ' ', formula.strip())
        
        return formula


def main():
    """测试函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced PDF to Markdown Converter")
    parser.add_argument("pdf_file", help="输入PDF文件")
    parser.add_argument("-o", "--output", help="输出Markdown文件")
    
    args = parser.parse_args()
    
    converter = EnhancedPDFToMarkdownConverter()
    markdown_content = converter.convert_pdf_to_markdown(args.pdf_file)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"Markdown已保存到: {args.output}")
    else:
        print(markdown_content)


if __name__ == "__main__":
    main()
