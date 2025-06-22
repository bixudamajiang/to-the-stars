// generate-search-index.js
const fs = require('fs');
const path = require('path');
const os = require('os');
const { normalize: unicodeNormalize } = require('unicode-normalization');

// 配置参数
const BOOKS_DIR = path.join(__dirname, 'books'); // 小说目录路径
const OUTPUT_FILE = path.join(__dirname, 'books.json'); // 输出文件

/**
 * 跨平台路径规范化
 * @param {string} filePath - 文件路径
 * @returns {string} 规范化后的路径
 */
function normalizePath(filePath) {
    // 转换为POSIX风格路径
    let posixPath = filePath.split(path.sep).join(path.posix.sep);
    
    // Unicode规范化 (NFC形式)
    return unicodeNormalize(posixPath);
}

/**
 * 内容规范化
 * @param {string} content - 文件内容
 * @returns {string} 规范化后的内容
 */
function normalizeContent(content) {
    // 统一行尾符为LF
    let normalized = content.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
    
    // Unicode规范化 (NFC形式)
    return unicodeNormalize(normalized);
}

/**
 * 构建简洁的书籍JSON索引
 * @param {string} booksDir - 书籍目录
 * @param {string} outputFile - 输出文件路径
 */
async function buildBookIndex(booksDir, outputFile) {
    // 尝试加载现有索引
    let existingIndex = {};
    if (fs.existsSync(outputFile)) {
        try {
            const data = fs.readFileSync(outputFile, 'utf8');
            const indexData = JSON.parse(data);
            
            for (const item of indexData) {
                // 使用规范化路径作为键
                const normPath = normalizePath(item.path);
                existingIndex[normPath] = {
                    content: item.content,
                    title: item.title,
                    directory: item.directory
                };
            }
            console.log(`✅ 加载现有索引: ${Object.keys(existingIndex).length} 个文件记录`);
        } catch (error) {
            console.log(`⚠️ 加载索引时出错，将重建: ${error.message}`);
            existingIndex = {};
        }
    }
    
    let newIndex = [];
    let totalFiles = 0;
    let newFiles = 0;
    let updatedFiles = 0;
    let skippedFiles = 0;
    
    /**
     * 递归处理目录
     * @param {string} dirPath - 当前目录路径
     * @param {string} basePath - 基础路径（用于相对路径计算）
     */
    function processDirectory(dirPath, basePath = '') {
        const items = fs.readdirSync(dirPath);
        
        for (const item of items) {
            const fullPath = path.join(dirPath, item);
            const relativePath = path.join(basePath, item);
            
            try {
                const stat = fs.statSync(fullPath);
                
                if (stat.isDirectory()) {
                    // 递归处理子目录
                    processDirectory(fullPath, relativePath);
                } else if (path.extname(item).toLowerCase() === '.md') {
                    // 处理Markdown文件
                    const content = fs.readFileSync(fullPath, 'utf8');
                    
                    // 规范化内容
                    const normalizedContent = normalizeContent(content);
                    
                    // 规范化路径
                    const normalizedPath = normalizePath(fullPath);
                    
                    // 检查是否需要更新
                    const existingEntry = existingIndex[normalizedPath];
                    if (existingEntry) {
                        // 直接比较内容是否相同
                        if (existingEntry.content === normalizedContent) {
                            // 使用现有条目
                            newIndex.push({
                                path: normalizedPath,
                                title: existingEntry.title,
                                directory: existingEntry.directory,
                                content: existingEntry.content
                            });
                            skippedFiles++;
                            continue;
                        }
                    }
                    
                    // 创建新条目
                    newIndex.push({
                        path: normalizedPath,
                        title: path.basename(item, '.md'),
                        directory: path.basename(dirPath),
                        content: normalizedContent
                    });
                    
                    totalFiles++;
                    if (existingEntry) {
                        updatedFiles++;
                    } else {
                        newFiles++;
                    }
                    
                    console.log(`✓ ${normalizedPath}`);
                } else {
                    skippedFiles++;
                }
            } catch (error) {
                console.error(`× 错误处理 ${fullPath}: ${error.message}`);
                skippedFiles++;
            }
        }
    }
    
    // 检查源目录是否存在
    if (!fs.existsSync(booksDir)) {
        console.error(`❌ 错误: 源目录 ${booksDir} 不存在`);
        process.exit(1);
    }
    
    console.log('开始生成搜索索引...');
    console.log(`源目录: ${BOOKS_DIR}`);
    console.log(`输出文件: ${OUTPUT_FILE}`);
    
    // 处理书籍目录
    processDirectory(booksDir);
    
    // 按路径排序确保一致顺序
    newIndex.sort((a, b) => a.path.localeCompare(b.path));
    
    // 写入JSON文件
    try {
        fs.writeFileSync(outputFile, JSON.stringify(newIndex, null, 2));
        console.log('\n索引完成!');
        console.log(`• 文件总数: ${newIndex.length}`);
        console.log(`• 新增文件: ${newFiles}`);
        console.log(`• 更新文件: ${updatedFiles}`);
        console.log(`• 未修改文件: ${skippedFiles}`);
        console.log(`索引已保存至: ${outputFile}`);
    } catch (error) {
        console.error('写入索引文件时出错:', error.message);
    }
}

// 主函数
function main() {
    console.log('='.repeat(60));
    console.log('简洁版小说索引构建工具');
    console.log('='.repeat(60));
    
    buildBookIndex(BOOKS_DIR, OUTPUT_FILE);
}

// 执行生成
main();