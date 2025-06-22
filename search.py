import json
import sys
import os
import re
from pathlib import Path

MAX_FILES = 100     # 最大显示文件数
MAX_SNIPPETS = 10   # 每个文件最多显示片段数
CONTEXT_SIZE = 100  # 匹配上下文字符数
OVERVIEW_PAGE_SIZE = 20  # 概览页面每页文件数

# 全局变量存储索引数据
books_index = None
index_loaded = False

def load_index(index_file):
    """加载索引文件到内存"""
    global books_index, index_loaded
    try:
        with open(index_file, 'r', encoding='utf-8') as f:
            books_index = json.load(f)
        index_loaded = True
        print(f"✅ 索引已加载: 共 {len(books_index)} 个文件")
    except FileNotFoundError:
        print(f"❌ 错误: 索引文件 {index_file} 不存在")
        print("请先运行 build_index.py 创建索引")
        return False
    except Exception as e:
        print(f"❌ 加载索引时出错: {str(e)}")
        return False
    return True

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

def execute_search(query):
    """执行搜索并显示结果"""
    if not index_loaded or not books_index:
        print("索引未加载，无法搜索")
        return
    
    # 编译正则表达式（不区分大小写）
    try:
        pattern = re.compile(query, re.IGNORECASE)
    except re.error as e:
        print(f"❌ 错误: 无效的正则表达式 '{query}': {str(e)}")
        return
    
    # 搜索所有书籍并收集匹配信息
    matching_books = []
    total_matches = 0
    
    for book in books_index:
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
        print(f"\n❌ 未找到匹配内容 (查询: {query})")
        return
    
    total_files = len(matching_books)
    print(f"\n✅ 找到 {total_matches} 处匹配 (分布在 {total_files} 个文件中)")
    
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
        print("命令: n=下一页, p=上一页, 1-999=查看文件详情, b=返回搜索, q=退出")
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
        elif user_input == 'b':
            print("\n返回搜索界面")
            return  # 返回主循环
        elif user_input == 'q':
            print("\n感谢使用，再见！")
            sys.exit(0)
        elif user_input.isdigit():
            file_index = int(user_input) - 1
            if 0 <= file_index < total_files:
                # 进入详细查看模式
                show_file_details(matching_books[file_index], pattern)
                print("按回车键返回概览...")
                input()
            else:
                print(f"❌ 错误: 无效的文件序号 (1-{total_files})")
        else:
            print("❌ 错误: 无效的命令")

def interactive_search(index_file):
    """交互式搜索主循环"""
    # 加载索引
    if not load_index(index_file):
        return
    
    print("\n" + "=" * 60)
    print("小说全文搜索工具 - 交互式模式")
    print("=" * 60)
    print("输入搜索词或正则表达式开始搜索")
    print("支持命令: /help 显示帮助, /exit 退出程序")
    print("-" * 60)
    
    while True:
        try:
            # 获取用户输入
            user_input = input("\n🔍 请输入搜索词: ").strip()
            
            # 处理特殊命令
            if not user_input:
                continue
            elif user_input.lower() == '/exit' or user_input.lower() == '/quit':
                print("感谢使用，再见！")
                break
            elif user_input.lower() == '/help':
                print("\n📘 帮助信息:")
                print("- 输入搜索词进行搜索 (例如: 魔法少女)")
                print("- 使用正则表达式进行高级搜索 (例如: 魔法少女|魔女)")
                print("- 精确单词匹配 (例如: \\b悲叹之种\\b)")
                print("\n📘 特殊命令:")
                print("  /help - 显示此帮助信息")
                print("  /exit - 退出程序")
                print("  /quit - 退出程序")
                continue
            
            # 执行搜索
            print(f"正在搜索: {user_input}")
            execute_search(user_input)
            
        except KeyboardInterrupt:
            print("\n检测到中断，输入 /exit 退出程序")
        except Exception as e:
            print(f"❌ 搜索过程中出错: {str(e)}")

if __name__ == "__main__":
    INDEX_FILE = 'books.json'
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        # 命令行模式
        if not load_index(INDEX_FILE):
            sys.exit(1)
        
        query = ' '.join(sys.argv[1:])
        print(f"🔍 搜索: {query}")
        execute_search(query)
    else:
        # 交互模式
        interactive_search(INDEX_FILE)