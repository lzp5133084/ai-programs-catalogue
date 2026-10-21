import {chromium} from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const base=path.dirname(new URL(import.meta.url).pathname).replace(/^\/([A-Z]:)/i,'$1');
const file=path.join(base,'..','outputs','AI开发程序目录.html');
const browser=await chromium.launch({executablePath:'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',headless:true});
const page=await browser.newPage({viewport:{width:1500,height:1100}});let errors=[];
page.on('pageerror',e=>errors.push(e.message));
await page.route('**/*',route=>route.request().url().startsWith('file:')?route.continue():route.abort());
await page.goto(pathToFileURL(file).href,{waitUntil:'load',timeout:60000});
const data=JSON.parse(await page.locator('#catalogue-data').textContent());
console.log(JSON.stringify({initialRows:await page.locator('#tbody tr').count(),errors,stats:await page.locator('#stats').textContent()}));
await page.screenshot({path:path.join(base,'网页目录预览.png'),fullPage:false});
if(await page.locator('#tbody tr').count()!==25){await browser.close();throw new Error('初始目录分页不正确：'+errors.join(' / '));}
await page.screenshot({path:path.join(base,'网页目录预览.png'),fullPage:false});
for(const [name,count] of [['程序入口',data.programs.length],['使用视频计划',data.programs.length],['问题与修复',data.issues.length],['开发工具',data.tools.length],['全部文件索引',data.files.length]]){
 await page.getByRole('button',{name,exact:true}).click();
 if(await page.locator('#resultCount').textContent()!=='共 '+count+' 条')throw new Error(name+'数量不一致');
}
await page.getByRole('button',{name:'项目目录',exact:true}).click();
await page.locator('#search').fill('实时屏幕翻译');
if(await page.locator('#tbody tr').count()<1)throw new Error('名称搜索失败');
await page.locator('#tbody button.detail').first().click();
const hrefs=await page.locator('#detailBody a').evaluateAll(nodes=>nodes.map(x=>x.href));
if(!hrefs.length||hrefs.some(x=>!x.startsWith('file:///')||x.includes('%5C')))throw new Error('原路径链接编码不正确');
await page.getByRole('button',{name:'关闭',exact:true}).click();
await page.getByRole('button',{name:'使用视频计划',exact:true}).click();
const select=page.locator('#tbody select').first();await select.selectOption('已完成');
await page.getByRole('button',{name:'项目目录',exact:true}).click();await page.getByRole('button',{name:'使用视频计划',exact:true}).click();
if(await page.locator('#tbody select').first().inputValue()!=='已完成')throw new Error('录制状态保存失败');
await page.locator('#tbody select').first().selectOption('待录制');
await page.getByRole('button',{name:'全部文件索引',exact:true}).click();await page.locator('#scopeFilter').selectOption('开发候选');
if(!Number((await page.locator('#resultCount').textContent()).match(/\d+/)[0]))throw new Error('文件类别筛选失败');
if(errors.length)throw new Error(errors.join('\n'));
await browser.close();
await fs.writeFile(path.join(base,'catalogue_qa.json'),JSON.stringify({page_errors:errors,checks:['分页','六类目录记录数量','名称搜索','详情弹窗','原路径file链接','视频状态持久化','文件类别筛选'],counts:data.counts},null,2));
console.log(JSON.stringify({browser_checks_passed:7,counts:data.counts}));
