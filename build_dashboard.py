"""data/lotto_history.csv 를 넣어 단일 파일 대시보드(dashboard.html)를 만든다."""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent

TEMPLATE = r"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>로또 3등 백테스트</title>
<style>
:root{--bg:#f4f5f3;--surface:#fff;--fg:#1c2220;--muted:#5c6662;--line:#dde1dd;--accent:#1f6f5b;--accentfg:#fff;--warn:#8a5a00;--warnbg:#fff4d6}
@media (prefers-color-scheme:dark){:root{--bg:#141a18;--surface:#1c2421;--fg:#e8ede9;--muted:#9aa6a0;--line:#2c3631;--accent:#4fb99c;--accentfg:#0c1411;--warn:#f0c76a;--warnbg:#2d2512}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.6 "Noto Sans KR","Malgun Gothic",sans-serif}
main{max-width:760px;margin:0 auto;padding:24px 16px 48px}
h1{font-size:22px;margin:0 0 4px}
.sub{color:var(--muted);margin:0 0 16px}
.warn{background:var(--warnbg);color:var(--warn);border-radius:8px;padding:10px 14px;margin-bottom:16px;font-size:14px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:20px;margin-bottom:16px}
.card h2{font-size:15px;margin:0 0 12px;color:var(--muted);font-weight:600}
.balls{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:16px}
.ball{width:52px;height:52px;border-radius:50%;display:grid;place-items:center;font-weight:700;font-size:19px;color:#fff;font-variant-numeric:tabular-nums}
.row{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
button{background:var(--accent);color:var(--accentfg);border:0;border-radius:8px;padding:10px 18px;font:inherit;font-weight:600;cursor:pointer}
button:focus-visible{outline:3px solid var(--fg);outline-offset:2px}
table{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums}
th,td{text-align:left;padding:7px 8px;border-bottom:1px solid var(--line)}
th{color:var(--muted);font-weight:600;font-size:13px}
td.n,th.n{text-align:right}
.meta{color:var(--muted);font-size:13px;margin-top:10px}
.num{display:inline-block;min-width:28px;padding:1px 4px;margin:1px 3px 1px 0;border-radius:6px;text-align:center;border:1px solid transparent}
.num.hit{color:#fff;font-weight:700}
.num.bonus{border:1px dashed var(--muted)}
.plus{color:var(--muted);margin:0 4px 0 2px}
</style>
</head>
<body>
<main>
<h1>로또 6/45 · 3등 백테스트</h1>
<p class="sub">__TOTAL__회차 (1회 ~ __LAST__회, 마지막 추첨일 __DATE__) 기준</p>
<div class="warn">과거 당첨번호에 맞춰 만든(과적합) 조합입니다. 3등이 많이 나온 조합들의 번호를 합친 조합이며, 앞으로의 당첨 확률은 모든 조합이 동일합니다(3등 1/35,724).</div>

<section class="card" aria-live="polite">
  <h2>생성된 번호</h2>
  <div class="balls" id="balls"></div>
  <div class="meta" id="status"></div>
</section>

<section class="card">
  <h2>백테스트 결과 (전 회차 대조)</h2>
  <table>
    <thead><tr><th>등수</th><th>조건</th><th class="n">횟수</th></tr></thead>
    <tbody id="ranks"></tbody>
  </table>
</section>

<section class="card">
  <h2>3등 · 4등 당첨 회차</h2>
  <table>
    <thead><tr><th>회차</th><th>추첨일</th><th>등수</th><th>당첨번호</th></tr></thead>
    <tbody id="hits"></tbody>
  </table>
  <div class="meta" id="filter"></div>
</section>
</main>

<script>
const DRAWS = __DATA__;  // [회차, 날짜, n1..n6, 보너스]
const COND = {1:"6개 일치",2:"5개 + 보너스",3:"5개 일치",4:"4개 일치",5:"3개 일치"};

function backtest(nums){
  const mine=new Set(nums), cnt={1:0,2:0,3:0,4:0,5:0}, hits=[];
  for(const d of DRAWS){
    const m=d.slice(2,8).filter(x=>mine.has(x)).length;
    let k=0;
    if(m===6)k=1; else if(m===5)k=mine.has(d[8])?2:3; else if(m===4)k=4; else if(m===3)k=5;
    if(k){cnt[k]++; if(k===3||k===4)hits.push({d,k})}
  }
  return {cnt,hits};
}
const MIN3 = 3;  // 백테스트에서 3등이 나와야 하는 최소 횟수
// 3등이 여러 번이려면 번호 4~5개가 겹치는 두 회차가 필요하다. 그런 쌍에서 후보를 만들어 전수 검사한다.
const CANDS = (()=>{
  const sets=DRAWS.map(d=>new Set(d.slice(2,8))), seen=new Set(), out=[];
  const add=n=>{n.sort((a,b)=>a-b);const k=n.join();if(!seen.has(k)){seen.add(k);out.push(n)}};
  for(let i=0;i<sets.length;i++)for(let j=i+1;j<sets.length;j++){
    const onlyA=[...sets[i]].filter(x=>!sets[j].has(x)), onlyB=[...sets[j]].filter(x=>!sets[i].has(x));
    const common=[...sets[i]].filter(x=>sets[j].has(x));
    if(common.length===4){for(const a of onlyA)for(const b of onlyB)add([...common,a,b])}
    else if(common.length===5){for(let x=1;x<=45;x++)if(!sets[i].has(x)&&!sets[j].has(x))add([...common,x])}
  }
  return out;
})();
// 1·2등 없이 3등이 MIN3회 이상인 조합들
const SOURCE = CANDS.map(n=>({nums:n,...backtest(n)}))
  .filter(r=>r.cnt[3]>=MIN3&&r.cnt[1]===0&&r.cnt[2]===0);
// 그 조합들에서 가장 많이 쓰인 번호 6개(같으면 작은 번호)를 합쳐 새 조합을 만든다
const USE = {};
for(const r of SOURCE)for(const n of r.nums)USE[n]=(USE[n]||0)+1;
const PICK = Object.keys(USE).map(Number).sort((a,b)=>USE[b]-USE[a]||a-b).slice(0,6);
const RESULT = {nums:PICK.slice().sort((a,b)=>a-b),...backtest(PICK)};
const color=n=>n<=10?"#c9961a":n<=20?"#2f6fb0":n<=30?"#c0443a":n<=40?"#6b7570":"#3c8a4f";
function el(tag,txt,cls){const e=document.createElement(tag);if(txt!==undefined)e.textContent=txt;if(cls)e.className=cls;return e}

function render(){
  const r=RESULT, balls=document.getElementById("balls");
  balls.replaceChildren();
  if(!SOURCE.length){document.getElementById("status").textContent="3등 "+MIN3+"회 이상 조합이 없습니다.";return}
  for(const n of r.nums){const b=el("div",n,"ball");b.style.background=color(n);balls.append(b)}
  document.getElementById("status").textContent="3등 "+MIN3+"회 이상 조합 "+SOURCE.length+"개에서 가장 많이 쓰인 번호 ("+r.nums.map(n=>n+":"+USE[n]+"회").join(" ")+")";
  const ranks=document.getElementById("ranks");ranks.replaceChildren();
  for(let k=1;k<=5;k++){const tr=el("tr");tr.append(el("td",k+"등"),el("td",COND[k]),el("td",r.cnt[k]+"회","n"));ranks.append(tr)}
  const nz=DRAWS.length-Object.values(r.cnt).reduce((a,b)=>a+b,0);
  const tr=el("tr");tr.append(el("td","낙첨"),el("td","2개 이하"),el("td",nz+"회","n"));ranks.append(tr);
  const hits=document.getElementById("hits");hits.replaceChildren();
  const mine=new Set(r.nums);
  for(const {d,k} of r.hits){
    const row=el("tr");
    const nums=el("td");
    d.slice(2,8).forEach(x=>{const s=el("span",x,mine.has(x)?"num hit":"num");if(mine.has(x))s.style.background=color(x);nums.append(s)});
    nums.append(el("span","+","plus"),el("span",d[8],"num bonus"));
    row.append(el("td",d[0]+"회"),el("td",d[1]),el("td",k+"등"),nums);
    hits.append(row);
  }
  document.getElementById("filter").textContent="위 공과 같은 색으로 칠해진 번호가 일치한 번호입니다. 점선 테두리는 보너스 번호입니다.";
}
render();
</script>
</body>
</html>
"""


def main():
    df = pd.read_csv(ROOT / "data" / "lotto_history.csv")
    data = json.dumps(df.values.tolist(), ensure_ascii=False)
    html = (
        TEMPLATE.replace("__DATA__", data)
        .replace("__TOTAL__", str(len(df)))
        .replace("__LAST__", str(int(df.draw_no.max())))
        .replace("__DATE__", str(df.date.iloc[-1]))
    )
    (ROOT / "dashboard.html").write_text(html, encoding="utf-8")
    print(f"dashboard.html 저장 완료 ({len(df)}회차)")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
