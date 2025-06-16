#!/usr/bin/env python3
"""
PDF到Markdown转换比赛解决方案安装脚本
"""

from setuptools import setup, find_packages
import os

# 读取README文件
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README_contest.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

# 读取requirements文件
def read_requirements():
    req_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(req_path):
        with open(req_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

setup(
    name="pdf-to-markdown-contest",
    version="1.0.0",
    description="PDF到Markdown转换比赛解决方案",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="Contest Team",
    author_email="team@example.com",
    url="https://github.com/your-repo/pdf-to-markdown-contest",
    
    packages=find_packages(),
    py_modules=[
        'pdf_to_markdown_contest',
        'enhanced_converter', 
        'evaluation_utils',
        'config',
        'test_system'
    ],
    
    install_requires=read_requirements(),
    
    extras_require={
        'dev': [
            'pytest>=6.0',
            'pytest-cov>=2.0',
            'black>=21.0',
            'flake8>=3.8',
            'mypy>=0.800',
        ],
        'gpu': [
            'onnxruntime-gpu>=1.12.0',
        ],
        'full': [
            'scipy>=1.7.0',
            'scikit-learn>=1.0.0',
            'matplotlib>=3.3.0',
            'seaborn>=0.11.0',
        ]
    },
    
    entry_points={
        'console_scripts': [
            'pdf2md-contest=pdf_to_markdown_contest:main',
            'pdf2md-enhanced=enhanced_converter:main',
            'pdf2md-eval=evaluation_utils:main',
            'pdf2md-test=test_system:main',
        ],
    },
    
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Text Processing :: Markup",
        "Topic :: Utilities",
    ],
    
    python_requires=">=3.8",
    
    keywords=[
        "pdf", "markdown", "document-parsing", "layout-analysis", 
        "text-extraction", "table-recognition", "formula-extraction",
        "document-structure", "reading-order", "contest"
    ],
    
    project_urls={
        "Bug Reports": "https://github.com/your-repo/pdf-to-markdown-contest/issues",
        "Source": "https://github.com/your-repo/pdf-to-markdown-contest",
        "Documentation": "https://github.com/your-repo/pdf-to-markdown-contest/blob/main/README_contest.md",
    },
    
    include_package_data=True,
    package_data={
        '': ['*.json', '*.yaml', '*.yml', '*.txt', '*.md'],
    },
    
    zip_safe=False,
)
