import json
import sys
import os
import re
from pathlib import Path

MAX_FILES = 100     # 最大显示文件数
MAX_SNIPPETS = 10   # 每个文件最多显示片段数
CONTEXT_SIZE = 100  # 匹配上下文字符数
PAGE_SIZE = 10      # 每页显示文件数
OVERVIEW_PAGE_SIZE = 20  # 概览页面每页文件数

def highlight_text(text, pattern):
    """高亮匹配文本"""
    return pattern.sub(lambda m: f"【{m.group()}】", text)

def extract_context(content, pattern, max_snippets=5):
    """提取包含搜索词的上下文"""
    snippets = []
    # 查找所有匹配位置
    matches = list(pattern.finditer(content))
    
    # 处理每个匹配
    for i, match in enumerate(matches[:max_snippets]):
        start = max(0, match.start() - CONTEXT_SIZE)
        end = min(len(content), match.end() + CONTEXT_SIZE)
        
        # 提取上下文
        context = content[start:end]
        
        # 添加边界指示
        if start > 0:
            context = "..." + context
        if end < len(content):
            context = context + "..."
            
        snippets.append(context)
    
    return snippets

def show_file_details(book, pattern):
    """显示单个文件的详细匹配内容"""
    content = book["content"]
    snippets = extract_context(content, pattern, MAX_SNIPPETS)
    
    if not snippets:
        print("未找到匹配片段")
        return
    
    print(f"\n📖 文件: {book['title']}")
    print(f"📁 目录: {book['directory']}")
    print(f"🔍 匹配数: {len(list(pattern.finditer(content)))}")
    print(f"🛣️ 路径: {book['path']}")
    print("-" * 80)
    
    # 显示每个匹配片段
    for j, snippet in enumerate(snippets, 1):
        highlighted = highlight_text(snippet, pattern)
        print(f"\n🔍 匹配片段 {j}:")
        # 格式化输出
        lines = [highlighted[i:i+80] for i in range(0, len(highlighted), 80)]
        for line in lines:
            print(f"    {line}")
    
    print("\n" + "=" * 80)

def search_books(index_file, query):
    """执行正则搜索"""
    try:
        with open(index_file, 'r', encoding='utf-8') as f:
            books = json.load(f)
    except FileNotFoundError:
        print(f"错误: 索引文件 {index_file} 不存在，请先运行 build_index.py")
        return
    
    # 编译正则表达式（不区分大小写）
    try:
        pattern = re.compile(query, re.IGNORECASE)
    except re.error as e:
        print(f"错误: 无效的正则表达式 '{query}': {str(e)}")
        return
    
    # 搜索所有书籍并收集匹配信息
    matching_books = []
    total_matches = 0
    
    for book in books:
        content = book["content"]
        matches = list(pattern.finditer(content))
        match_count = len(matches)
        
        if match_count > 0:
            total_matches += match_count
            # 存储基本信息用于概览
            matching_books.append({
                "path": book["path"],
                "title": book["title"],
                "directory": book["directory"],
                "match_count": match_count,
                "content": content  # 保留内容用于详细查看
            })
    
    if not matching_books:
        print(f"\n未找到匹配内容 (查询: {query})")
        return
    
    total_files = len(matching_books)
    print(f"\n找到 {total_matches} 处匹配 (分布在 {total_files} 个文件中)")
    
    # 按匹配次数降序排序
    matching_books.sort(key=lambda x: x["match_count"], reverse=True)
    
    # 检查文件数量限制
    if total_files > MAX_FILES:
        print(f"⚠️ 匹配文件过多 (超过{MAX_FILES}个)，只显示前{MAX_FILES}个文件")
        matching_books = matching_books[:MAX_FILES]
        total_files = MAX_FILES
    
    # 概览模式 - 显示文件列表和匹配次数
    overview_page = 0
    total_overview_pages = (total_files + OVERVIEW_PAGE_SIZE - 1) // OVERVIEW_PAGE_SIZE
    
    while True:
        start_idx = overview_page * OVERVIEW_PAGE_SIZE
        end_idx = min(start_idx + OVERVIEW_PAGE_SIZE, total_files)
        
        print(f"\n📊 概览页 {overview_page+1}/{total_overview_pages} (共 {total_files} 个文件)")
        print("-" * 80)
        print("序号 | 匹配数 | 文件")
        print("-" * 80)
        
        for i in range(start_idx, end_idx):
            book = matching_books[i]
            print(f"{i+1:4d} | {book['match_count']:6d} | {book['directory']}/{book['title']}")
        
        print("-" * 80)
        print("命令: n=下一页, p=上一页, 1-999=查看文件详情, q=退出")
        user_input = input("请输入命令: ").strip().lower()
        
        # 处理导航命令
        if user_input == 'n':
            if overview_page < total_overview_pages - 1:
                overview_page += 1
            else:
                print("已经是最后一页")
        elif user_input == 'p':
            if overview_page > 0:
                overview_page -= 1
            else:
                print("已经是第一页")
        elif user_input == 'q':
            print("\n搜索已结束")
            return
        elif user_input.isdigit():
            file_index = int(user_input) - 1
            if 0 <= file_index < total_files:
                # 进入详细查看模式
                show_file_details(matching_books[file_index], pattern)
            else:
                print(f"错误: 无效的文件序号 (1-{total_files})")
        else:
            print("错误: 无效的命令")

if __name__ == "__main__":
    INDEX_FILE = 'books.json'
    
    if len(sys.argv) < 2:
        print("小说正则搜索工具 - 增强版")
        print("使用方法: python search.py <搜索词或正则表达式>")
        print("示例: python search.py \"悲叹之种\"")
        print("高级搜索: python search.py \"魔法少女|魔女\"")
        print("精确搜索: python search.py \"\\b悲叹之种\\b\"")
        sys.exit(1)
    
    query = ' '.join(sys.argv[1:])
    print(f"🔍 搜索: {query}")
    
    try:
        search_books(INDEX_FILE, query)
    except KeyboardInterrupt:
        print("\n搜索已取消")