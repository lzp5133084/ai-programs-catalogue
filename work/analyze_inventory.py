import pathlib, json, collections, re, ast, hashlib, datetime, concurrent.futures
BASE=pathlib.Path(__file__).resolve().parent
TARGET={'.html','.htm','.py','.pyw','.bat','.cmd','.ps1','.exe','.apk','.aab','.app','.jar','.vbs','.sh'}
VENDOR_ROOTS={'360ai浏览器','360downloads','580驱动','百度网盘','剪映','微信开发者工具','智能鼠标','android studio','android studio1','clash verge','flclash','kgmusic','kugou','ollama','ollama-chucunlujin','python312','qianwenapp','qycache','snipaste-2.10.5-x64','snipaste-2.10.6-x64','tengxun','trae cn','trae solo cn','豆包','搜狗输入法','腾讯会议','微信','cursor','trae','weixinkaifazhegongju','单击游戏','电脑急救包勿删除','扣子','codex','kdubasoftdownloads'}
VENDOR_PARTS={'node_modules','site-packages','__pycache__','.venv','venv','.git','.pnpm-store','_internal','jbr','sdk','sdks','cmake','build-tools','platform-tools','dist-info','tts-deps','pip-deps','python312','python313','python314','python311','ffmpeg_extract','flutter','ffmpeg','pd6p-win-g1010-1_03-ea34_2','win-g1010-1_4-n_mcd'}
paths=[]
for file in BASE.glob('*_files.txt'):
    paths+=file.read_text(encoding='utf-8-sig',errors='replace').splitlines()
paths=sorted(set(p for p in paths if p and not p.startswith('rg:') and not p.lower().startswith(str(BASE.parent).lower()+'\\')))

def category(p):
    parts=pathlib.PureWindowsPath(p).parts
    lower=[x.lower() for x in parts]
    if any(x in lower for x in ['.ripgrep','.wdm']) or parts[-1].lower()=='mavis-trash.cmd': return '运行环境或依赖组件'
    if any(x in lower for x in ['.codebuddy','.cursor','.trae','.trae-cn','.workbuddy','.minidev','.minimax','.openclaw']) and any(x in lower for x in ['extensions','plugins','binaries','builtin','builtin_skills','.builtin-skills','design_libraries','dl_cache','toolhost','assets']): return '运行环境或依赖组件'
    if len(parts)>1 and parts[0][0] in 'DE' and lower[1] in VENDOR_ROOTS:
        # The user's similarly named WeChat source project lives on E:\weixinkaifazhegongju.
        if lower[1]=='weixinkaifazhegongju' and parts[0][0]=='E': return '开发候选'
        return '第三方软件或安装组件'
    if any(x in VENDOR_PARTS or x.endswith('.dist-info') for x in lower): return '运行环境或依赖组件'
    if 'appdata' in lower: return '软件运行数据或组件'
    if any(x in lower for x in ['xwechat_files','weixinshuju','wechat files','微信备份','baidunetdiskdownload','360ai浏览器下载','qq浏览器下载内容','浏览器下载']): return '收到或下载的程序，作者待核实'
    name=parts[-1].lower()
    if name in {'licenses.chromium.html','elevate.exe','cloudflared.exe','cpolar.exe','app_shell_updater.exe','dump_reporter.exe','elevation_service.exe','crashpad_handler.exe','rg.exe','fastboot.exe','codex-code-mode-host.exe','codex-command-runner.exe'}: return '第三方软件或安装组件'
    if pathlib.PureWindowsPath(p).suffix.lower()=='.exe' and re.search(r'setup|installer|install|unins|trae_|codebuddy-win|snipaste|python.exe|pythonw.exe|ffmpeg|ffprobe|node.exe|uv.exe|adb.exe',name): return '第三方软件或安装组件'
    if any(x.startswith('xref-') or x.startswith('warn-') for x in lower): return '构建诊断文件'
    if 'build' in lower and pathlib.PureWindowsPath(p).suffix.lower() not in {'.apk','.aab','.exe'}: return '构建或测试辅助文件'
    if any(x in lower for x in ['tests','test','docs','samples','examples']) or name.startswith('test_'): return '测试或文档辅助文件'
    if 'work' in lower and 'codex' in lower: return 'AI开发过程辅助文件'
    return '开发候选'

def group(p):
    q=pathlib.PureWindowsPath(p); parts=q.parts; low=[x.lower() for x in parts]
    if parts[0][0] in 'DE':
        if len(parts)==2: return p
        if low[1]=='chat gpt6' and len(parts)>3 and parts[2] in {'01_项目','主动保存','Organized Downloads'}:
            return str(pathlib.PureWindowsPath(*parts[:4]))
        if low[1] in {'a_a_a_lot_of_ai_computer','chat gpt6'}: return str(pathlib.PureWindowsPath(*parts[:3]))
        return str(pathlib.PureWindowsPath(*parts[:2]))
    if 'codex' in low:
        i=low.index('codex'); return str(pathlib.PureWindowsPath(*parts[:min(i+3,len(parts))]))
    if 'doubao' in low and 'chats' in low:
        i=low.index('chats'); return str(pathlib.PureWindowsPath(*parts[:min(i+3,len(parts))]))
    if '.trae-cn' in low and 'memory' in low:
        i=low.index('memory');return str(pathlib.PureWindowsPath(*parts[:min(i+2,len(parts))]))
    if '.trae-cn' in low and 'attachments' in low:
        i=low.index('attachments');return str(pathlib.PureWindowsPath(*parts[:min(i+2,len(parts))]))
    if 'desktop' in low:
        i=low.index('desktop')
        if len(parts)<=i+2 or parts[i+1] in ['快捷启动程序','7月桌面应用集合']: return p
        return str(pathlib.PureWindowsPath(*parts[:i+2]))
    if 'desktop_code' in low: return p
    if 'documents' in low:
        i=low.index('documents'); return str(pathlib.PureWindowsPath(*parts[:min(i+2,len(parts))]))
    if 'downloads' in low:
        i=low.index('downloads'); return p if len(parts)==i+2 else str(pathlib.PureWindowsPath(*parts[:i+2]))
    return str(q.parent)

def decode(raw):
    encodings=['utf-16','utf-8-sig','gb18030'] if raw.startswith((b'\xff\xfe',b'\xfe\xff')) else ['utf-8-sig','gb18030']
    for enc in encodings:
        try: return raw.decode(enc),enc
        except UnicodeError: pass
    return raw.decode('utf-8',errors='replace'),'utf-8(含替换字符)'

def inspect(p):
    q=pathlib.Path(p); cat=category(p)
    r={'path':p,'extension':q.suffix.lower(),'category':cat,'project':group(p),'name':q.name}
    try:
        st=q.stat(); r.update(size=st.st_size,created=datetime.datetime.fromtimestamp(st.st_ctime,datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='seconds'),modified=datetime.datetime.fromtimestamp(st.st_mtime,datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='seconds'))
        if cat not in ['开发候选','收到或下载的程序，作者待核实']: return r
        if q.suffix.lower() not in {'.exe','.apk','.aab','.jar','.app'} and st.st_size<3_000_000:
            raw=q.read_bytes(); text,enc=decode(raw); r['encoding']=enc; r['sha256']=hashlib.sha256(raw).hexdigest()
            r['ai_markers']=[x for x in ['DeepSeek','ChatGPT','Claude','TRAE','CodeBuddy','豆包','Codex','Cursor'] if re.search(re.escape(x),text,re.I)]
            if q.suffix.lower() in {'.html','.htm'}:
                title=re.search(r'<title[^>]*>(.*?)</title>',text,re.I|re.S); r['title']=re.sub(r'\s+',' ',title.group(1)).strip() if title else ''
                r['features']=list(dict.fromkeys(re.sub('<[^>]+>','',s).strip() for s in re.findall(r'<(?:h[1-3]|button)[^>]*>(.*?)</(?:h[1-3]|button)>',text,re.I|re.S)))[:18]
                r['external_scripts']=re.findall(r'<script[^>]+src=["\']([^"\']+)',text,re.I)[:8]
                r['storage']=bool(re.search('localStorage|indexedDB',text))
            elif q.suffix.lower() in {'.py','.pyw'}:
                try:
                    tree=ast.parse(text,filename=p); r['syntax']='通过'; imports=set()
                    for n in ast.walk(tree):
                        if isinstance(n,ast.Import): imports.update(v.name.split('.')[0] for v in n.names)
                        elif isinstance(n,ast.ImportFrom) and n.module: imports.add(n.module.split('.')[0])
                    r['imports']=sorted(imports); r['docstring']=(ast.get_docstring(tree) or '')[:500]
                    r['functions']=[n.name for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.ClassDef))][:35]
                except SyntaxError as e: r['syntax']=f'语法错误，第{e.lineno}行：{e.msg}'
                r['title']=' / '.join(dict.fromkeys(re.findall(r'(?:\.title|setWindowTitle)\(\s*["\']([^"\']{1,100})',text)))[:220]
                r['main_guard']='__main__' in text
            elif q.name.lower().startswith('readme'):
                r['heading']=' / '.join(re.findall(r'^#{1,3}\s+(.+)',text,re.M)[:12])[:500]
                r['excerpt']=re.sub(r'(?:sk-|AIza)[A-Za-z0-9_-]{12,}','[已隐藏]',text[:1400])
            elif q.name=='package.json':
                try:
                    d=json.loads(text);r['package']={k:d.get(k) for k in ['name','description','scripts','dependencies','devDependencies']}
                except ValueError: pass
            elif q.suffix.lower() in {'.bat','.cmd','.ps1'}:
                r['relative_launch']=bool(re.search(r'python[^\r\n]*\s+[\w\u4e00-\u9fff_-]+\.py|start[^\r\n]+\.html',text,re.I))
                r['sets_cwd']=bool(re.search(r'%~dp0|PSScriptRoot|Set-Location',text,re.I))
                r['dangerous']=bool(re.search(r'\b(?:del|rd|rmdir|format|diskpart)\b|Remove-Item|reg delete',text,re.I))
    except Exception as e: r['read_error']=type(e).__name__+': '+str(e)
    return r

with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool: records=list(pool.map(inspect,paths))
(BASE/'inventory.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
groups=collections.defaultdict(list)
for r in records:
    if r['category']=='开发候选': groups[r['project']].append(r)
summary=[]
for p,rs in sorted(groups.items()):
    summary.append({'project':p,'count':len(rs),'types':dict(collections.Counter(r['extension'] for r in rs)), 'titles':list(dict.fromkeys(r.get('title','') for r in rs if r.get('title')))[:12], 'files':[r['name'] for r in rs if r['extension'] in TARGET][:50], 'headings':[r.get('heading','') for r in rs if r.get('heading')][:3], 'syntax_errors':[{k:r[k] for k in ['path','syntax']} for r in rs if r.get('syntax','').startswith('语法错误')]})
(BASE/'group_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'paths':len(paths),'categories':dict(collections.Counter(r['category'] for r in records)),'projects':len(groups),'python_errors':[{'path':r['path'],'syntax':r['syntax']} for r in records if r.get('syntax','').startswith('语法错误')]},ensure_ascii=False))
