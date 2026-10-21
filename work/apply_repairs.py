import pathlib,json,hashlib,ast,os
BASE=pathlib.Path(__file__).resolve().parent
repairs=json.loads((BASE/'repairs.json').read_text(encoding='utf-8'))
tests=json.loads((BASE/'repair_test_results.json').read_text(encoding='utf-8'))
assert all(t['passed'] for t in tests)
for r in repairs:
    p=pathlib.Path(r['source'])
    for ancestor in [p.parent,*p.parents]:
        instructions=ancestor/'AGENTS.md'
        if instructions.exists():
            raise RuntimeError('须先核对源目录指令: '+str(instructions))
    assert hashlib.sha256(p.read_bytes()).hexdigest()==r['original_sha256'],'原文件已有新修改，停止替换: '+str(p)
    assert pathlib.Path(r['backup']).read_bytes()==p.read_bytes()
    ast.parse(pathlib.Path(r['repaired_copy']).read_text(encoding='utf-8'))
applied=[]
try:
    for r in repairs:
        p=pathlib.Path(r['source']); tmp=p.with_name(p.name+'.codex-repair.tmp')
        if tmp.exists(): raise RuntimeError('已有临时文件: '+str(tmp))
        tmp.write_bytes(pathlib.Path(r['repaired_copy']).read_bytes())
        os.replace(tmp,p); applied.append(r)
        assert hashlib.sha256(p.read_bytes()).hexdigest()==r['fixed_sha256']
        ast.parse(p.read_text(encoding='utf-8'))
        r['applied']=True
except Exception:
    for r in reversed(applied):
        pathlib.Path(r['source']).write_bytes(pathlib.Path(r['backup']).read_bytes());r['applied']=False
    raise
for r in repairs:
    r['tests']='；'.join(t['check'] for t in tests if t['source']==r['source'])
(BASE/'repairs.json').write_text(json.dumps(repairs,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'applied':len(applied),'backups_verified':len(applied),'source_syntax_passed':len(applied)},ensure_ascii=False))
