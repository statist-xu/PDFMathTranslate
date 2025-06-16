# PDF到Markdown转换比赛解决方案

基于PDFMathTranslate项目开发的专业PDF到Markdown转换工具，专门针对文档结构化解析比赛进行优化。

## 项目特点

- 🎯 **专门优化**: 针对比赛的10个评估指标进行专门优化
- 📊 **高精度解析**: 支持文本、标题、公式、表格的精确识别
- 🔄 **阅读顺序**: 智能保持文档的逻辑阅读顺序
- ⚡ **高效处理**: 支持多线程并行处理大量PDF文件
- 📝 **标准输出**: 严格遵循标准Markdown格式规范

## 评估指标覆盖

### 1. 文本提取 (Text Extraction)
- ✅ 编辑距离相似度 (EDS)
- ✅ 词汇表F1分数

### 2. 标题检测 (Heading Detection)  
- ✅ 标题拼接EDS
- ✅ 目录树TEDS (Tree Edit Distance Similarity)

### 3. 公式转换 (Formula Conversion)
- ✅ 行内公式EDS (`$...$`)
- ✅ 独立公式EDS (`$$...$$`)

### 4. 表格识别 (Table Recognition)
- ✅ 表格内容EDS
- ✅ 表格结构TEDS

### 5. 阅读顺序检测 (Reading Order Detection)
- ✅ 语义块KTDS (Kendall Tau Distance Similarity)
- ✅ Token级KTDS

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 基础转换

```bash
# 转换单个PDF文件
python enhanced_converter.py input.pdf -o output.md

# 批量处理PDF目录
python pdf_to_markdown_contest.py /path/to/pdf_directory -o result.csv
```

### 2. 比赛提交格式

```bash
# 处理测试集A
python pdf_to_markdown_contest.py ./test_set_A/ -o result_A.csv -t 8

# 处理测试集B  
python pdf_to_markdown_contest.py ./test_set_B/ -o result_B.csv -t 8
```

### 3. 质量评估

```bash
# 评估转换质量
python evaluation_utils.py
```

## 输出格式说明

### CSV结果文件格式
```csv
file_id,answer
document1,"# Title\n\nContent with $formula$ and tables..."
document2,"# Another Document\n\n$$E=mc^2$$\n\n| A | B |\n|---|---|\n| 1 | 2 |"
```

### Markdown格式要求

1. **标题**: 使用标准`#`语法
   ```markdown
   # 一级标题
   ## 二级标题
   ### 三级标题
   ```

2. **行内公式**: 使用单个`$`包围
   ```markdown
   这是行内公式 $x = y + z$ 的示例。
   ```

3. **块级公式**: 使用双`$$`包围
   ```markdown
   $$
   E = mc^2
   $$
   ```

4. **表格**: 使用标准Markdown表格格式
   ```markdown
   | 列1 | 列2 | 列3 |
   |-----|-----|-----|
   | 数据1 | 数据2 | 数据3 |
   ```

## 核心算法

### 1. 文档布局识别
- 使用DocLayout-YOLO模型进行版面分析
- 识别文本、标题、表格、公式、图片等元素
- 基于ONNX Runtime实现高效推理

### 2. 阅读顺序优化
- 多层次排序算法：页面 → Y坐标 → X坐标
- 语义块智能分割
- 保持逻辑连贯性

### 3. 公式处理
- 正则表达式识别LaTeX公式
- 区分行内和块级公式
- 保持数学符号完整性

### 4. 表格重建
- PyMuPDF表格提取
- 智能单元格合并
- 标准Markdown表格格式化

## 性能优化

### 1. 并行处理
```python
# 使用多线程处理大量文件
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
    futures = [executor.submit(process_pdf, pdf_file) for pdf_file in pdf_files]
```

### 2. 内存管理
- 逐页处理避免内存溢出
- 及时释放PDF文档资源
- 优化图像处理内存使用

### 3. 模型优化
- ONNX模型量化
- 批处理推理
- GPU加速支持

## 项目结构

```
├── pdf_to_markdown_contest.py    # 主程序入口
├── enhanced_converter.py         # 增强转换器
├── evaluation_utils.py           # 评估工具
├── requirements.txt              # 依赖列表
├── README_contest.md            # 项目说明
└── models/                      # 模型文件目录
    └── doclayout_yolo.onnx     # 布局识别模型
```

## 调优建议

### 1. 针对不同文档类型调优

**科技文献**:
- 增强公式识别精度
- 优化双栏布局处理
- 改进参考文献格式化

**开发文档**:
- 强化代码块识别
- 优化层级结构解析
- 改进链接和引用处理

**通用文档**:
- 平衡各类元素识别
- 优化混合内容处理
- 提升鲁棒性

### 2. 评估指标优化策略

- **EDS优化**: 改进文本清理和标准化
- **F1优化**: 增强词汇提取准确性
- **TEDS优化**: 完善树结构构建算法
- **KTDS优化**: 优化阅读顺序排序逻辑

## 常见问题

### Q: 如何处理复杂的多栏布局？
A: 使用布局识别模型先分割栏目，然后按阅读顺序重新组织内容。

### Q: 公式识别不准确怎么办？
A: 可以调整公式识别的正则表达式模式，或者使用更专业的数学公式识别模型。

### Q: 表格格式不标准？
A: 检查表格提取逻辑，确保单元格分割准确，并验证Markdown表格语法。

### Q: 如何提高处理速度？
A: 增加并行线程数，使用GPU加速，或者对模型进行量化优化。

## 许可证

本项目基于AGPL-3.0许可证开源。

## 贡献

欢迎提交Issue和Pull Request来改进项目。

## 联系方式

如有问题请通过GitHub Issues联系。
