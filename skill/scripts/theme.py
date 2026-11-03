# -*- coding: utf-8 -*-
"""报告样式与前端脚本（深色主题）。"""

CSS = r"""
:root{
  --bg:#0d1117; --bg2:#131a23; --card:#161e28; --card2:#1b2530;
  --line:#243040; --line2:#2e3d4f;
  --tx:#e6edf3; --tx2:#9fb0c2; --tx3:#6b7d90;
  --green:#3fb950; --green-bg:rgba(63,185,80,.12);
  --amber:#e3a008; --amber-bg:rgba(227,160,8,.12);
  --red:#f85149; --red-bg:rgba(248,81,73,.12);
  --blue:#4c8dff; --blue-bg:rgba(76,141,255,.12);
  --mono:"Cascadia Code","JetBrains Mono",Consolas,monospace;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{
  background:radial-gradient(1200px 600px at 12% -10%,#16202c 0%,#0d1117 55%) no-repeat,#0d1117;
  color:var(--tx); font-family:-apple-system,"Segoe UI","Microsoft YaHei",system-ui,sans-serif;
  font-size:14px; line-height:1.65; -webkit-font-smoothing:antialiased;
}
.wrap{max-width:1080px;margin:0 auto;padding:44px 26px 90px}
header.top{margin-bottom:26px}
.eyebrow{font-size:12px;letter-spacing:.18em;text-transform:uppercase;color:var(--blue);font-weight:600}
h1{font-size:30px;line-height:1.25;margin:8px 0 10px;letter-spacing:-.02em;font-weight:700}
.meta{color:var(--tx3);font-size:12.5px;display:flex;flex-wrap:wrap;gap:14px}
.meta span{display:inline-flex;align-items:center;gap:6px}
.dot{width:3px;height:3px;border-radius:50%;background:var(--tx3)}

.card{background:linear-gradient(180deg,var(--card2),var(--card));border:1px solid var(--line);
  border-radius:16px;padding:22px 24px;margin:16px 0}
.card.tight{padding:18px 20px}

/* 磁盘总览 */
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:20px}
.kpi{background:var(--bg2);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.kpi .lbl{font-size:11.5px;color:var(--tx3);letter-spacing:.04em;margin-bottom:6px}
.kpi .val{font-size:24px;font-weight:700;letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.kpi .val small{font-size:13px;font-weight:500;color:var(--tx3);margin-left:7px}
.bar{height:22px;border-radius:8px;background:#0a0f15;border:1px solid var(--line);
  display:flex;overflow:hidden;position:relative}
.bar > div{height:100%;transition:filter .2s}
.bar > div:hover{filter:brightness(1.25)}
.bar .g{background:linear-gradient(180deg,#49c95c,#2f9c40)}
.bar .y{background:linear-gradient(180deg,#efb01a,#c98a05)}
.bar .r{background:linear-gradient(180deg,#ff6b63,#d93e37)}
.bar .b{background:linear-gradient(180deg,#5b96ff,#3a6fd8)}
.legend{display:flex;flex-wrap:wrap;gap:10px;margin-top:14px}
.pill{display:inline-flex;align-items:center;gap:7px;background:var(--bg2);border:1px solid var(--line);
  border-radius:999px;padding:5px 13px;font-size:12.5px;color:var(--tx2)}
.pill i{width:8px;height:8px;border-radius:50%;display:inline-block}
.pill b{color:var(--tx);font-weight:600;font-variant-numeric:tabular-nums}

/* 排行 */
h2{font-size:15px;letter-spacing:.02em;margin:34px 0 12px;color:var(--tx);font-weight:650}
h2 .num{color:var(--tx3);font-weight:500;font-size:12.5px;margin-left:8px}
.rank{display:flex;flex-direction:column;gap:2px}
.row{display:grid;grid-template-columns:26px 1fr 128px;align-items:center;gap:12px;padding:9px 4px;
  border-bottom:1px dashed rgba(46,61,79,.55)}
.row:last-child{border-bottom:none}
.row .idx{color:var(--tx3);font-size:12px;font-variant-numeric:tabular-nums}
.row .nm{font-weight:600;font-size:13.5px;display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.row .tag{font-size:10.5px;padding:1px 7px;border-radius:5px;background:var(--blue-bg);color:#89b4ff;
  border:1px solid rgba(76,141,255,.3);font-weight:600;letter-spacing:.02em}
.row .p{font-family:var(--mono);font-size:11px;color:var(--tx3);margin-top:3px;word-break:break-all}
.row .sz{text-align:right;font-variant-numeric:tabular-nums;font-weight:650;font-size:13.5px;color:var(--tx)}
.track{grid-column:2/4;height:4px;background:#0a0f15;border-radius:3px;overflow:hidden;margin:-4px 0 6px}
.track > i{display:block;height:100%;background:linear-gradient(90deg,#3a6fd8,#5b96ff);border-radius:3px}

/* 建议 */
.callout{background:linear-gradient(90deg,rgba(76,141,255,.1),rgba(76,141,255,.02));
  border-left:3px solid var(--blue);border-radius:0 10px 10px 0;padding:14px 18px;color:var(--tx);
  font-size:14px;margin-bottom:16px}
ol.prio{margin:0;padding-left:0;counter-reset:p;list-style:none;display:flex;flex-direction:column;gap:9px}
ol.prio li{counter-increment:p;position:relative;padding-left:34px;color:var(--tx2);font-size:13.5px}
ol.prio li:before{content:counter(p);position:absolute;left:0;top:1px;width:22px;height:22px;border-radius:7px;
  background:var(--bg2);border:1px solid var(--line2);color:var(--blue);font-size:11.5px;font-weight:700;
  display:flex;align-items:center;justify-content:center}
ol.prio li b{color:var(--tx)}

/* 三级区块 */
.tier{margin:26px 0}
.tier-h{display:flex;align-items:center;gap:10px;margin-bottom:4px}
.tier-h .badge{font-size:11px;font-weight:700;padding:3px 9px;border-radius:6px;letter-spacing:.04em}
.tier-h h3{font-size:16px;margin:0;font-weight:650}
.tier-h .sum{color:var(--tx3);font-size:12.5px;margin-left:auto;font-variant-numeric:tabular-nums}
.tier-desc{color:var(--tx3);font-size:12.5px;margin:0 0 12px}
.g .badge{background:var(--green-bg);color:var(--green);border:1px solid rgba(63,185,80,.3)}
.y .badge{background:var(--amber-bg);color:#f0b429;border:1px solid rgba(227,160,8,.3)}
.r .badge{background:var(--red-bg);color:#ff7b72;border:1px solid rgba(248,81,73,.3)}

details.item{background:linear-gradient(180deg,var(--card2),var(--card));border:1px solid var(--line);
  border-radius:13px;margin-bottom:10px;overflow:hidden}
details.item > summary{cursor:pointer;padding:14px 18px;display:flex;align-items:center;gap:12px;
  list-style:none;user-select:none}
details.item > summary::-webkit-details-marker{display:none}
details.item > summary:hover{background:rgba(76,141,255,.04)}
.sum-main{flex:1;min-width:0}
.sum-title{font-weight:640;font-size:14px;display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.sum-path{font-family:var(--mono);font-size:11px;color:var(--tx3);margin-top:3px;word-break:break-all}
.sum-size{font-variant-numeric:tabular-nums;font-weight:700;font-size:14px;white-space:nowrap}
.chev{color:var(--tx3);font-size:11px;transition:transform .18s}
details[open] .chev{transform:rotate(90deg)}
.body{padding:2px 18px 18px;border-top:1px solid rgba(36,48,64,.8);margin-top:2px}
.body p{margin:10px 0;color:var(--tx2);font-size:13px}
.body .kv{display:flex;gap:8px;font-size:12.5px;color:var(--tx2);margin:7px 0}
.body .kv .k{color:var(--tx3);flex:0 0 74px}
.note{background:rgba(227,160,8,.07);border:1px solid rgba(227,160,8,.22);border-radius:8px;
  padding:9px 12px;font-size:12.5px;color:#e8c07d;margin:10px 0}
.note.info{background:var(--blue-bg);border-color:rgba(76,141,255,.22);color:#a8c4ff}
code.cmd{display:block;position:relative;font-family:var(--mono);font-size:12px;color:#c9d6e4;
  background:#0a0f15;border:1px solid var(--line);border-radius:8px;padding:10px 96px 10px 12px;
  white-space:pre-wrap;word-break:break-all;margin:8px 0}
code.cmd .cp{position:absolute;right:8px;top:7px;font-family:inherit;font-size:11px;background:var(--card2);
  color:var(--tx2);border:1px solid var(--line2);border-radius:6px;padding:3px 9px;cursor:pointer}
code.cmd .cp:hover{color:var(--tx);border-color:var(--blue)}
.btnrow{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
button.act{font-family:inherit;font-size:12.5px;font-weight:600;border-radius:8px;padding:7px 14px;
  cursor:pointer;border:1px solid var(--line2);background:var(--card2);color:var(--tx);transition:.15s}
button.act:hover{border-color:var(--blue);color:#9dc0ff}
button.act.g{background:rgba(63,185,80,.14);border-color:rgba(63,185,80,.4);color:#66d97a}
button.act.g:hover{background:rgba(63,185,80,.24)}
button.act.r{background:rgba(248,81,73,.1);border-color:rgba(248,81,73,.35);color:#ff8b84}
button.act.r:hover{background:rgba(248,81,73,.2)}
button.act:disabled{opacity:.45;cursor:not-allowed}
ul.steps{margin:8px 0 0;padding-left:20px;color:var(--tx2);font-size:13px}
ul.steps li{margin:5px 0}
.tip{font-size:12px;color:var(--tx3);margin-top:10px}
.longterm{display:grid;grid-template-columns:1fr 1fr;gap:10px 22px}
.longterm div{font-size:13px;color:var(--tx2);padding-left:22px;position:relative}
.longterm div:before{content:"›";position:absolute;left:6px;color:var(--blue);font-weight:700}
footer{margin-top:40px;padding-top:16px;border-top:1px solid var(--line);color:var(--tx3);font-size:11.5px}
#toast{position:fixed;left:50%;bottom:26px;transform:translateX(-50%) translateY(20px);opacity:0;
  background:#1b2530;border:1px solid var(--line2);border-radius:10px;padding:11px 20px;font-size:13px;
  box-shadow:0 12px 32px rgba(0,0,0,.5);transition:.25s;pointer-events:none;z-index:99;max-width:80vw}
#toast.show{opacity:1;transform:translateX(-50%) translateY(0)}
@media (max-width:760px){
  .kpis{grid-template-columns:1fr 1fr}
  .longterm{grid-template-columns:1fr}
  .row{grid-template-columns:20px 1fr 96px}
  h1{font-size:23px}
}
"""

JS = r"""
const TOKEN = "__TOKEN__";
function toast(msg, bad){
  const t = document.getElementById('toast');
  t.textContent = msg; t.style.borderColor = bad ? '#f85149' : '#2e3d4f';
  t.classList.add('show'); clearTimeout(window.__tt);
  window.__tt = setTimeout(()=>t.classList.remove('show'), 3600);
}
async function post(ep, body){
  const r = await fetch(ep, {method:'POST',
    headers:{'Content-Type':'application/json','X-Token':TOKEN},
    body: JSON.stringify(body)});
  let j = {};
  try { j = await r.json(); } catch(e){}
  if(!r.ok || j.ok === false) throw new Error(j.error || ('HTTP '+r.status));
  return j;
}
async function act(kind, paths, label){
  if(!Array.isArray(paths)) paths = [paths];
  let tip = '';
  if(kind==='trash') tip = '移入回收站（可还原）：\n\n' + paths.join('\n') + '\n\n继续？';
  if(kind==='rm') tip = '⚠️ 直接删除、不可恢复：\n\n' + paths.join('\n') + '\n\n确定继续？';
  if(!confirm(tip)) return;
  try{
    const j = await post('/api/'+kind, {paths});
    toast((label||'') + ' 完成：' + (j.count||paths.length) + ' 项' + (j.freed? '，释放 '+j.freed : ''));
  }catch(e){ toast('失败：'+e.message, true); }
}
async function openPath(p){
  try{ await post('/api/open', {paths:[p]}); toast('已在资源管理器中打开'); }
  catch(e){ toast('打开失败：'+e.message, true); }
}
function copyCmd(btn){
  const txt = btn.parentElement.querySelector('.txt').textContent;
  navigator.clipboard.writeText(txt).then(()=>{
    const o = btn.textContent; btn.textContent='已复制'; setTimeout(()=>btn.textContent=o, 1200);
  });
}
"""
