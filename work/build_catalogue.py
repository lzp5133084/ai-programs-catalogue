import pathlib,json,collections,re,datetime,subprocess,concurrent.futures,html
BASE=pathlib.Path(__file__).resolve().parent;OUT=BASE.parent/'outputs';OUT.mkdir(exist_ok=True)
data=json.loads((BASE/'inventory.json').read_text(encoding='utf-8'))
repairs=json.loads((BASE/'repairs.json').read_text(encoding='utf-8'))
repair_map={r['source']:r for r in repairs}
checks=json.loads((BASE/'html_checks.json').read_text(encoding='utf-8'))
html_map={r.get('sha256'):r for r in checks if r.get('sha256')}
exe=json.loads((BASE/'exe_details.json').read_text(encoding='utf-8-sig'))
exe_map={r['path']:r for r in exe}
TARGET={'.html','.htm','.py','.pyw','.bat','.cmd','.ps1','.exe','.apk','.aab','.app','.jar','.vbs','.sh'}
SOURCE={'.cs','.dart','.java','.kt','.tsx','.jsx','.vue','.wxml','.js','.ts'}

def auxiliary_name(name):
    return bool(re.match(r'^(?:_|download|install|build|deploy|diag|patch|gen_|create_|extract_|test_|check_|fix_|setup|bootstrap)',name,re.I))

def clean(value):
    value=re.sub(r'\\u([0-9a-fA-F]{4})',lambda m:chr(int(m.group(1),16)),str(value or ''))
    value=re.sub(r'<[^>]*>|\{%.*?%\}|\{\{.*?\}\}', '',value)
    return re.sub(r'\s+',' ',html.unescape(value)).strip()

for r in data:
    # EXE branding identifies several installed applications and generic runtimes.
    meta=exe_map.get(r['path'],{})
    dependency_parts={'pyautogui','pynput','pyqt6','pyside6','matplotlib','numpy','scipy','pandas','pil','cv2','torch','torchaudio','transformers','cryptography','selenium','certifi','charset_normalizer','urllib3','requests','pygame','tkinter','win32com','pythonwin','setuptools','pip','pydantic','fastapi','starlette','jinja2','werkzeug','flask','sqlalchemy','onnx','onnxruntime','sounddevice','fsspec','tqdm','httpx','httpcore','anyio','sniffio','huggingface_hub','filelock','yaml'}
    if any(part.lower() in dependency_parts or re.match(r'node-v\d',part,re.I) for part in r['path'].split('\\')):r['category']='运行环境或依赖组件'
    if any(re.match(r'gradle-\d',part,re.I) for part in r['path'].split('\\')):r['category']='运行环境或依赖组件'
    if ('ByteDance' in (meta.get('company') or '') and 'webcast_mate' in r['path']) or (meta.get('product') or '').strip() in {'Electron','Git','Python 3.12.9 (64-bit)'} or '\\legend_server\\MirServer\\' in r['path']:
        r['category']='第三方软件或安装组件'
    if 'C:\\Temp\\app_extract' in r['path']:r['category']='临时解包文件'
    if r['path'] in repair_map:r['syntax']='通过（本次已修复）'
    if r.get('title'):r['title']=clean(r['title'])

OVERRIDES={
 'A35py程序集合':('Python程序集合与Excel拼音工具','目录中同时保存Python程序管理器和Excel姓名拼音首字母处理工具。','用app_manager.py管理和启动已登记程序；姓名处理使用Excel首字母标记(超级好用) - 副本.py。两者是独立入口。'),
 'A37PPTUI设计':('二维码、对话与投保界面工具','同目录包含二维码管理、双人对话与投保/理赔界面三个方向的桌面工具。','按需求分别运行二维码管理工具_增强版.py、对话程序.py或投保界面.py；先核对各自依赖。'),
 '11111':('待办精灵与AI短剧工作站','同一目录内保存待办事项工具和AI短剧生产工作站。','先按程序入口中的路径区分两个子项目，各自使用对应启动脚本或主程序；AI生产功能依赖模型/服务配置。'),
 '000001':('足球悬浮记事本与客户问卷','目录中有悬浮记事本程序、记事网页和客户问卷等独立内容。','记事本可核对dist中的足球悬浮记事本.exe；问卷使用对应网页入口。足球悬浮记事本.py已被截断，不能作为可靠启动入口。'),
 '最新项目-语音AI':('API管理、语音与家庭助手项目','同目录存放API管理、语音AI和家庭助手的多个版本与子项目。','先按程序入口中的完整路径选择子程序，再核对其模型/API和运行配置；不要把各子项目的启动文件混用。'),
 'AI_Lead_Radar_Real_v1':('保险客资雷达','将获授权的RSS、网页或API内容按地区和需求筛选，人工核对后记录与导出。','双击启动客资雷达.bat，浏览器访问 http://127.0.0.1:8765；首次按本地启动窗口提示登录，添加数据源后创建任务。'),
 '泸州保险客资雷达_电脑版':('泸州保险客资雷达','泸州保险需求信息的本地采集、人工核对、记录及导出。','进入AI_Lead_Radar_Real_v1文件夹，双击启动客资雷达.bat；浏览器访问 http://127.0.0.1:8765。'),
 'AI_Live_Assistant_V01':('女AI直播助理 V0.1','桌面助理、文字命令、动作状态和Windows本地语音播报。','运行AI_Live_Assistant_V01.exe，输入文字命令；可演示欢迎、介绍、招手、飞吻。路线文档中的后续功能不等于已经实现。'),
 'AURORA_AI_ASSISTANT_V1':('AURORA AI 助理原型','Windows桌面AI助理的初始化项目。','当前以README和源码为主，先核对编译入口与配置；尚未确认存在可直接运行的独立程序。'),
 'EQChat':('知心回复','安卓聊天回复助手，README列出两种模式及真机验收要求。','将知心回复_v0.2.0_debug.apk传到安卓手机安装；具体模式与配置先读README。未进行真机验证。'),
 'PhoneGuard':('手机使用提醒 PhoneGuard','按休息时间段触发手机使用提醒的安卓程序。','把PhoneGuard-Debug-安装包.apk传到安卓手机，按应用提示设置时间与所需权限；未做真机权限、后台及音量行为验收。'),
 'family_assistant_app':('家庭助手安卓源码','家庭助手的Android源码与构建文件。','用Android Studio打开项目，根据gradle配置构建；安装包在D:\\APK有多个版本，需先核对版本对应关系。'),
 'APK':('家庭助手安装包集合','家庭助手多个APK版本的保存目录。','选择目标版本APK传到安卓手机安装。文件名含v2、v3、release，不能仅凭名字确定最新版更可靠。'),
 'baoxianxiang':('我的数字保险箱','电脑EXE与安卓APK的私密资料管理程序，含密码、备忘录和操作记录界面。','电脑运行我的数字保险箱.exe；安卓使用app-release.apk。首次用示例资料验证，已有数据库先保留原位置并备份。'),
 '我的数字保险箱':('我的数字保险箱 V2.9','电脑端和手机端数字保险箱的分发版本。','电脑使用电脑端V2.9.exe；手机安装手机端V2.9.apk。版本迁移前备份原数据。'),
 'AI-Girl':('AI女助理小羽 / Open-LLM-VTuber集成','基于Open-LLM-VTuber的本地AI女助理项目，包含个性化界面、语音和模型配置。','优先使用桌面AI女助理小羽快捷方式或启动AI女助理.bat；需要按本地配置连接模型或API。开源基础源码不全部属于个人原创。'),
 'linshicaozuo':('本地全模态AI工作台','本地AI工作台及API、历史记录模块的集成项目。','优先使用桌面本地全模态AI工作台快捷方式；进入AI全模态工作台目录核对模型、服务和配置。'),
 'PY程序集合界面':('Python程序集合管理器','把Python工具登记到统一启动界面。','运行app_manager.py，添加程序路径与分类，再从界面启动已登记工具；移动源码会使旧路径失效。'),
 'search_programs.py':('Python程序搜索器','按功能关键词搜索Python与PYW程序，排除常见依赖并去重。','在脚本中设置search_dirs和target_features，再用Python运行；本次已修复编码、扩展名与重复路径处理。'),
 '窗口识别自动化工具':('窗口识别自动化工具','按选定窗口或屏幕区域进行识别和操作的自动化工具。','先在演示窗口选定目标与区域，设置触发规则，再启动与停止；本次未实际执行自动点击。'),
 'jilu_mobile':('应用监控助手手机端与电脑管理器','包含安卓应用监控、电脑端管理器及网页查看端。','手机安装app-debug.apk并按应用提示设置权限；电脑端使用app_monitor_client.py。联动、后台采集与权限需真机验收。'),
 'jilu':('应用使用监控助手','记录应用使用情况，并显示时长、打开顺序与频率统计。','使用项目main.py启动；本次修复01trea/main_window.py。所检查的Python环境缺少SQLAlchemy，完整界面仍需配置依赖后验证。'),
 'yijianfuzhi':('表格一键复制与语音任务工具','目录内包含表格内容复制、语音任务管理以及小程序子项目。','网页工具可先打开对应index.html；小程序需微信开发者工具导入。start.bat使用当前目录和旧默认安装路径，需进一步核对。'),
 'weixinkaifazhegongju':('智能生日助手与微信小程序','生日管理工具的桌面项目与微信小程序源码。','桌面项目进入智能生日助手子文件夹启动；小程序用微信开发者工具导入project.config.json所在目录。'),
 '批量重命名.py':('智能批量重命名执行器','根据前缀和序号规则批量改名，支持读取JSON配置或交互输入。','用Python运行，输入目录、前缀、起始编号和位数；先复制少量样本验证。当前逐个改名遇到已有目标会跳过。'),
 '修复问题':('本地API与代理诊断脚本集合','用于检测本地API与代理服务、检查连接和生成报告的维护脚本。','先阅读目标脚本再在本机运行；目录中有服务安装与修复脚本，功能范围不同。API密钥报告不适合直接录屏展示。'),
 'A18倒计时闹钟':('倒计时闹钟及多个实验版本','倒计时、时间提醒和任务完成统计的不同桌面版本。','优先选语法通过的完整文件；最终时间子目录中多份功能、界面、简洁版源码被截断，不能正常启动。'),
 'A44':('实时屏幕翻译','选定屏幕区域，识别英文后显示中文译文，提供透明度及高级设置。','配置识别与翻译服务后运行main.py；本次修复返回结果分支的缩进。外部API与实际屏幕识别仍需本机验收。'),
 'A45':('信用卡管理与文档搜索工具','目录内包含信用卡管理系统和MD/TXT文档搜索工具。','信用卡系统按其requirements和启动入口运行；本次修复web/api_integration.py中的SDK字符串。文档搜索是另一个子工具。'),
 'a16':('信用卡管理Flutter项目','信用卡管理前端与Flutter工程。','在项目根目录核对pubspec.yaml和main.dart，用Flutter构建；SDK目录与示例不属于该应用的开发成果。'),
 'a17':('信用卡管理移动端工程','目录包含移动端工程及开发环境文件。','先核对pubspec.yaml、package.json和应用入口；未确认可直接安装的当前版本。'),
 'a_ai_computer_6':('保险客户管理Web及移动端','保险客户管理的Web实现和Flutter工程。','按具体子项目启动。insurance_client_webapp.py有缩进错误，Flutter SDK源码已归为依赖，不计为个人程序。'),
 '数字生态家园':('数字生态家园','基于Python后端的数字社区网站，包含登录、管理与模板页面。','先安装项目requirements，运行app.py，并按启动输出访问本地地址；templates内HTML需要后端渲染。'),
 '资料百事通':('资料百事通','资料分享与查找服务，包含后台、收藏、详情及AI服务模块。','Python版按requirements运行app.py；另有豆包聊天目录中的HTML原型，两者需分别验收。'),
 '理赔资料助手':('理赔资料助手网页原型','整理理赔资料的网页界面与测试图片生成脚本。','先打开index.html体验界面；使用虚构的测试资料演示，实际识别和上传功能需核实配置。'),
 '20260919_163427_OPC-AI_Commander':('OPC-AI Commander V0.1','电脑端AI调度与快捷命令管理原型，包含API适配器和桌面界面。','按README使用启动入口；先用计算器等无副作用任务演示，记录本地执行结果。'),
 'Chat GPT6OPC_V2':('OPC V2桌面程序','OPC调度与电脑执行相关程序，保存了多个EXE构建。','优先使用OPC.exe或目录中已配置的桌面快捷方式；不同new、DEV、BASELINE文件是不同构建，尚未判定推荐版。'),
 'OPC_V2_REAL_TEST':('OPC测试计算器与客户管理原型','用于OPC联动测试的计算器与客户管理网页原型。','运行OPC测试计算器.exe或打开index.html，在测试环境验证桥接流程。'),
 '2026年6月22日手机APP':('短剧自动广告滑动安卓工具','ShortCutAutoPlay安卓工程和对应安装包。','用Android Studio核对源码与版本；手机安装APK后按应用提示操作。未测试自动操作、广告与后台行为。'),
}

def override(p):
    name=pathlib.PureWindowsPath(p).name
    if name in OVERRIDES:return OVERRIDES[name]
    for k in ['A44','Chat GPT6OPC_V2','A45']:
        if name.startswith(k):return OVERRIDES[k]
    return None

TOPICS=[
 ('家谱与宗亲',r'家谱|族谱|宗亲|宗族|任氏|家族', '整理与展示家族成员、宗亲服务和相关资料。','用虚构成员演示信息查看、编辑或检索，再展示保存与导出入口。'),
 ('保险与理赔',r'保险|理赔|投保|客资|身份证|工伤|伤残', '服务于保险资料、客户信息或理赔工作。','用虚构客户与示例资料完成一次录入或查询，再展示结果与导出。'),
 ('财务与资产',r'信用卡|财务|消费|记账|finance|credit.card|资产|保险箱|密码|密钥', '管理财务、消费、资产或私密资料。','用示例记录展示新增、查询和结果；私密内容用占位数据替换后录制。'),
 ('桌面自动化',r'自动点击|点击器|clicker|区域|屏幕监控|窗口识别|RPA|自动发送|浏览器自动|openclaw|龙虾', '按屏幕区域、窗口或预设规则执行桌面自动化。','选定演示窗口，配置区域与触发条件，演示启动、停止和日志。'),
 ('AI助理与调度',r'AI女|女AI|AI.*助|AI.*工作|AI.*平台|OPC|AURORA|多模型|智能体|prompt|实时生图|虚拟家园', '提供AI助理、模型调用、任务调度或生成服务的界面。','说明模型与连接状态，使用一条演示指令，再展示结果和记录。'),
 ('直播与音视频',r'直播|视频|音效|歌词|播放器|Audio2Video|音频|语音|voice|speech', '辅助直播、语音提醒或音视频内容处理。','选择短示例内容，演示主要操作，再展示播放、停止或导出结果。'),
 ('办公与文件',r'Excel|表格|OCR|复制|通讯录|文件|重命名|资料管理|搜索|PDF|PPT|工具集合|工具箱|ToolBox|工具管理|程序集合', '整理办公资料、处理文件或集中管理常用工具。','准备少量副本数据，演示处理与预览，再展示保存位置和结果。'),
 ('日历与提醒',r'生日|日历|倒计时|提醒|闹钟|待办|记事本|notes|calendar', '记录事项并提供日历、倒计时或提醒功能。','新增一条示例事项，设置短时间提醒，再展示保存、完成和历史记录。'),
 ('网站与业务原型',r'网站|门户|个人|客户|社区|邻里|土特产|岗位|招聘|宠拉拉|交通|产品经理|名片|二维码|问卷|资源|幸运|抽奖|座位|成长站|管理', '提供对应业务的信息展示、管理或交互界面。','浏览主要页面，选择一个示例流程操作，再展示结果和未实现入口。'),
]
def topic(name,purpose=''):
    for label,pattern,desc,demo in TOPICS:
        if re.search(pattern,name+' '+purpose,re.I):return label,desc,demo
    return '其他开发工具','用途需要结合项目说明与运行界面继续核实。','先展示启动入口、界面和源码可确认的功能，再记录尚需核实的操作。'

def precise_purpose(name,fallback):
    descriptions=[
      (r'Excel.*首字母|名字拼音','读取Excel姓名，将名字转换为拼音首字母并输出处理结果。'),
      (r'Excel.*列对齐|列对齐工具','对齐Excel表格的列，提供数据预览，减少手工调整。'),
      (r'Excel.*排序|字母彩色排序','按字母与配色规则整理Excel表格内容。'),
      (r'OCR|证件识别|信息提取','从图片、证件或文本提取结构化信息，辅助整理与表格录入；实际识别效果需验收。'),
      (r'通讯录转换','将通讯录内容转为方便整理姓名与电话的格式。'),
      (r'通讯录管理','在界面中查看和管理联系人记录。'),
      (r'二维码|多码集|QR 工坊','创建、管理或展示二维码，服务于名片和信息分享。'),
      (r'桌面文件整理|一键清理桌面','按文件类型整理桌面文件，减少桌面散乱。'),
      (r'保险文件收集','从指定目录收集保险相关文件，减少手工查找。'),
      (r'文件内容搜索|包含字段|文件查找','按文件名、内容或关键词查找本地资料。'),
      (r'保险客户记录','登记保险客户、保单/保险类型、待办与服务跟进信息。'),
      (r'客户资料.*管理|客户信息.*管理','管理客户资料与附件，辅助查询和日常服务跟进。'),
      (r'客户关系管理|知遇','记录客户关系与服务事项，支持日常跟进。'),
      (r'语音提醒|语音播报','保存提醒内容并用语音播报，在约定条件下提醒事项。'),
      (r'语音命令发布','将语音识别为命令，发送给配置的开发工具或执行端。'),
      (r'倒计时|闹钟','设置倒计时与时间提醒，部分版本包含任务完成记录。'),
      (r'日历事件','按日期查看、添加和管理日历事件。'),
      (r'生日助手','管理生日信息与生日提醒，包含桌面或移动端版本。'),
      (r'歌词','桌面显示与编辑歌词或歌曲相关文字，辅助直播演唱。'),
      (r'足球.*记事本|智能记事本','通过悬浮窗口记录事项，部分版本包含提醒和历史记录。'),
      (r'实时屏幕翻译','识别选定屏幕区域的文字并显示翻译结果。'),
      (r'窗口识别|屏幕监控|区域.*监控|自动点击|点击器','识别指定窗口或屏幕区域，并按配置触发点击或相关操作。'),
      (r'应用.*监控|应用使用','记录和查看应用使用时长、打开顺序或使用频率。'),
      (r'直播.*资源看板|资源看板','在控制端编辑直播嘉宾或资源信息，在展示端显示。'),
      (r'直播.*背景','调整直播背景与展示效果，供直播画面使用。'),
      (r'PK直播|灵魂拷问','提供直播互动问答和PK场景所用的界面。'),
      (r'音效效果器|声纹','处理音效或识别语音/声纹，辅助直播互动。'),
      (r'Audio2Video|音频转视频','把音频与画面组合为视频；需要对应服务与编码工具。'),
      (r'短视频智能|VideoForge|短剧.*工作站','提供视频或短剧制作流程的操作界面，实际生成依赖配置的服务。'),
      (r'霓虹边框','为图片或选定画面增加边框与视觉强调效果。'),
      (r'泸州任氏|任氏宗族|家谱|族谱','展示宗亲资料与家族关系，服务于族谱整理、寻根和宗亲交流。'),
      (r'土特产|Earth Local','展示不同地区的土特产信息与相关页面。'),
      (r'亲子沟通','展示亲子沟通主题内容与成长建议的网页原型。'),
      (r'社区共享|社区互助|邻里|社区微循环','展示社区互助、物品共享或物业服务流程；后端与交易闭环需验收。'),
      (r'产品经理|产品管理|PM Assistant','组织产品需求、开发流程、进度或验收信息。'),
      (r'岗位.*筛选','提供岗位需求筛选与管理端/用户端展示。'),
      (r'宠拉拉|宠拉拉|宠物货拉拉','展示宠物运输业务的用户、司机和管理端界面。'),
      (r'财务资产|信用卡|消费.*监控|记账','整理财务、消费或信用卡记录，辅助查看账单与统计。'),
      (r'军哥懂保|任军学|个人主页|个人简介|展示门户|GEO','展示个人、保险服务或数字资产信息，支持个人品牌传播。'),
      (r'工具集合|工具箱|ToolBox|程序集合管理','把多个常用工具组织到统一界面，便于选择和启动。'),
      (r'个人运势|小六壬','输入相关信息并展示文化娱乐性质的分析或解读界面。'),
      (r'API.*管理|API渠道','登记和管理模型/API渠道与调用配置。'),
    ]
    for pattern,desc in descriptions:
        if re.search(pattern,name,re.I):return desc
    return fallback

def provenance(p,rs):
    if '\\Documents\\Codex\\' in p:return 'Codex工作目录','Codex（目录证据）'
    if '\\Doubao\\chats\\' in p or '.super_doubao' in p:return '豆包开发工作目录','豆包（目录证据）'
    if '\\.trae-cn\\' in p:return 'TRAE保存目录','TRAE（目录证据）'
    if '\\.minimax\\workspace' in p:return 'MiniMax工作目录','MiniMax（目录证据）'
    if 'Chat GPT6' in p:return 'ChatGPT命名目录，归属待核实','ChatGPT（目录命名）'
    if 'deepseek' in p.lower():return 'DeepSeek命名文件，归属待核实','DeepSeek（文件命名）'
    if pathlib.Path(p).is_dir() and (pathlib.Path(p)/'.trae').exists():return '存在TRAE配置，归属待核实','TRAE（配置证据）'
    return '个人开发候选，生成工具待核实','待核实'

def date_from_name(p):
    m=re.search(r'(20\d{2})(?:年|-|nian)(\d{1,2})(?:月|-|yue)(\d{1,2})(?:日|ri|\b)',p)
    if not m:m=re.search(r'(20\d{2})(\d{2})(\d{2})[_-]',p)
    if m:
        try:return datetime.date(*map(int,m.groups())).isoformat()
        except ValueError:pass
    return None

def git_info(p):
    root=pathlib.Path(p)
    if not root.is_dir() or not (root/'.git').exists():return {}
    try:
        cmd=['git','-C',str(root),'log','--reverse','--format=%aI%x09%s']
        r=subprocess.run(cmd,capture_output=True,encoding='utf-8',errors='replace',timeout=10)
        if r.returncode==0 and r.stdout.strip():
            date,subject=r.stdout.splitlines()[0].split('\t',1);return {'git_date':date[:10],'git_subject':subject[:150]}
    except Exception:pass
    return {}

groups=collections.defaultdict(list)
for r in data:
    if r['category']=='开发候选':groups[r['project']].append(r)
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:git_records=dict(zip(groups,pool.map(git_info,groups)))
programs=[];projects=[];issues=[]
for r in repairs:
    issues.append({'kind':'已修复','path':r['source'],'problem':r['reason'],'action':r['tests'],'status':'已写回原路径；有原版备份','backup':r['backup'],'repaired_copy':r['repaired_copy']})

for p,rs in groups.items():
    targets=[r for r in rs if r['extension'] in TARGET|SOURCE]
    if not targets:continue
    ov=override(p)
    titles=list(dict.fromkeys(clean(r.get('title')) for r in rs if r.get('title')))
    headings=[clean(r.get('heading')) for r in rs if r.get('heading')]
    pack=[r['package'] for r in rs if r.get('package')]
    name=ov[0] if ov else (titles[0].split(' / ')[0][:100] if titles else (pack[0].get('description') or pack[0].get('name') if pack else pathlib.PureWindowsPath(p).name))
    name=clean(name) or pathlib.PureWindowsPath(p).name
    category,desc,demo=topic(name+' '+p)
    purpose=ov[1] if ov else precise_purpose(name,desc)
    evidence='页面/窗口标题：'+('；'.join(titles[:6]) if titles else '未提取到标题')
    if headings:evidence+='；项目说明：'+headings[0][:200]
    ai,tool=provenance(p,rs)
    directory_date=date_from_name(p)
    git=git_records.get(p,{})
    source_dates=[min(r['modified'][:10],r.get('created',r['modified'])[:10]) for r in targets if r.get('modified') and r['modified'][:10]>='2020-01-01' and r['extension'] not in {'.exe','.apk','.jar'}]
    all_dates=[min(r['modified'][:10],r.get('created',r['modified'])[:10]) for r in targets if r.get('modified') and r['modified'][:10]>='2020-01-01']
    if directory_date:date=directory_date;date_basis='目录/文件命名日期（推定）'
    elif git.get('git_date') and git['git_date']>='2025-01-01' and 'AI-Girl' not in p:date=git['git_date'];date_basis='仓库最早提交（可能早于个人改造）'
    else:date=min(source_dates or all_dates or ['']);date_basis='文件创建/修改较早时间（推定）'
    if p.endswith('\\AI-Girl'):
        dates=[r['modified'][:10] for r in rs if r.get('modified') and (r['name']=='启动AI女助理.bat' or r['path'].endswith('\\frontend\\index.html'))]
        if dates:date=min(dates);date_basis='本地启动器/定制界面修改日期（推定）'
    if p.endswith('\\ai-tools'):
        dates=[r['modified'][:10] for r in rs if r.get('modified') and 'AI 资产总览' in r.get('title','')]
        if dates:date=min(dates);date_basis='本地资产总览页面修改日期（推定）'
    launchers=[r for r in targets if r['extension'] in {'.bat','.cmd','.vbs'} and re.search(r'启动|start|run',r['name'],re.I) and not re.search(r'build|install|test|deploy|download|clean',r['name'],re.I)]
    binaries=[r for r in targets if r['extension']=='.exe']
    mainpy=[r for r in targets if r['extension'] in {'.py','.pyw'} and r.get('main_guard') and not r.get('syntax','').startswith('语法错误') and not auxiliary_name(r['name'])]
    mainpy.sort(key=lambda r:(0 if r['name'].lower() in {'main.py','app.py','app_manager.py'} else 1 if r.get('title') else 2,r['name']))
    htmls=[r for r in targets if r['extension'] in {'.html','.htm'} and not any(x in r['path'].lower().split('\\') for x in ['templates','test','tests','docs'])]
    candidates=launchers or binaries or mainpy or htmls or targets
    entry=next((r for r in candidates if r['name'].lower() in {'start.bat','启动客资雷达.bat','main.py','app.py','index.html'}),candidates[0])
    if ov:usage=ov[2]
    elif entry['extension'] in {'.bat','.cmd','.vbs','.exe'}:usage='在原目录使用 '+entry['name']+'；脚本运行前核对其功能与配置，保留同目录依赖和数据。'
    elif entry['extension'] in {'.py','.pyw'}:usage='先核对项目requirements和配置，再在程序目录运行 '+entry['name']+'；不应单独移走源码文件。'
    elif entry['extension'] in {'.html','.htm'}:usage='先用浏览器打开 '+entry['name']+'；如果有后端或构建配置，按项目说明启动服务后访问页面。'
    elif entry['extension'] in {'.apk','.aab'}:usage='将APK传到安卓设备按提示安装；AAB需开发工具构建分发。手机权限和后台行为尚未验证。'
    else:usage='源码工程；用项目对应的开发工具打开，核对构建配置和主入口后运行。'
    bad=[r for r in rs if r.get('syntax','').startswith('语法错误')]
    repaired=[r for r in repairs if r['source'] in {s['path'] for s in rs}]
    html_bad=[r for r in rs if html_map.get(r.get('sha256'),{}).get('errors')]
    if bad:status=f'存在{len(bad)}份语法错误源码；运行待验收'
    elif repaired:status='已修复部分源码；完整运行待验收'
    elif html_bad:status='网页脚本有检查异常；需核对'
    else:status='静态整理完成；运行待验收'
    project={'id':'','order':0,'date':date,'date_basis':date_basis,'name':name,'category':category,'purpose':purpose,'role':'解决的工作：'+purpose,'features':evidence,'usage':usage,'entry':entry['path'],'path':p,'tool':tool,'ai_evidence':ai,'status':status,'files':len(targets),'types':' / '.join(k.lstrip('.').upper() for k in sorted({r['extension'] for r in targets})),'git_date':git.get('git_date',''),'demo':demo,'video_status':'待录制','notes':'同目录不同文件可能是历史版本或不同子程序；详见程序入口与文件明细。'}
    if 'AI-Girl' in p or p.endswith('\\ai-tools'):project['ai_evidence']='本地部署/集成，含大量第三方基础源码'
    projects.append(project)
    selected=[]
    for r in targets:
        ext=r['extension'];namefile=r['name'];parts=[x.lower() for x in r['path'].split('\\')]
        is_entry=(ext in {'.html','.htm'} and 'templates' not in parts and 'docs' not in parts) or ext in {'.exe','.apk','.aab','.bat','.cmd','.ps1','.vbs','.sh'} or (ext in {'.py','.pyw'} and (r.get('main_guard') or r.get('title') or r.get('syntax','').startswith('语法错误')))
        if is_entry:selected.append(r)
    if not selected:selected=[entry]
    for r in selected:
        title=clean(r.get('title'))
        nm=title.split(' / ')[0][:120] if title else (project['name'] if r is entry else r['name'])
        ext=r['extension'];state='未做完整运行验证';typ=''
        if ext in {'.html','.htm'}:
            typ='网页';use='浏览器打开此HTML；存在服务或构建配置时按项目说明运行。'
            hc=html_map.get(r.get('sha256'),{})
            if hc.get('errors'):state='脚本检查异常：'+' / '.join(hc['errors'])
            elif hc.get('missing_scripts'):state='引用脚本文件缺失：'+' / '.join(hc['missing_scripts'])
            elif hc.get('checked'):state='内联JS语法检查通过；交互未验收'
            if hc.get('template_skipped'):state+='；模板脚本需服务渲染'
        elif ext in {'.py','.pyw'}:
            typ='Python工具/辅助脚本' if auxiliary_name(r['name']) else 'Python主入口' if r.get('main_guard') else 'Python界面/模块'
            use=('按项目需要运行此辅助脚本；通常不作为软件主窗口的启动入口。' if auxiliary_name(r['name']) else '在原目录用Python运行此文件；核对requirements和配置。' if r.get('main_guard') else '此文件可能由主程序调用；从项目主入口启动，不能保证单独运行。')
            state=r.get('syntax','未取得语法检查结果')+'；完整运行未验收'
        elif ext=='.exe':typ='Windows程序';use='在原目录双击EXE；保留配套DLL、资源和数据文件。'
        elif ext in {'.apk','.aab'}:typ='安卓包';use='APK传到安卓设备按提示安装；AAB通过开发工具分发；本次未装机。'
        elif ext in {'.bat','.cmd','.ps1','.vbs','.sh'}:
            typ='启动/维护脚本';use='先阅读脚本用途，再用对应Windows命令环境或Shell运行；不是所有脚本都是软件启动器。'
            if r.get('relative_launch') and not r.get('sets_cwd'):state='使用相对路径但未固定工作目录，可能启动失败'
            if r.get('dangerous'):state+='；包含删除或系统维护操作，未执行'
        else:typ='源码工程';use=project['usage']
        if r['path'] in repair_map:state='本次已修复并写回；完整运行未验收'
        program={'id':'','order':0,'date':date_from_name(r['path']) or (date if r['path'] in repair_map or p.endswith('\\AI-Girl') or p.endswith('\\ai-tools') else min(r.get('modified','')[:10],r.get('created',r.get('modified',''))[:10])) or date,'date_basis':'文件/目录日期，推定顺序','name':nm,'project_name':project['name'],'project_path':p,'category':category,'type':typ,'purpose':project['purpose'] if r is entry or not title else precise_purpose(nm,topic(nm+' '+p)[1]), 'features':'；'.join(clean(v) for v in r.get('features',[])[:12]) or '源码窗口/页面标题：'+(title or r['name']), 'usage':use,'path':r['path'],'tool':tool,'status':state,'duplicate_paths':[],'demo':topic(nm+' '+p)[2],'video_status':'待录制','sha256':r.get('sha256',''),'size':r.get('size',0)}
        programs.append(program)
    for r in bad:
        alternatives=[s['path'] for s in rs if s['extension'] in {'.py','.pyw'} and s.get('syntax','').startswith('通过') and s.get('main_guard')][:3]
        action='核对原始生成记录与同目录完整版本；被截断的文件需补齐缺失功能，再做功能测试。'
        if alternatives:action+=' 同项目可先核对的语法通过入口（不保证功能相同）：'+'；'.join(alternatives)
        issues.append({'kind':'Python语法错误','path':r['path'],'problem':r['syntax'],'action':action,'status':'未修复；需逐项处理','backup':''})

# Consolidate truly byte-identical text entries; keep every original path in file detail.
unique={};merged=[]
for r in programs:
    key=(r['sha256'],r['type']) if r['sha256'] else ('path',r['path'])
    if key in unique:
        keep=unique[key];keep['duplicate_paths'].append(r['path']);keep['date']=min(keep['date'],r['date'])
    else:unique[key]=r;merged.append(r)
programs=merged
projects.sort(key=lambda r:(r['date'] or '9999',r['name'],r['path']))
for i,r in enumerate(projects,1):r['id']=f'PJ{i:03d}';r['order']=i
programs.sort(key=lambda r:(r['date'] or '9999',r['name'],r['path']))
for i,r in enumerate(programs,1):r['id']=f'APP{i:04d}';r['order']=i
for check in checks:
    if check.get('errors'):
        issues.append({'kind':'网页脚本检查异常','path':check['path'],'problem':' / '.join(check['errors']),'action':'核对模板、JSX或浏览器脚本语法；静态检查异常不直接等同于整站无法运行。','status':'待核对','backup':''})
    if check.get('missing_scripts'):
        issues.append({'kind':'网页本地脚本缺失','path':check['path'],'problem':' / '.join(check['missing_scripts']),'action':'找回引用脚本，或使用原项目构建/服务入口；不能只复制HTML。','status':'待核对','backup':''})

tools=[]
shortcuts=json.loads((BASE/'desktop_shortcuts.json').read_text(encoding='utf-8-sig'))
for s in shortcuts:
    if re.search(r'Trae|TRAE|Doubao|豆包|千问|扣子|Ollama|微信开发者|AI女助理|本地全模态|AI全模态|OPC',s['Name']):
        path=s['Target'] or s['WorkingDirectory']
        tools.append({'name':s['Name'],'path':path,'workdir':s['WorkingDirectory'],'status':'存在' if path and pathlib.Path(path).exists() else '入口需进一步核对','purpose':'开发/模型/应用启动工具；快捷方式存在不证明每份代码均由它生成。'})
for name,path,role in [('Python 3.12',r'D:\Python312\python.exe','Python源码运行环境'),('Node.js',r'D:\Program Files\nodejs\node.exe','JavaScript与网页项目构建环境'),('Git',r'D:\Program Files\Git\cmd\git.exe','版本记录工具'),('Android Studio',r'D:\Android Studio\bin\studio64.exe','Android项目开发工具')]:
    tools.append({'name':name,'path':path,'workdir':'','status':'存在' if pathlib.Path(path).exists() else '未在此路径确认','purpose':role})

relevant=[r for r in data if r['category'] in {'开发候选','收到或下载的程序，作者待核实'} and r['extension'] in TARGET|SOURCE]
files=[]
for r in data:
    files.append({k:r.get(k,'') for k in ['name','path','extension','category','project','size','created','modified','syntax','read_error','sha256']})
scope=json.loads((BASE/'scan_scope.json').read_text(encoding='utf-8'))
scope['supplement']='补扫C盘用户主目录、豆包聊天目录和部分Android/Flutter/C#源码；主目录访问受限后使用只读权限补查。'
scope['limits']='未扫描排除的Windows、Program Files、系统与依赖目录；压缩包内部内容和WSL虚拟磁盘未完整展开；隐藏/受保护目录、临时模型与测试缓存存在少量拒绝访问。下载/收到的文件不自动认定为个人开发。'
scope['timeline']='按推定开发时间排序。目录命名日期、仓库最早提交、文件最早修改时间均不能完整还原AI对话中的开发顺序，复制、解压、第三方仓库与修复会影响时间。'
counts={'scan_records':len(data),'projects':len(projects),'program_entries':len(programs),'relevant_files':len(relevant),'repaired_files':len(repairs),'remaining_python_syntax_errors':sum(i['kind']=='Python语法错误' for i in issues),'html_check_alerts':sum(i['kind']=='网页脚本检查异常' for i in issues),'duplicate_source_entries':sum(len(r['duplicate_paths']) for r in programs),'categories':dict(collections.Counter(r['category'] for r in data))}
bundle={'as_of':'2026-10-15','counts':counts,'scope':scope,'projects':projects,'programs':programs,'issues':issues,'tools':tools,'files':files,'relevant_files':[{k:r.get(k,'') for k in ['name','path','extension','category','project','size','created','modified','syntax','read_error','sha256']} for r in relevant]}
(BASE/'catalogue_data.json').write_text(json.dumps(bundle,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'全部文件索引.json').write_text(json.dumps({'as_of':bundle['as_of'],'counts':counts,'scope':scope,'files':files},ensure_ascii=False,indent=2),encoding='utf-8')
report=['# 电脑AI开发程序整理记录','',f"整理日期：2026-10-15。扫描记录 {counts['scan_records']} 条，项目/目录候选 {counts['projects']} 个，可展示的程序/脚本入口 {counts['program_entries']} 条。入口按内容哈希合并完全一致的文本副本；不能据此认定全部为原创、全部由AI生成或全部可以运行。",'',scope['timeline'],'',scope['limits'],'','## 已修复并写回原路径','']
for r in repairs:report += [f"- {r['source']}：{r['reason']} 测试：{r['tests']}。原版备份：{r['backup']}。"]
report += ['','修复共通过8项针对性检查。GUI、真实数据库、外部API、摄像头/自动点击和安卓真机未完整验收；应用监控项目尚缺SQLAlchemy依赖。','','## 后续使用视频','', '每个目录与程序入口都已有演示提纲及“待录制”状态。建议先录已能启动、输入输出清楚的工具；存在语法错误或缺配置的项目先修复、验收。录制时使用示例客户、示例文件和占位凭证。','','建议成片顺序：10秒说明用途，20秒说明启动与准备，60至120秒演示一个完整场景，20秒展示输出与保存位置，10秒说明当前限制。界面预览不能代替真实运行演示。','','## 时间顺序项目索引','']
for r in projects:report += [f"{r['order']}. **{r['name']}**（{r['date'] or '日期待核实'}，{r['date_basis']}）  ", f"   用途：{r['purpose']}  ", f"   使用：{r['usage']}  ",f"   工具：{r['tool']}；状态：{r['status']}  ",f"   路径：{r['path']}",'']
(OUT/'整理说明与开发顺序.md').write_text('\n'.join(report),encoding='utf-8')
print(json.dumps(counts,ensure_ascii=False))
