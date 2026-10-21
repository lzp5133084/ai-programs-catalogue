import fs from 'node:fs/promises';
import path from 'node:path';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const base=path.dirname(new URL(import.meta.url).pathname).replace(/^\/([A-Z]:)/i,'$1');
const data=JSON.parse(await fs.readFile(path.join(base,'catalogue_data.json'),'utf8'));
const output=path.join(base,'..','outputs','程序清单');await fs.mkdir(output,{recursive:true});
const wb=Workbook.create();
const names=['项目目录','程序入口','视频计划','文件明细','问题与修复','开发工具'];
const sheets=Object.fromEntries(names.map(n=>[n,wb.worksheets.add(n)]));
const date=v=>v?new Date(v.slice(0,10)+'T00:00:00Z'):null;
const literal=v=>typeof v==='string'&&v.startsWith('=')?"'"+v:v??'';
function addSheet(name,title,note,headers,rows,widths,dateCols=[]){
 const s=sheets[name],n=rows.length+6,last=String.fromCharCode(64+headers.length);
 s.showGridLines=false;s.getRange(`A1:${last}${n}`).format.font={name:'Arial',size:10,color:'#1C2F43'};
 s.getRange('A2').values=[[title]];s.getRange('A2').format.font={name:'Arial',size:14,bold:true,color:'#183B56'};
 s.getRange('A3').values=[[note]];s.getRange('A3').format.font={name:'Arial',size:10,italic:true,color:'#62758A'};
 s.getRange(`A6:${last}6`).values=[headers];
 if(rows.length)s.getRange(`A7:${last}${n}`).values=rows.map(r=>r.map(literal));
 s.getRange(`A6:${last}6`).format={fill:'#203E5B',font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},rowHeight:28,verticalAlignment:'center',horizontalAlignment:'center',wrapText:true};
 s.getRange(`A7:${last}${n}`).format.wrapText=true;s.getRange(`A7:${last}${n}`).format.verticalAlignment='top';
 s.getRange(`A7:${last}${n}`).format.rowHeight=30;
 widths.forEach((w,i)=>s.getRangeByIndexes(0,i,n,1).format.columnWidth=w);
 for(const col of dateCols)s.getRange(`${col}7:${col}${n}`).setNumberFormat('yyyy-mm-dd');
 const table=s.tables.add(`A6:${last}${n}`,true,'T'+names.indexOf(name)+'Inventory');table.style='TableStyleMedium2';table.showFilterButton=true;
 for(let i=0;i<rows.length;i++){
   const lines=Math.max(1,...rows[i].map((v,c)=>{if(typeof v!=='string')return 1;return Math.max(...v.split('\n').map(t=>Math.ceil([...t].reduce((n,ch)=>n+(ch.charCodeAt(0)>255?2:1),0)/Math.max(8,widths[c]-2))))}));
   s.getRangeByIndexes(i+6,0,1,headers.length).format.rowHeight=Math.max(26,lines*13+7);
 }
 s.freezePanes.freezeRows(6);s.freezePanes.freezeColumns(name==='文件明细'?1:3);
 return s;
}
addSheet('项目目录','AI开发项目目录','截至2026-10-15。按推定开发时间排序；目录候选不能证明全部由AI生成或已经可用。',
 ['顺序','推定开发时间','名称','类别','用途与作用','使用方式','项目路径','工具证据','检查状态','文件形式','时间依据','源码功能证据','使用视频提纲','AI归属依据','启动入口'],
 data.projects.map(r=>[r.order,date(r.date),r.name,r.category,r.purpose,r.usage,r.path,r.tool,r.status,r.types,r.date_basis,r.features,r.demo,r.ai_evidence,r.entry]),
 [7,15,40,20,55,65,100,30,48,26,40,90,65,45,100],['B']);
addSheet('程序入口','程序、脚本与历史入口','按文件/目录日期推定顺序。完全一致的文本副本合并；所有原路径保留在文件明细中。',
 ['顺序','推定时间','名称','形式','所属项目','用途','使用方式','当前检查','原路径','其他完全相同副本','工具证据','可见功能','程序编号'],
 data.programs.map(r=>[r.order,date(r.date),r.name,r.type,r.project_name,r.purpose,r.usage,r.status,r.path,r.duplicate_paths.join('\n'),r.tool,r.features,r.id]),
 [7,15,42,24,40,55,65,65,100,100,30,80,16],['B']);
addSheet('视频计划','程序使用与应用视频计划','先验收再录制；用示例文件、虚构客户和占位凭证。黄色状态列可以修改。',
 ['顺序','程序编号','程序名称','演示内容','准备与录制限制','录制状态','原程序路径','程序形式','检查状态'],
 data.programs.map(r=>[r.order,r.id,r.name,r.demo,/脚本/.test(r.type)?'先审查脚本用途，维护脚本可并入项目演示。':'说明用途和启动；演示一个完整场景；展示结果、保存位置和当前限制。','待录制',r.path,r.type,r.status]),
 [7,16,44,70,65,20,100,24,75]);
const vid=sheets['视频计划'];const vn=data.programs.length+6;
vid.getRange(`F7:F${vn}`).dataValidation={rule:{type:'list',values:['待录制','待修复/验收','录制中','已完成']}};
vid.getRange(`F7:F${vn}`).format.fill='#FFF0BF';
addSheet('文件明细','相关源码与程序文件','包含开发候选与收到/下载文件；作者不确定的文件单独标注。全部扫描记录另存JSON索引。',
 ['文件名','形式','归类','所属目录','完整路径','大小（KB）','创建时间','修改时间','语法/读取状态','内容SHA256'],
 data.relevant_files.map(r=>[r.name,r.extension,r.category,r.project,r.path,typeof r.size==='number'?r.size/1024:null,date(r.created),date(r.modified),r.syntax||r.read_error||'未做运行验证',r.sha256]),
 [44,12,34,100,110,15,15,15,75,72],['G','H']);
sheets['文件明细'].getRange(`F7:F${data.relevant_files.length+6}`).setNumberFormat('#,##0.0');
addSheet('问题与修复','已修复问题与待处理清单','4份源码已写回并备份；GUI、真实数据库、外部API与安卓真机未完整验收。',
 ['类型','原文件路径','具体问题','修复/后续动作','状态','原版备份','修复版本'],
 data.issues.map(r=>[r.kind,r.path,r.problem,r.action,r.status,r.backup||'',r.repaired_copy||'']),
 [28,110,75,100,55,110,110]);
addSheet('开发工具','本机开发与应用启动工具','路径来自桌面快捷方式、文件记录与已检查的运行环境；工具存在不能证明代码生成归属。',
 ['名称','工具或启动路径','工作目录','路径检查','用途'],
 data.tools.map(r=>[r.name,r.path,r.workdir,r.status,r.purpose]),
 [40,110,100,35,75]);
const main=sheets['项目目录'];main.tabColor='#203E5B';vid.tabColor='#D4A038';
main.getRange('A4:F4').values=[['项目/目录候选',null,'程序/脚本入口',null,'已修复文件',null]];
main.getRange('B4').formulas=[[`=COUNTA(C7:C${data.projects.length+6})`]];
main.getRange('D4').formulas=[[`=COUNTA('程序入口'!C7:C${data.programs.length+6})`]];
main.getRange('F4').formulas=[[`=COUNTIFS('问题与修复'!A7:A${data.issues.length+6},"已修复")`]];
vid.getRange('A4:F4').values=[['待录制',null,'录制中',null,'已完成',null]];
vid.getRange('B4').formulas=[[`=COUNTIFS(F7:F${vn},"待录制")`]];
vid.getRange('D4').formulas=[[`=COUNTIFS(F7:F${vn},"录制中")`]];
vid.getRange('F4').formulas=[[`=COUNTIFS(F7:F${vn},"已完成")`]];
for(const s of [main,vid])s.getRange('A4:F4').format.font={name:'Arial',size:10,bold:true,color:'#183B56'};
// Test the editable video status, then restore it before recalculation/export.
vid.getRange('F7').values=[['已完成']];
if(vid.getRange('F4').values[0][0]!==1)throw new Error('视频状态汇总没有更新');
vid.getRange('F7').values=[['待录制']];
wb.recalculate();
console.log((await wb.inspect({kind:'table',range:'项目目录!A4:F8',include:'values,formulas',tableMaxRows:5,tableMaxCols:6,maxChars:3500})).ndjson);
console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:10},maxChars:1500})).ndjson);
for(const name of names){const range=name==='文件明细'?'A6:C10':name==='开发工具'?'A6:B9':name==='问题与修复'?'A6:C9':'A6:E9';const blob=await wb.render({sheetName:name,range,scale:1,format:'png'});await fs.writeFile(path.join(base,'preview_'+name+'.png'),new Uint8Array(await blob.arrayBuffer()));}
const xlsx=await SpreadsheetFile.exportXlsx(wb);await xlsx.save(path.join(output,'AI开发程序总清单.xlsx'));
console.log(JSON.stringify({exported:path.join(output,'AI开发程序总清单.xlsx'),sheets:names,projects:data.projects.length,programs:data.programs.length,files:data.relevant_files.length}));
