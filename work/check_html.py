import pathlib,json,re,subprocess,concurrent.futures,hashlib
BASE=pathlib.Path(__file__).resolve().parent
NODE=r'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
rs=json.loads((BASE/'inventory.json').read_text(encoding='utf-8'))
htmls=[r for r in rs if r['category']=='开发候选' and r['extension'] in {'.html','.htm'} and r.get('sha256')]
unique={}
for r in htmls: unique.setdefault(r['sha256'],r)
def check(r):
    try:
        text=pathlib.Path(r['path']).read_text(encoding=r.get('encoding','utf-8'))
        result={'path':r['path'],'sha256':r['sha256'],'inline_scripts':0,'checked':0,'errors':[],'missing_scripts':[],'template_skipped':0}
        for attrs,code in re.findall(r'<script([^>]*)>(.*?)</script\s*>',text,re.I|re.S):
            src=re.search(r'\bsrc\s*=\s*["\']([^"\']+)',attrs,re.I)
            if src:
                target=src.group(1)
                if not re.match(r'https?:|//|data:|/|\{',target) and not (pathlib.Path(r['path']).parent/target.split('?')[0]).exists(): result['missing_scripts'].append(target)
                continue
            if not code.strip():continue
            typ=re.search(r'\btype\s*=\s*["\']([^"\']+)',attrs,re.I)
            if typ and typ.group(1) not in {'module','text/javascript','application/javascript'}:continue
            result['inline_scripts']+=1
            if '{{' in code or '{%' in code:result['template_skipped']+=1;continue
            mode='module' if typ and typ.group(1)=='module' else 'commonjs'
            proc=subprocess.run([NODE,'--input-type='+mode,'--check'],input=code,capture_output=True,text=True,encoding='utf-8',timeout=8)
            result['checked']+=1
            if proc.returncode:
                msg=re.search(r'SyntaxError: ([^\r\n]+)',proc.stderr)
                result['errors'].append(msg.group(1) if msg else proc.stderr[-300:])
        return result
    except Exception as e:return {'path':r['path'],'read_error':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool: results=list(pool.map(check,unique.values()))
(BASE/'html_checks.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'unique_html':len(results),'checked_scripts':sum(r.get('checked',0) for r in results),'syntax_errors':[r for r in results if r.get('errors')],'missing_script_files':sum(bool(r.get('missing_scripts')) for r in results)},ensure_ascii=False))
