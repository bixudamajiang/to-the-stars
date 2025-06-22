import os
import json
import re
from pathlib import Path

def build_book_index(books_dir, index_file):
    """构建书籍JSON索引"""
    book_index = []
    total_files = 0
    skipped_files = 0
    
    # 递归遍历所有目录
    for root, _, files in os.walk(books_dir):
        for file in files:
            if not file.endswith('.md'):
                skipped_files += 1
                continue
                
            file_path = Path(root) / file
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                
                # 添加文件信息到索引
                book_index.append({
                    "path": str(file_path),
                    "title": file,
                    "directory": Path(root).name,
                    "content": content
                })
                
                total_files += 1
                print(f"✓ 已索引: {file_path}")
                
            except Exception as e:
                print(f"× 错误处理 {file_path}: {str(e)}")
                skipped_files += 1
    
    # 保存索引到JSON文件
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(book_index, f, ensure_ascii=False, indent=2)
    
    print(f"\n索引完成! 共处理 {total_files} 个文件, 跳过 {skipped_files} 个非MD文件")
    print(f"索引已保存至: {index_file}")
    return total_files

if __name__ == "__main__":
    # 配置路径
    BOOKS_DIR = 'books'        # 小说目录
    INDEX_FILE = 'books.json'  # 索引文件
    
    print("开始构建书籍索引...")
    
    # 确保books目录存在
    if not os.path.exists(BOOKS_DIR):
        print(f"错误: 小说目录 '{BOOKS_DIR}' 不存在")
        sys.exit(1)
    
    count = build_book_index(BOOKS_DIR, INDEX_FILE)
    
    if count > 0:
        print("提示：搜索时使用正则表达式进行高级匹配")
    else:
        print("错误：未找到可索引文件，请检查目录结构")