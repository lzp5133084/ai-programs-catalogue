import pathlib,json,ast,tempfile,contextlib,io,datetime,types
BASE=pathlib.Path(__file__).resolve().parent
repairs=json.loads((BASE/'repairs.json').read_text(encoding='utf-8'))
checks=[]
for r in repairs:
    ast.parse(pathlib.Path(r['repaired_copy']).read_text(encoding='utf-8'))
    checks.append({'source':r['source'],'check':'完整源码可解析','passed':True})

api=next(r for r in repairs if pathlib.Path(r['source']).name=='api_integration.py')
tree=ast.parse(pathlib.Path(api['repaired_copy']).read_text(encoding='utf-8'))
value=next(n.value.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='API_EXAMPLE_CODE' for t in n.targets))
ast.parse(value); assert 'class CreditCardAPIClient' in value and '获取访问令牌' in value
checks.append({'source':api['source'],'check':'内嵌SDK可解析且内容保留','passed':True})

search=next(r for r in repairs if pathlib.Path(r['source']).name=='search_programs.py')
namespace={'__name__':'repair_test'}
exec(compile(pathlib.Path(search['repaired_copy']).read_text(encoding='utf-8'),search['repaired_copy'],'exec'),namespace)
namespace['chardet']=None
with tempfile.TemporaryDirectory(dir=BASE) as td:
    root=pathlib.Path(td); sub=root/'子目录';sub.mkdir(); deps=root/'node_modules';deps.mkdir()
    texts=[('utf8.PY','utf-8'),('utf16.pyw','utf-16'),('中文.py','gb18030')]
    for name,enc in texts:
        (sub/name).write_bytes(('"""二维码工具"""\nimport os\n').encode(enc))
    (deps/'vendor.py').write_text('"""二维码工具"""',encoding='utf-8')
    with contextlib.redirect_stdout(io.StringIO()):
        results=namespace['search_py_programs'](['二维码'],[str(root),str(sub)])
    assert len(results)==3,(len(results),[x['path'] for x in results])
    assert len(set(x['path'] for x in results))==3
    assert all('node_modules' not in x['path'] for x in results)
    for name,enc in texts:
        with contextlib.redirect_stdout(io.StringIO()): content=namespace['read_file_content'](str(sub/name))
        assert '二维码工具' in content
checks.append({'source':search['source'],'check':'三种编码、PY/PYW、大小写、重复路径、依赖排除','passed':True})

screen=next(r for r in repairs if 'A44' in r['source'])
tree=ast.parse(pathlib.Path(screen['repaired_copy']).read_text(encoding='utf-8'))
method=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and any(isinstance(x,ast.Constant) and isinstance(x.value,str) and '火山引擎API返回完整结果' in x.value for x in ast.walk(n)))
# Execute only the already inspected response-parsing branch; all HTTP and credentials stay outside the test.
branch=next(n for n in ast.walk(method) if isinstance(n,ast.If) and 'choices' in ast.unparse(n.test))
testfn=ast.FunctionDef(name='parse_result',args=ast.arguments(posonlyargs=[],args=[ast.arg(arg='result')],vararg=None,kwonlyargs=[],kw_defaults=[],kwarg=None,defaults=[]),body=[branch],decorator_list=[])
testmod=ast.fix_missing_locations(ast.Module(body=[testfn],type_ignores=[]))
env={'logger':types.SimpleNamespace(info=lambda *a:None,error=lambda *a:None)};exec(compile(testmod,'response_test','exec'),env)
assert env['parse_result']({'choices':[{'message':{'content':'  翻译文本  '}}]})=='翻译文本'
assert env['parse_result']({'choices':[]})=='[翻译结果格式异常]'
assert env['parse_result']({})=='[翻译结果格式异常]'
checks.append({'source':screen['source'],'check':'模拟翻译成功、空choices、缺少choices分支','passed':True})

usage=next(r for r in repairs if pathlib.Path(r['source']).name=='main_window.py')
tree=ast.parse(pathlib.Path(usage['repaired_copy']).read_text(encoding='utf-8'))
fn=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='update_stats')
class Expr:
    def __init__(self,name):self.name=name
    def __ge__(self,other):return ('gte',self.name,other)
    def label(self,name):return self
    def desc(self):return ('desc',self.name)
class Query:
    def __init__(self,args):self.args=args;self.calls=[]
    def filter(self,v):self.calls.append(('filter',v));return self
    def group_by(self,v):self.calls.append(('group',v));return self
    def order_by(self,v):self.calls.append(('order',v));return self
    def all(self):return self.calls
queries=[]
db=types.SimpleNamespace(query=lambda *args: queries.append(Query(args)) or queries[-1])
model=types.SimpleNamespace(**{k:Expr(k) for k in ['app_name','active_duration','start_time','end_time','id']})
func=types.SimpleNamespace(sum=lambda e:Expr('sum('+e.name+')'),count=lambda e:Expr('count('+e.name+')'))
env={'db':db,'AppUsage':model,'func':func,'start_of_day':datetime.datetime(2026,10,15)}
for stmt in fn.body:
    if isinstance(stmt,ast.Assign) and any(isinstance(t,ast.Name) and t.id in {'duration_data','order_data','frequency_data'} for t in stmt.targets):
        exec(compile(ast.Module(body=[stmt],type_ignores=[]),'query_test','exec'),env)
assert len(queries)==3
assert [k for k,v in queries[0].calls]==['filter','group','order']
assert [k for k,v in queries[1].calls]==['filter','order']
assert [k for k,v in queries[2].calls]==['filter','group','order']
checks.append({'source':usage['source'],'check':'三处统计查询构造及日期过滤（模拟数据库，非真实SQL执行）','passed':True})
(BASE/'repair_test_results.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'checks_passed':len(checks),'checks':checks},ensure_ascii=False))
