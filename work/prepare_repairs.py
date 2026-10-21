import pathlib, json, hashlib, difflib, ast, re
BASE=pathlib.Path(__file__).resolve().parent
OUT=BASE.parent/'outputs'/'修复与备份'
OUT.mkdir(parents=True,exist_ok=True)
records=[]

def save_repair(source, transform, reason, tests):
    source=pathlib.Path(source); raw=source.read_bytes(); text=raw.decode('utf-8-sig').replace('\r\n','\n')
    fixed=transform(text)
    if fixed==text: raise RuntimeError('未产生修改: '+str(source))
    ast.parse(fixed,filename=str(source))
    folder=OUT/f'{len(records)+1:02d}_{source.stem}'
    folder.mkdir(exist_ok=True)
    backup=folder/('原版_'+source.name); backup.write_bytes(raw)
    patched=folder/source.name; patched.write_text(fixed,encoding='utf-8',newline='\r\n' if b'\r\n' in raw else '')
    diff=folder/'修改对照.diff'; diff.write_text(''.join(difflib.unified_diff(text.splitlines(keepends=True),fixed.splitlines(keepends=True),fromfile=str(source),tofile=str(patched))),encoding='utf-8')
    records.append({'source':str(source),'repaired_copy':str(patched),'backup':str(backup),'diff':str(diff),'original_sha256':hashlib.sha256(raw).hexdigest(),'fixed_sha256':hashlib.sha256(patched.read_bytes()).hexdigest(),'reason':reason,'tests':tests,'applied':False})

screen=next(pathlib.Path(r'E:\a_a_A_lot_of_AI_computer').glob('A44*/main.py'))
def screen_fix(text):
    old='''            if result and "choices" in result and len(result["choices"]) > 0:
                  translated_text = result["choices"][0]["message"]["content"].strip()
                  logger.info(f"翻译成功，翻译结果长度: {len(translated_text)}字符")
                  return translated_text
              else:
                  logger.error(f"火山引擎API返回格式错误: {result}")
                  return "[翻译结果格式异常]"'''
    new='''            if result and "choices" in result and len(result["choices"]) > 0:
                translated_text = result["choices"][0]["message"]["content"].strip()
                logger.info(f"翻译成功，翻译结果长度: {len(translated_text)}字符")
                return translated_text
            else:
                logger.error(f"火山引擎API返回格式错误: {result}")
                return "[翻译结果格式异常]"'''
    assert old in text
    return text.replace(old,new)
save_repair(screen,screen_fix,'翻译API返回结果分支缩进错位，导致整个源码无法启动。','完整源码语法检查；使用模拟响应验证成功、空结果和异常分支，未调用付费API。')

api=pathlib.Path(r'E:\a_a_A_lot_of_AI_computer\A45\credit_card_system\web\api_integration.py')
def api_fix(text):
    marker='API_EXAMPLE_CODE = """'
    assert text.count(marker)==1
    left,right=text.split(marker,1)
    # The embedded SDK uses triple double-quoted docstrings; change only its outer delimiter.
    pos=right.rfind('"""')
    assert pos>0
    return left+"API_EXAMPLE_CODE = '''"+right[:pos]+"'''"+right[pos+3:]
save_repair(api,api_fix,'SDK示例字符串和内部说明使用同一种三引号，导致API模块无法解析。','完整源码语法检查；提取SDK示例再做独立语法检查，验证示例内容完整。')

usage=pathlib.Path(r'E:\jilu\01trea\main_window.py')
def usage_fix(text):
    text=text.replace('import datetime\n','import datetime\nfrom sqlalchemy import func\n',1)
    text=text.replace('db.func.sum(', 'func.sum(').replace('db.func.count(', 'func.count(')
    lines=text.splitlines(keepends=True)
    for name in ['duration_data','order_data','frequency_data']:
        start=next(i for i,line in enumerate(lines) if line.lstrip().startswith(name+' = db.query('))
        end=next(i for i in range(start+1,len(lines)) if lines[i].strip()=='.all()')
        head=lines[start]; indent=head[:len(head)-len(head.lstrip())]
        lines[start]=head.replace('= db.query(', '= (db.query(',1)
        for i in range(start+1,end+1): lines[i]=indent+'    '+lines[i].lstrip()
        lines[end]=lines[end].rstrip('\r\n')+')\n'
    text=''.join(lines)
    # PyQt6 removed the Qt5 QFileDialog.Options() constructor.
    text=text.replace('options = QFileDialog.Options()', 'options = QFileDialog.Option(0)')
    return text
save_repair(usage,usage_fix,'三处数据库查询换行缺少括号，统计函数调用到Session上，以及PyQt6保存窗口使用已移除的Qt5接口。','完整源码语法检查；使用隔离SQLite或模拟查询验证三种统计查询；未启动真实监控。')

def search_fix(text):
    text=text.replace('import chardet\n', 'try:\n    import chardet\nexcept ImportError:\n    chardet = None\n',1)
    text=text.replace("            result = chardet.detect(raw)\n            return result['encoding'] or 'utf-8'", "            if raw.startswith((b'\\xff\\xfe', b'\\xfe\\xff')):\n                return 'utf-16'\n            if raw.startswith(b'\\xef\\xbb\\xbf'):\n                return 'utf-8-sig'\n            try:\n                raw.decode('utf-8')\n                return 'utf-8'\n            except UnicodeDecodeError:\n                pass\n            if chardet is not None:\n                result = chardet.detect(raw)\n                if result.get('encoding') and result.get('confidence', 0) >= 0.8:\n                    return result['encoding']\n            return 'gb18030'")
    text=text.replace('    results = []\n    \n    for search_dir', "    results = []\n    seen_files = set()\n    skip_dirs = {'node_modules', 'site-packages', '.venv', 'venv', '__pycache__', '.git', '.pnpm-store'}\n    \n    for search_dir",1)
    text=text.replace('for root, _, files in os.walk(search_dir):', "for root, directories, files in os.walk(search_dir, followlinks=False):\n            directories[:] = sorted(d for d in directories if d.lower() not in skip_dirs)")
    text=text.replace("if file.endswith('.py'):", "if file.lower().endswith(('.py', '.pyw')):")
    text=text.replace('                    file_path = os.path.join(root, file)\n', "                    file_path = os.path.join(root, file)\n                    canonical = os.path.normcase(os.path.realpath(file_path))\n                    if canonical in seen_files:\n                        continue\n                    seen_files.add(canonical)\n",1)
    return text
for path in [r'E:\search_programs.py']:
    save_repair(path,search_fix,'扫描重复目录会重复列出程序、遗漏PYW/大写扩展名、将依赖源码当成程序，并且缺少chardet时直接退出。','隔离临时目录验证重叠路径去重、PY/PYW大小写、依赖目录排除和UTF-8/UTF-16/GB18030编码。')

(BASE/'repairs.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'prepared':len(records),'files':[r['source'] for r in records]},ensure_ascii=False))
