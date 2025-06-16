#!/usr/bin/env python3
"""
评估工具 - 用于优化PDF到Markdown转换质量
实现比赛中的评估指标
"""

import re
import difflib
from typing import List, Tuple, Dict
from collections import Counter
import numpy as np
from scipy.stats import kendalltau


class MarkdownEvaluator:
    """Markdown质量评估器"""
    
    def __init__(self):
        pass
    
    def evaluate_all_metrics(self, predicted: str, ground_truth: str) -> Dict[str, float]:
        """计算所有评估指标"""
        metrics = {}
        
        # 1. 文本提取指标
        metrics['text_eds'] = self.calculate_text_eds(predicted, ground_truth)
        metrics['text_f1'] = self.calculate_text_f1(predicted, ground_truth)
        
        # 2. 标题检测指标
        metrics['heading_eds'] = self.calculate_heading_eds(predicted, ground_truth)
        metrics['heading_teds'] = self.calculate_heading_teds(predicted, ground_truth)
        
        # 3. 公式转换指标
        metrics['inline_formula_eds'] = self.calculate_inline_formula_eds(predicted, ground_truth)
        metrics['block_formula_eds'] = self.calculate_block_formula_eds(predicted, ground_truth)
        
        # 4. 表格识别指标
        metrics['table_eds'] = self.calculate_table_eds(predicted, ground_truth)
        metrics['table_teds'] = self.calculate_table_teds(predicted, ground_truth)
        
        # 5. 阅读顺序检测指标
        metrics['reading_order_block_ktds'] = self.calculate_reading_order_block_ktds(predicted, ground_truth)
        metrics['reading_order_token_ktds'] = self.calculate_reading_order_token_ktds(predicted, ground_truth)
        
        # 计算平均分
        metrics['average_score'] = sum(metrics.values()) / len(metrics)
        
        return metrics
    
    def calculate_text_eds(self, predicted: str, ground_truth: str) -> float:
        """计算文本编辑距离相似度"""
        # 提取纯文本
        pred_text = self._extract_plain_text(predicted)
        gt_text = self._extract_plain_text(ground_truth)
        
        return self._edit_distance_similarity(pred_text, gt_text)
    
    def calculate_text_f1(self, predicted: str, ground_truth: str) -> float:
        """计算文本词汇F1分数"""
        # 提取词汇
        pred_words = set(self._extract_words(predicted))
        gt_words = set(self._extract_words(ground_truth))
        
        if not gt_words:
            return 1.0 if not pred_words else 0.0
        
        intersection = pred_words & gt_words
        precision = len(intersection) / len(pred_words) if pred_words else 0
        recall = len(intersection) / len(gt_words)
        
        if precision + recall == 0:
            return 0.0
        
        return 2 * precision * recall / (precision + recall)
    
    def calculate_heading_eds(self, predicted: str, ground_truth: str) -> float:
        """计算标题编辑距离相似度"""
        pred_headings = self._extract_headings(predicted)
        gt_headings = self._extract_headings(ground_truth)
        
        pred_text = ' '.join(pred_headings)
        gt_text = ' '.join(gt_headings)
        
        return self._edit_distance_similarity(pred_text, gt_text)
    
    def calculate_heading_teds(self, predicted: str, ground_truth: str) -> float:
        """计算标题树编辑距离相似度"""
        pred_tree = self._build_heading_tree(predicted)
        gt_tree = self._build_heading_tree(ground_truth)
        
        # 简化的树编辑距离计算
        return self._tree_edit_distance_similarity(pred_tree, gt_tree)
    
    def calculate_inline_formula_eds(self, predicted: str, ground_truth: str) -> float:
        """计算行内公式编辑距离相似度"""
        pred_formulas = self._extract_inline_formulas(predicted)
        gt_formulas = self._extract_inline_formulas(ground_truth)
        
        pred_text = ' '.join(pred_formulas)
        gt_text = ' '.join(gt_formulas)
        
        return self._edit_distance_similarity(pred_text, gt_text)
    
    def calculate_block_formula_eds(self, predicted: str, ground_truth: str) -> float:
        """计算块级公式编辑距离相似度"""
        pred_formulas = self._extract_block_formulas(predicted)
        gt_formulas = self._extract_block_formulas(ground_truth)
        
        pred_text = ' '.join(pred_formulas)
        gt_text = ' '.join(gt_formulas)
        
        return self._edit_distance_similarity(pred_text, gt_text)
    
    def calculate_table_eds(self, predicted: str, ground_truth: str) -> float:
        """计算表格编辑距离相似度"""
        pred_tables = self._extract_tables(predicted)
        gt_tables = self._extract_tables(ground_truth)
        
        pred_text = ' '.join(pred_tables)
        gt_text = ' '.join(gt_tables)
        
        return self._edit_distance_similarity(pred_text, gt_text)
    
    def calculate_table_teds(self, predicted: str, ground_truth: str) -> float:
        """计算表格树编辑距离相似度"""
        pred_table_structures = self._extract_table_structures(predicted)
        gt_table_structures = self._extract_table_structures(ground_truth)
        
        # 使用最大二分匹配算法
        return self._bipartite_matching_teds(pred_table_structures, gt_table_structures)
    
    def calculate_reading_order_block_ktds(self, predicted: str, ground_truth: str) -> float:
        """计算块级阅读顺序肯德尔tau距离相似性"""
        pred_blocks = self._split_into_blocks(predicted)
        gt_blocks = self._split_into_blocks(ground_truth)
        
        return self._kendall_tau_distance_similarity(pred_blocks, gt_blocks)
    
    def calculate_reading_order_token_ktds(self, predicted: str, ground_truth: str) -> float:
        """计算token级阅读顺序肯德尔tau距离相似性"""
        pred_tokens = self._extract_words(predicted)
        gt_tokens = self._extract_words(ground_truth)
        
        return self._kendall_tau_distance_similarity(pred_tokens, gt_tokens)
    
    def _extract_plain_text(self, markdown: str) -> str:
        """提取纯文本"""
        # 移除Markdown标记
        text = re.sub(r'#+\s*', '', markdown)  # 标题
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # 粗体
        text = re.sub(r'\*(.*?)\*', r'\1', text)  # 斜体
        text = re.sub(r'`(.*?)`', r'\1', text)  # 代码
        text = re.sub(r'\$\$(.*?)\$\$', '', text, flags=re.DOTALL)  # 块级公式
        text = re.sub(r'\$(.*?)\$', '', text)  # 行内公式
        text = re.sub(r'\|.*?\|', '', text)  # 表格
        text = re.sub(r'\n+', ' ', text)  # 多个换行
        
        return text.strip()
    
    def _extract_words(self, text: str) -> List[str]:
        """提取单词"""
        # 简单的单词分割
        words = re.findall(r'\b\w+\b', text.lower())
        return words
    
    def _extract_headings(self, markdown: str) -> List[str]:
        """提取标题"""
        headings = []
        for line in markdown.split('\n'):
            match = re.match(r'^(#+)\s*(.*)', line.strip())
            if match:
                headings.append(match.group(2).strip())
        return headings
    
    def _build_heading_tree(self, markdown: str) -> Dict:
        """构建标题树"""
        tree = {'level': 0, 'title': 'root', 'children': []}
        stack = [tree]
        
        for line in markdown.split('\n'):
            match = re.match(r'^(#+)\s*(.*)', line.strip())
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                
                # 找到合适的父节点
                while len(stack) > 1 and stack[-1]['level'] >= level:
                    stack.pop()
                
                node = {'level': level, 'title': title, 'children': []}
                stack[-1]['children'].append(node)
                stack.append(node)
        
        return tree
    
    def _extract_inline_formulas(self, markdown: str) -> List[str]:
        """提取行内公式"""
        return re.findall(r'\$([^$]+)\$', markdown)
    
    def _extract_block_formulas(self, markdown: str) -> List[str]:
        """提取块级公式"""
        return re.findall(r'\$\$(.*?)\$\$', markdown, re.DOTALL)
    
    def _extract_tables(self, markdown: str) -> List[str]:
        """提取表格内容"""
        tables = []
        lines = markdown.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('|') and line.endswith('|'):
                # 找到表格
                table_lines = []
                while i < len(lines) and lines[i].strip().startswith('|'):
                    table_lines.append(lines[i].strip())
                    i += 1
                
                if table_lines:
                    tables.append('\n'.join(table_lines))
            else:
                i += 1
        
        return tables
    
    def _extract_table_structures(self, markdown: str) -> List[List[List[str]]]:
        """提取表格结构"""
        structures = []
        tables = self._extract_tables(markdown)
        
        for table in tables:
            rows = []
            for line in table.split('\n'):
                if '---' not in line:  # 跳过分隔符行
                    cells = [cell.strip() for cell in line.split('|')[1:-1]]
                    if cells:
                        rows.append(cells)
            
            if rows:
                structures.append(rows)
        
        return structures
    
    def _split_into_blocks(self, markdown: str) -> List[str]:
        """将文档分割为语义块"""
        blocks = []
        current_block = []
        
        for line in markdown.split('\n'):
            line = line.strip()
            
            if not line:  # 空行分割块
                if current_block:
                    blocks.append(' '.join(current_block))
                    current_block = []
            else:
                current_block.append(line)
        
        if current_block:
            blocks.append(' '.join(current_block))
        
        return blocks
    
    def _edit_distance_similarity(self, s1: str, s2: str) -> float:
        """计算编辑距离相似度"""
        if not s1 and not s2:
            return 1.0
        
        max_len = max(len(s1), len(s2))
        if max_len == 0:
            return 1.0
        
        # 使用difflib计算相似度
        similarity = difflib.SequenceMatcher(None, s1, s2).ratio()
        return similarity
    
    def _tree_edit_distance_similarity(self, tree1: Dict, tree2: Dict) -> float:
        """计算树编辑距离相似度（简化版）"""
        # 简化实现：比较树的结构和内容
        def tree_to_string(tree):
            if not tree.get('children'):
                return tree.get('title', '')
            
            children_str = ''.join(tree_to_string(child) for child in tree['children'])
            return f"{tree.get('title', '')}({children_str})"
        
        s1 = tree_to_string(tree1)
        s2 = tree_to_string(tree2)
        
        return self._edit_distance_similarity(s1, s2)
    
    def _bipartite_matching_teds(self, structures1: List, structures2: List) -> float:
        """使用最大二分匹配计算表格TEDS（简化版）"""
        if not structures1 and not structures2:
            return 1.0
        
        if not structures1 or not structures2:
            return 0.0
        
        # 简化实现：计算每对表格的相似度，取最大匹配
        similarities = []
        
        for s1 in structures1:
            best_sim = 0.0
            for s2 in structures2:
                sim = self._table_structure_similarity(s1, s2)
                best_sim = max(best_sim, sim)
            similarities.append(best_sim)
        
        return sum(similarities) / len(similarities) if similarities else 0.0
    
    def _table_structure_similarity(self, table1: List[List[str]], table2: List[List[str]]) -> float:
        """计算表格结构相似度"""
        # 简化实现：比较行数、列数和内容
        if len(table1) != len(table2):
            return 0.0
        
        total_cells = 0
        matching_cells = 0
        
        for row1, row2 in zip(table1, table2):
            if len(row1) != len(row2):
                return 0.0
            
            for cell1, cell2 in zip(row1, row2):
                total_cells += 1
                if cell1.strip() == cell2.strip():
                    matching_cells += 1
        
        return matching_cells / total_cells if total_cells > 0 else 1.0
    
    def _kendall_tau_distance_similarity(self, list1: List[str], list2: List[str]) -> float:
        """计算肯德尔tau距离相似性"""
        if not list1 and not list2:
            return 1.0
        
        # 找到共同元素
        common_elements = set(list1) & set(list2)
        if len(common_elements) < 2:
            return 0.0
        
        # 构建排序
        order1 = {elem: i for i, elem in enumerate(list1) if elem in common_elements}
        order2 = {elem: i for i, elem in enumerate(list2) if elem in common_elements}
        
        # 计算肯德尔tau相关系数
        common_list = list(common_elements)
        ranks1 = [order1[elem] for elem in common_list]
        ranks2 = [order2[elem] for elem in common_list]
        
        try:
            tau, _ = kendalltau(ranks1, ranks2)
            # 转换为相似度（tau范围是-1到1）
            similarity = (tau + 1) / 2
            return similarity
        except:
            return 0.0


def main():
    """测试评估工具"""
    evaluator = MarkdownEvaluator()
    
    # 示例文档
    predicted = """
# Introduction
This is a sample document with $x = y + z$ inline formula.

## Method
The method involves:
$$
E = mc^2
$$

| Name | Age | City |
|------|-----|------|
| John | 25  | NYC  |
| Jane | 30  | LA   |
"""
    
    ground_truth = """
# Introduction  
This is a sample document with $x = y + z$ inline formula.

## Methodology
The method involves:
$$
E = mc^2
$$

| Name | Age | Location |
|------|-----|----------|
| John | 25  | New York |
| Jane | 30  | Los Angeles |
"""
    
    metrics = evaluator.evaluate_all_metrics(predicted, ground_truth)
    
    print("评估结果:")
    for metric, score in metrics.items():
        print(f"{metric}: {score:.4f}")


if __name__ == "__main__":
    main()
