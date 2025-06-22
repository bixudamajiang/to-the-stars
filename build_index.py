import os
import json
import hashlib
import re
import sys
from pathlib import Path

def calculate_content_hash(content):
    """计算内容的MD5哈希值"""
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def build_book_index(books_dir, index_file):
    """构建书籍JSON索引（支持增量更新）"""
    # 尝试加载现有索引
    existing_index = {}
    if os.path.exists(index_file):
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                for item in json.load(f):
                    existing_index[item['path']] = {
                        'hash': item['hash'],
                        'last_indexed': item.get('last_indexed', 0)
                    }
            print(f"✅ 加载现有索引: {len(existing_index)} 个文件记录")
        except Exception as e:
            print(f"⚠️ 加载索引时出错，将重建: {str(e)}")
            existing_index = {}
    
    new_index = []
    total_files = 0
    new_files = 0
    updated_files = 0
    skipped_files = 0
    
    # 递归遍历所有目录
    for root, _, files in os.walk(books_dir):
        for file in files:
            if not file.endswith('.md'):
                skipped_files += 1
                continue
                
            file_path = Path(root) / file
            file_path_str = str(file_path)
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                
                # 计算内容哈希
                content_hash = calculate_content_hash(content)
                
                # 检查是否需要更新
                existing_entry = existing_index.get(file_path_str)
                if existing_entry and existing_entry['hash'] == content_hash:
                    # 使用现有条目（避免重复处理）
                    new_index.append({
                        "path": file_path_str,
                        "title": file,
                        "directory": Path(root).name,
                        "content": content,
                        "hash": content_hash,
                        "last_indexed": existing_entry['last_indexed'],
                        "status": "未修改"
                    })
                    skipped_files += 1
                    continue
                
                # 创建新条目
                new_index.append({
                    "path": file_path_str,
                    "title": file,
                    "directory": Path(root).name,
                    "content": content,
                    "hash": content_hash,
                    "last_indexed": os.path.getmtime(file_path),
                    "status": "新增" if not existing_entry else "更新"
                })
                
                total_files += 1
                if existing_entry:
                    updated_files += 1
                else:
                    new_files += 1
                
                print(f"✓ {file_path_str} - {'新增' if not existing_entry else '更新'}")
                
            except Exception as e:
                print(f"× 错误处理 {file_path_str}: {str(e)}")
                skipped_files += 1
    
    # 保存索引到JSON文件
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(new_index, f, ensure_ascii=False, indent=2)
    
    print(f"\n索引完成!")
    print(f"• 文件总数: {len(new_index)}")
    print(f"• 新增文件: {new_files}")
    print(f"• 更新文件: {updated_files}")
    print(f"• 未修改文件: {skipped_files}")
    print(f"索引已保存至: {index_file}")
    
    return len(new_index)

def main():
    """主函数"""
    # 配置路径
    BOOKS_DIR = 'books'        # 小说目录
    INDEX_FILE = 'books.json'  # 索引文件
    
    print("=" * 60)
    print("小说索引构建工具 - 增量更新版")
    print("=" * 60)
    
    # 确保books目录存在
    if not os.path.exists(BOOKS_DIR):
        print(f"❌ 错误: 小说目录 '{BOOKS_DIR}' 不存在")
        sys.exit(1)
    
    # 显示统计信息
    md_files = 0
    for root, _, files in os.walk(BOOKS_DIR):
        md_files += sum(1 for f in files if f.endswith('.md'))
    
    print(f"• 小说目录: {BOOKS_DIR}")
    print(f"• 索引文件: {INDEX_FILE}")
    print(f"• 检测到 {md_files} 个Markdown文件")
    print("-" * 60)
    
    # 构建索引
    count = build_book_index(BOOKS_DIR, INDEX_FILE)
    
    if count > 0:
        print("\n✅ 索引构建成功!")
        print("提示：下次运行将只处理修改或新增的文件")
    else:
        print("\n⚠️ 未找到可索引文件，请检查目录结构")

if __name__ == "__main__":
    main()