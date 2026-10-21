import os
try:
    import chardet
except ImportError:
    chardet = None
import re
from typing import List, Dict, Tuple

def detect_file_encoding(file_path: str) -> str:
    """检测文件编码"""
    try:
        with open(file_path, 'rb') as file:
            raw = file.read()
            if raw.startswith((b'\xff\xfe', b'\xfe\xff')):
                return 'utf-16'
            if raw.startswith(b'\xef\xbb\xbf'):
                return 'utf-8-sig'
            try:
                raw.decode('utf-8')
                return 'utf-8'
            except UnicodeDecodeError:
                pass
            if chardet is not None:
                result = chardet.detect(raw)
                if result.get('encoding') and result.get('confidence', 0) >= 0.8:
                    return result['encoding']
            return 'gb18030'
    except Exception as e:
        print(f"检测编码出错 {file_path}: {str(e)}")
        return 'utf-8'

def read_file_content(file_path: str) -> str:
    """读取文件内容，自动处理编码"""
    try:
        encoding = detect_file_encoding(file_path)
        print(f"正在读取文件: {file_path} (编码: {encoding})")
        with open(file_path, 'r', encoding=encoding) as file:
            return file.read()
    except Exception as e:
        print(f"读取文件出错 {file_path}: {str(e)}")
        return ""

def analyze_py_file(file_path: str) -> Dict[str, str]:
    """分析Python文件的功能特征"""
    print(f"\n正在分析文件: {file_path}")
    content = read_file_content(file_path)
    
    # 提取文件信息
    info = {
        'path': file_path,
        'name': os.path.basename(file_path),
        'content': content,
        'description': '',
        'features': set(),
        'start_cmd': f'python "{file_path}"'
    }
    
    # 分析注释和文档字符串
    doc_pattern = r'"""(.*?)"""|\'\'\'(.*?)\'\'\''
    comments = re.findall(doc_pattern, content, re.DOTALL)
    if comments:
        info['description'] = comments[0][0] or comments[0][1]
        print(f"找到文档注释: {info['description'][:100]}...")
    
    # 分析导入的模块
    imports = re.findall(r'import\s+(\w+)|from\s+(\w+)\s+import', content)
    for imp in imports:
        module = imp[0] or imp[1]
        info['features'].add(module)
    print(f"导入的模块: {', '.join(info['features'])}")
    
    # 功能特征识别
    feature_keywords = {
        'GUI': ['tkinter', 'PyQt', 'wx', '界面', '窗口'],
        '自动化': ['pyautogui', 'selenium', 'auto', '自动'],
        '文件处理': ['shutil', 'os.path', '文件', '复制'],
        '网络': ['requests', 'urllib', 'socket', '网络'],
        '数据处理': ['pandas', 'numpy', 'excel', '数据'],
        '图像处理': ['PIL', 'cv2', 'image', '图片'],
        '音频处理': ['pygame', 'playsound', '音频', '声音'],
        '定时任务': ['schedule', 'time.sleep', '定时', '闹钟'],
        '系统操作': ['os', 'sys', 'win32', '系统'],
        '爬虫': ['scrapy', 'beautifulsoup', '爬虫'],
    }
    
    for category, keywords in feature_keywords.items():
        if any(keyword.lower() in content.lower() for keyword in keywords):
            info['features'].add(category)
    print(f"识别的功能: {', '.join(info['features'])}")
    
    return info

def search_py_programs(target_features: List[str], search_dirs: List[str] = None) -> List[Dict[str, str]]:
    """搜索并分析Python程序"""
    if search_dirs is None or not search_dirs:
        search_dirs = ["C:\\", "D:\\", "E:\\", os.path.expanduser("~")]
    
    results = []
    seen_files = set()
    skip_dirs = {'node_modules', 'site-packages', '.venv', 'venv', '__pycache__', '.git', '.pnpm-store'}
    
    for search_dir in search_dirs:
        print(f"\n正在搜索目录: {search_dir}")
        if not os.path.exists(search_dir):
            print(f"目录不存在: {search_dir}")
            continue
            
        for root, directories, files in os.walk(search_dir, followlinks=False):
            directories[:] = sorted(d for d in directories if d.lower() not in skip_dirs)
            for file in files:
                if file.lower().endswith(('.py', '.pyw')):
                    file_path = os.path.join(root, file)
                    canonical = os.path.normcase(os.path.realpath(file_path))
                    if canonical in seen_files:
                        continue
                    seen_files.add(canonical)
                    print(f"\n发现Python文件: {file_path}")
                    try:
                        file_info = analyze_py_file(file_path)
                        
                        # 检查是否匹配目标功能
                        features_str = ' '.join(file_info['features']).lower()
                        content_str = file_info['content'].lower()
                        
                        for target in target_features:
                            target = target.lower()
                            if (target in features_str or 
                                target in content_str or 
                                target in file_info['name'].lower() or 
                                target in file_info['description'].lower()):
                                print(f"匹配关键词: {target}")
                                results.append(file_info)
                                break
                    except Exception as e:
                        print(f"处理文件出错 {file_path}: {str(e)}")
                        continue
    
    return results

def print_results(results: List[Dict[str, str]]):
    """格式化输出结果"""
    print("\n找到以下Python程序：")
    print("-" * 80)
    for i, info in enumerate(results, 1):
        print(f"\n{i}. 程序名称：{info['name']}")
        print(f"   完整路径：{info['path']}")
        print(f"   启动命令：{info['start_cmd']}")
        if info['description']:
            print(f"   程序描述：{info['description'][:200]}...")
        print(f"   功能特征：{', '.join(info['features'])}")
        print("-" * 80)

if __name__ == "__main__":
    # 设置搜索路径为E盘
    search_dirs = ["E:\\"]
    
    print(f"开始搜索Python程序...")
    print(f"搜索路径: {search_dirs}")
    
    # 这里替换为你要搜索的功能关键词
    target_features = [
        "自动点击", "auto click",  # 区域自动点击
        "待办事项", "todo", "task",  # 待办事项
        "语音播报", "voice", "tts",  # 语音播报
        "应用记录", "usage record",  # 记录应用使用情况
        "目录生成", "directory",  # 自动生成目录
        "重命名", "rename",  # 批量重命名
        "定时提醒", "闹钟", "alarm",  # 定时提醒（闹钟）
        "文件同步", "sync",  # 文件同步工具
        "计算器", "calculator",  # 计算器
        "关机", "shutdown",  # 自动关机
        "密码管理", "password",  # 密码管理器
        "文本处理", "text process",  # 文本处理工具
        "数据可视化", "visualization",  # 数据可视化工具
        "excel", "表格处理",  # Excel数据处理
        "pdf合并", "pdf merge",  # PDF合并工具
        "图像处理", "image process",  # 图像处理工具
        "爬虫", "crawler", "spider",  # 网页爬虫
        "聊天机器人", "chatbot",  # 聊天机器人
        "自动化脚本", "automation",  # 自动化脚本框架
        "游戏辅助", "game assist",  # 游戏辅助工具
        "系统监控", "monitor",  # 系统监控工具
        "拼音转换", "pinyin",  # 批量互改中文文件名为拼音
        "图片尺寸", "resize",  # 批量修改图片尺寸
        "锁屏", "screen lock",  # 星空锁屏
        "记事本", "notepad",  # 简易记事本
        "二维码", "qrcode"  # 二维码生成器
    ]
    
    print("正在搜索Python程序，请稍候...")
    print(f"搜索关键词: {target_features}")
    
    results = search_py_programs(target_features, search_dirs)
    print(f"\n找到 {len(results)} 个匹配的程序")
    print_results(results)
    
    if not results:
        print("\n未找到匹配的Python程序。")
    
    input("\n按回车键退出...")
