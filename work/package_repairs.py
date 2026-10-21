import pathlib,json,zipfile,hashlib
BASE=pathlib.Path(__file__).resolve().parent
OUT=BASE.parent/'outputs'
rs=json.loads((BASE/'repairs.json').read_text(encoding='utf-8'))
lines=['# 本次修复与恢复说明','','4份源码已写回原路径，原版备份和修改对照完整保留。','','修复验证：4份完整源码语法检查、内嵌SDK语法检查、程序搜索编码/路径去重测试、翻译结果模拟分支、应用统计模拟查询，共8项检查。完整GUI、真实数据库、外部API和安卓真机未验收。应用使用监控尚需SQLAlchemy运行依赖。','','## 修复记录','']
for i,r in enumerate(rs,1):
    lines.extend([f"### {i}. {r['source']}",'',r['reason'],'','验证：'+r['tests'],'','原版：'+r['backup'],'','修复版：'+r['repaired_copy'],''])
lines.extend(['## 恢复到修复前','','关闭对应程序。解压修复备份包，找到对应目录的原版文件。将它复制到记录中的原目录，改回原文件名并替换，即可恢复。每个原版的SHA256和原路径记录在包内修复清单.json。不要把不同目录中同名的main.py混用。'])
(OUT/'修复与备份'/'修复说明.md').write_text('\n'.join(lines),encoding='utf-8')
(OUT/'修复与备份'/'修复清单.json').write_text(json.dumps(rs,ensure_ascii=False,indent=2),encoding='utf-8')
with zipfile.ZipFile(OUT/'修复备份包.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted((OUT/'修复与备份').rglob('*')):
        if p.is_file():z.write(p,str(p.relative_to(OUT/'修复与备份')))
with zipfile.ZipFile(OUT/'修复备份包.zip') as z:assert z.testzip() is None
assert all(hashlib.sha256(pathlib.Path(r['source']).read_bytes()).hexdigest()==r['fixed_sha256'] for r in rs)
assert all(hashlib.sha256(pathlib.Path(r['backup']).read_bytes()).hexdigest()==r['original_sha256'] for r in rs)
print('修复包和四份原版备份完整性验证通过')
