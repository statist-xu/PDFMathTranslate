#!/usr/bin/env python3
"""
PDF to Markdown Contest Solution
基于PDFMathTranslate项目，专门用于PDF到Markdown转换比赛
"""

import argparse
import csv
import io
import logging
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import concurrent.futures
from dataclasses import dataclass

import cv2
import numpy as np
from pdfminer.converter import PDFConverter
from pdfminer.layout import LTChar, LTFigure, LTLine, LTPage, LTTextBox, LTTextLine
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.utils import apply_matrix_pt
import pymupdf as fitz

# 文档布局识别相关
try:
    import onnx
    import onnxruntime
    from huggingface_hub import hf_hub_download
except ImportError as e:
    print(f"请安装必要的依赖: {e}")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class LayoutElement:
    """文档布局元素"""
    type: str  # text, title, formula, table, figure
    bbox: Tuple[float, float, float, float]  # x0, y0, x1, y1
    content: str
    confidence: float
    page_num: int
    reading_order: int = 0


class DocLayoutModel:
    """文档布局识别模型"""
    
    def __init__(self, model_path: str = None):
        if model_path is None:
            # 下载预训练模型
            model_path = self._download_model()
        
        self.model_path = model_path
        self.model = onnxruntime.InferenceSession(model_path)
        
        # 模型类别映射
        self.class_names = {
            0: 'text',
            1: 'title', 
            2: 'list',
            3: 'table',
            4: 'figure',
            5: 'formula'
        }
    
    def _download_model(self) -> str:
        """下载DocLayout-YOLO模型"""
        try:
            model_path = hf_hub_download(
                repo_id="wybxc/DocLayout-YOLO-DocStructBench-onnx",
                filename="doclayout_yolo_docstructbench_imgsz1024.onnx"
            )
            return model_path
        except Exception as e:
            logger.error(f"模型下载失败: {e}")
            raise
    
    def predict(self, image: np.ndarray, conf_threshold: float = 0.25) -> List[Dict]:
        """预测文档布局"""
        # 图像预处理
        orig_h, orig_w = image.shape[:2]
        processed_img = self._preprocess_image(image)
        
        # 模型推理
        inputs = {self.model.get_inputs()[0].name: processed_img}
        outputs = self.model.run(None, inputs)
        
        # 后处理
        detections = self._postprocess(outputs[0], orig_h, orig_w, conf_threshold)
        
        return detections
    
    def _preprocess_image(self, image: np.ndarray, target_size: int = 1024) -> np.ndarray:
        """图像预处理"""
        # 调整大小并保持宽高比
        h, w = image.shape[:2]
        scale = target_size / max(h, w)
        new_h, new_w = int(h * scale), int(w * scale)
        
        resized = cv2.resize(image, (new_w, new_h))
        
        # 填充到目标尺寸
        padded = np.full((target_size, target_size, 3), 114, dtype=np.uint8)
        padded[:new_h, :new_w] = resized
        
        # 转换为模型输入格式
        padded = padded.transpose(2, 0, 1)  # HWC -> CHW
        padded = padded[np.newaxis, :].astype(np.float32) / 255.0
        
        return padded
    
    def _postprocess(self, output: np.ndarray, orig_h: int, orig_w: int, 
                    conf_threshold: float) -> List[Dict]:
        """后处理检测结果"""
        detections = []
        
        # 过滤低置信度检测
        valid_detections = output[output[:, 4] > conf_threshold]
        
        for detection in valid_detections:
            x1, y1, x2, y2, conf, cls = detection[:6]
            
            # 坐标缩放回原图尺寸
            scale = max(orig_h, orig_w) / 1024
            x1, y1, x2, y2 = x1 * scale, y1 * scale, x2 * scale, y2 * scale
            
            detections.append({
                'bbox': (x1, y1, x2, y2),
                'confidence': conf,
                'class': int(cls),
                'class_name': self.class_names.get(int(cls), 'unknown')
            })
        
        return detections


class PDFToMarkdownConverter:
    """PDF到Markdown转换器"""
    
    def __init__(self):
        self.layout_model = DocLayoutModel()
    
    def convert_pdf_to_markdown(self, pdf_path: str) -> str:
        """将PDF转换为Markdown"""
        try:
            # 打开PDF文档
            doc = fitz.open(pdf_path)
            
            all_elements = []
            
            # 逐页处理
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # 获取页面图像用于布局识别
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2倍缩放提高精度
                img_data = pix.tobytes("png")
                img_array = np.frombuffer(img_data, dtype=np.uint8)
                image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                
                # 布局识别
                layout_results = self.layout_model.predict(image)
                
                # 提取文本内容
                page_elements = self._extract_page_elements(page, layout_results, page_num)
                all_elements.extend(page_elements)
            
            doc.close()
            
            # 按阅读顺序排序
            all_elements = self._sort_reading_order(all_elements)
            
            # 转换为Markdown
            markdown_content = self._elements_to_markdown(all_elements)
            
            return markdown_content
            
        except Exception as e:
            logger.error(f"PDF转换失败 {pdf_path}: {e}")
            return ""
    
    def _extract_page_elements(self, page, layout_results: List[Dict], 
                              page_num: int) -> List[LayoutElement]:
        """从页面提取结构化元素"""
        elements = []
        
        for detection in layout_results:
            bbox = detection['bbox']
            class_name = detection['class_name']
            confidence = detection['confidence']
            
            # 提取该区域的文本
            rect = fitz.Rect(bbox)
            text_content = page.get_text("text", clip=rect).strip()
            
            if text_content:
                element = LayoutElement(
                    type=class_name,
                    bbox=bbox,
                    content=text_content,
                    confidence=confidence,
                    page_num=page_num
                )
                elements.append(element)
        
        return elements
    
    def _sort_reading_order(self, elements: List[LayoutElement]) -> List[LayoutElement]:
        """按阅读顺序排序元素"""
        # 按页面、Y坐标、X坐标排序
        elements.sort(key=lambda x: (x.page_num, -x.bbox[1], x.bbox[0]))
        
        # 分配阅读顺序
        for i, element in enumerate(elements):
            element.reading_order = i
        
        return elements
    
    def _elements_to_markdown(self, elements: List[LayoutElement]) -> str:
        """将结构化元素转换为Markdown"""
        markdown_lines = []
        
        for element in elements:
            content = element.content.strip()
            if not content:
                continue
            
            if element.type == 'title':
                # 根据字体大小或位置判断标题级别
                level = self._determine_heading_level(element)
                markdown_lines.append(f"{'#' * level} {content}")
                markdown_lines.append("")
                
            elif element.type == 'formula':
                # 处理数学公式
                if self._is_inline_formula(element):
                    # 行内公式
                    formula = self._clean_formula(content)
                    markdown_lines.append(f"${formula}$")
                else:
                    # 块级公式
                    formula = self._clean_formula(content)
                    markdown_lines.append("$$")
                    markdown_lines.append(formula)
                    markdown_lines.append("$$")
                    markdown_lines.append("")
                    
            elif element.type == 'table':
                # 处理表格
                table_md = self._convert_table_to_markdown(content)
                if table_md:
                    markdown_lines.append(table_md)
                    markdown_lines.append("")
                    
            elif element.type == 'text':
                # 普通文本
                markdown_lines.append(content)
                markdown_lines.append("")
        
        return "\n".join(markdown_lines).strip()
    
    def _determine_heading_level(self, element: LayoutElement) -> int:
        """确定标题级别"""
        # 简单的启发式规则，可以根据需要改进
        bbox_height = element.bbox[3] - element.bbox[1]
        
        if bbox_height > 30:
            return 1
        elif bbox_height > 25:
            return 2
        elif bbox_height > 20:
            return 3
        else:
            return 4
    
    def _is_inline_formula(self, element: LayoutElement) -> bool:
        """判断是否为行内公式"""
        # 简单判断：较小的公式认为是行内公式
        bbox_height = element.bbox[3] - element.bbox[1]
        return bbox_height < 25
    
    def _clean_formula(self, formula_text: str) -> str:
        """清理公式文本"""
        # 移除多余的空格和换行
        cleaned = re.sub(r'\s+', ' ', formula_text.strip())
        return cleaned
    
    def _convert_table_to_markdown(self, table_text: str) -> str:
        """将表格文本转换为Markdown表格格式"""
        lines = table_text.strip().split('\n')
        if len(lines) < 2:
            return ""
        
        # 简单的表格转换逻辑
        markdown_table = []
        
        for i, line in enumerate(lines):
            # 分割单元格（这里使用简单的空格分割，实际可能需要更复杂的逻辑）
            cells = [cell.strip() for cell in re.split(r'\s{2,}', line.strip())]
            if cells:
                markdown_table.append("| " + " | ".join(cells) + " |")
                
                # 添加表头分隔符
                if i == 0:
                    separator = "| " + " | ".join(["---"] * len(cells)) + " |"
                    markdown_table.append(separator)
        
        return "\n".join(markdown_table)


def process_single_pdf(pdf_path: str, converter: PDFToMarkdownConverter) -> Tuple[str, str]:
    """处理单个PDF文件"""
    file_id = Path(pdf_path).stem
    markdown_content = converter.convert_pdf_to_markdown(pdf_path)
    return file_id, markdown_content


def main():
    parser = argparse.ArgumentParser(description="PDF to Markdown Contest Solution")
    parser.add_argument("input_dir", help="输入PDF文件目录")
    parser.add_argument("-o", "--output", default="result.csv", help="输出CSV文件路径")
    parser.add_argument("-t", "--threads", type=int, default=4, help="并行处理线程数")
    
    args = parser.parse_args()
    
    # 检查输入目录
    input_path = Path(args.input_dir)
    if not input_path.exists():
        logger.error(f"输入目录不存在: {input_path}")
        sys.exit(1)
    
    # 获取所有PDF文件
    pdf_files = list(input_path.glob("*.pdf"))
    if not pdf_files:
        logger.error("未找到PDF文件")
        sys.exit(1)
    
    logger.info(f"找到 {len(pdf_files)} 个PDF文件")
    
    # 创建转换器
    converter = PDFToMarkdownConverter()
    
    # 并行处理PDF文件
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
        future_to_file = {
            executor.submit(process_single_pdf, str(pdf_file), converter): pdf_file
            for pdf_file in pdf_files
        }
        
        for future in concurrent.futures.as_completed(future_to_file):
            pdf_file = future_to_file[future]
            try:
                file_id, markdown_content = future.result()
                results.append([file_id, markdown_content])
                logger.info(f"完成处理: {pdf_file.name}")
            except Exception as e:
                logger.error(f"处理失败 {pdf_file.name}: {e}")
                results.append([pdf_file.stem, ""])  # 失败时添加空内容
    
    # 保存结果到CSV
    with open(args.output, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["file_id", "answer"])  # 写入表头
        writer.writerows(results)
    
    logger.info(f"结果已保存到: {args.output}")


if __name__ == "__main__":
    main()
