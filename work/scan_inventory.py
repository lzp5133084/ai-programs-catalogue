import concurrent.futures, subprocess, pathlib, json, time

BASE = pathlib.Path(__file__).resolve().parent
RG = r'C:\Users\Administrator\AppData\Local\OpenAI\Codex\bin\5cb96978b0b525f8\rg.exe'
EXTS = ['html','htm','py','pyw','bat','cmd','ps1','exe','apk','aab','app','jar','vbs','sh']
MARKERS = ['package.json','requirements*.txt','pyproject.toml','README*','readme*','AGENTS.md','build.gradle*','AndroidManifest.xml','pubspec.yaml','*.spec','*.sln','*.csproj','project.config.json','index.js','main.js','main.ts','App.tsx','App.vue','app.json','*.kt']
EXCLUDED = ['Windows','Program Files','Program Files (x86)','ProgramData','$RECYCLE.BIN','$Recycle.Bin','System Volume Information','Recovery','Boot','Drivers','AMD','WindowsApps','WpSystem','node_modules','site-packages','.venv','venv','__pycache__','.git','.pnpm-store','.gradle','.m2','.cache','codex-runtimes','Library','Lib','libs','Chrome','Edge','GPUCache','Cache','Code Cache','IndexedDB','Service Worker','anaconda3','miniconda3']

def scan(drive):
    cmd = [RG,'--files','--hidden','--no-ignore','--glob-case-insensitive']
    for ext in EXTS: cmd += ['-g','*.'+ext]
    for marker in MARKERS: cmd += ['-g',marker]
    for name in EXCLUDED: cmd += ['-g','!**/'+name+'/**']
    cmd += ['-g','!**/Documents/Codex/2026-10-15/new-chat/**',drive+'\\']
    start = time.time()
    with (BASE/(drive[0]+'_files.txt')).open('w',encoding='utf-8') as out, (BASE/(drive[0]+'_errors.txt')).open('w',encoding='utf-8') as err:
        proc = subprocess.run(cmd,stdout=out,stderr=err,encoding='utf-8',errors='replace')
    paths = (BASE/(drive[0]+'_files.txt')).read_text(encoding='utf-8').splitlines()
    result = {'drive':drive,'seconds':round(time.time()-start,1),'files':len(paths),'exit_code':proc.returncode}
    print(json.dumps(result,ensure_ascii=False),flush=True)
    return result

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    results = list(pool.map(scan,['C:','D:','E:']))
(BASE/'scan_scope.json').write_text(json.dumps({'results':results,'excluded_directory_names':EXCLUDED,'extensions':EXTS,'supplementary_markers':MARKERS},ensure_ascii=False,indent=2),encoding='utf-8')
