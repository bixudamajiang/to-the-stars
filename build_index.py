import os
import json
import hashlib
import sys
from pathlib import Path, PurePath
import unicodedata

def normalize_path(path):
    """跨平台路径规范化"""
    # 转换为POSIX风格路径
    posix_path = PurePath(path).as_posix()
    # Unicode规范化 (NFC形式)
    return unicodedata.normalize('NFC', posix_path)

def normalize_content(content):
    """内容规范化"""
    # 统一行尾符为LF
    normalized = content.replace('\r\n', '\n').replace('\r', '\n')
    # Unicode规范化 (NFC形式)
    return unicodedata.normalize('NFC', normalized)

def build_book_index(books_dir, index_file):
    """构建简洁的书籍JSON索引"""
    # 尝试加载现有索引
    existing_index = {}
    if os.path.exists(index_file):
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                for item in json.load(f):
                    # 使用规范化路径作为键
                    norm_path = normalize_path(item['path'])
                    existing_index[norm_path] = {
                        'content': item['content'],
                        'title': item['title'],
                        'directory': item['directory']
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
            if not file.lower().endswith('.md'):
                skipped_files += 1
                continue
                
            file_path = Path(root) / file
            file_path_str = str(file_path)
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    raw_content = f.read()
                
                # 规范化内容
                normalized_content = normalize_content(raw_content)
                
                # 规范化路径
                normalized_path = normalize_path(file_path_str)
                
                # 检查是否需要更新
                existing_entry = existing_index.get(normalized_path)
                if existing_entry:
                    # 直接比较内容是否相同
                    if existing_entry['content'] == normalized_content:
                        # 使用现有条目
                        new_index.append({
                            "path": normalized_path,
                            "title": existing_entry['title'],
                            "directory": existing_entry['directory'],
                            "content": existing_entry['content']
                        })
                        skipped_files += 1
                        continue
                
                # 创建新条目
                new_index.append({
                    "path": normalized_path,
                    "title": file,
                    "directory": Path(root).name,
                    "content": normalized_content
                })
                
                total_files += 1
                if existing_entry:
                    updated_files += 1
                else:
                    new_files += 1
                
                print(f"✓ {normalized_path}")
                
            except Exception as e:
                print(f"× 错误处理 {file_path_str}: {str(e)}")
                skipped_files += 1
    
    # 按路径排序确保一致顺序
    new_index.sort(key=lambda x: x['path'])
    
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
    print("简洁版小说索引构建工具")
    print("=" * 60)
    
    # 确保books目录存在
    if not os.path.exists(BOOKS_DIR):
        print(f"❌ 错误: 小说目录 '{BOOKS_DIR}' 不存在")
        sys.exit(1)
    
    # 构建索引
    count = build_book_index(BOOKS_DIR, INDEX_FILE)
    
    if count > 0:
        print("\n✅ 索引构建成功!")
    else:
        print("\n⚠️ 未找到可索引文件")

if __name__ == "__main__":
    main()