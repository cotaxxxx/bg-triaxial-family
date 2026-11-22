"""Refresh the single human-readable position and save completed inner integrals."""
import json
import hashlib
from datetime import datetime,timezone,timedelta
from pathlib import Path
from samples import ROOT
from run_intervals import atomic
from run_references import aggregate,keys,path

P=ROOT/'results';aggregate()
gate=json.loads((P/'E2_REFERENCE_GATE.json').read_text())
done=[f.name for k,i in keys() for d in (80,110) if (f:=path(k,i,d)).exists() and f.stat().st_size]
lat={};index={};modified=[]
archive=P/'checkpoints';archive.mkdir(exist_ok=True)
for f in sorted((P/'ref_work').glob('*.jsonl')):
    raw=f.read_bytes();raw=raw[:raw.rfind(b'\n')+1]
    if not raw:continue
    lines=raw.splitlines(keepends=True);key=f.stem;lat[f.name]=len(lines)
    original=archive/f.name;parts=[];offset=0
    if original.exists():
        first=original.read_bytes()
        if not raw.startswith(first):raise ValueError('local records differ from committed prefix')
        parts.append((f.name,first));offset=len(first.splitlines())
    for n in range(offset,len(lines),256):
        rel=f'parts/{key}/{n+1:08d}.jsonl';block=b''.join(lines[n:n+256])
        dest=archive/rel;dest.parent.mkdir(parents=True,exist_ok=True)
        if not dest.exists() or dest.read_bytes()!=block:
            dest.write_bytes(block);modified.append(str(dest.relative_to(ROOT)))
        parts.append((rel,block))
    index[key]={'rows':len(lines),'files':[{'path':name,'sha256':hashlib.sha256(block).hexdigest()} for name,block in parts]}
atomic(archive/'INDEX.json',json.dumps(index,sort_keys=True,indent=2)+'\n')
# Local publication convenience. The index is the durable source of truth.
atomic(P/'checkpoint_changed_local.json',json.dumps(modified)+'\n')
now=datetime.now(timezone.utc);jst=now.astimezone(timezone(timedelta(hours=9))).strftime('%Y-%m-%d %H:%M:%S JST')
progress={'utc':now.isoformat(timespec='seconds'),'recorded_jst':jst,'completed_pairs':gate['pairs'],'total_pairs':88,
          'completed_precision_runs':len(done),'total_precision_runs':176,'completed_runs':done,
          'checkpoint_latitudes':lat,'reference_gate':gate['reference_gate'],'E3':'PASS_92_OF_92','E4':'NOT_STARTED'}
atomic(P/'REFERENCE_PROGRESS.json',json.dumps(progress,ensure_ascii=False,indent=2)+'\n')
passed=gate['statuses'].get('PASS',0)
blocked=gate['reference_gate']=='STOP_REPORT'
next_action=('未収束または不包含の記録を chat・Judge に報告し、E4 を停止する。' if blocked else
             '完了した80桁・110桁の各組で、絶対差が 10⁻⁵⁵ 未満か、110桁の値を固定済み区間が含むかを判定する。E2c は親箱への包含も照合する。')
timing=''
first=path('H',0,80)
counters=[P/f'progress_Haa_11_{d}.json' for d in (80,110)]
if first.exists() and first.stat().st_size and all(f.exists() for f in counters):
    baseline=json.loads(first.read_text())
    data=[json.loads(f.read_text()) for f in counters]
    scales=[baseline['quadrature_calls']*row['seconds']/row['evaluations']/3600 for row in data]
    scenario=(160*baseline['seconds']/3600+8*sum(scales))/9
    timing=(f'**所要時間の目安**　最初の通常点の80桁は {baseline["seconds"]/60:.1f} 分・'
            f'{baseline["quadrature_calls"]:,} 評価。通常点・接触点の160本が同じ時間、'
            f'Hₐₐ の16本が同じ評価数（現在の速度で80桁 {scales[0]:.1f} 時間・110桁 {scales[1]:.1f} 時間／本）と仮定し、'
            f'9枠に均等配分すると全体で約 {scenario:.0f} 時間。実際の評価数は点と精度で異なり、'
            '全体には数十時間〜数日を見込む。終了日時は未確定。')
top=f'''<!-- CURRENT_BEGIN -->
## 現在地　{jst}

|項目|実測・状態|
|---|---|
|正式参照（純 mpmath、精度別）|**{len(done)} / 176 完了**|
|80桁・110桁が両方完了したペア|**{gate['pairs']} / 88**（包含まで合格 {passed}）|
|E1|測定完了。2,048面の幅は中心 5.99839、全箱 23.39254|
|E3|**92 / 92 合格**（chat 判定 c157cc6）|
|E4|**未開始**。監査済みの八組・予算を維持。E2 群と運用条件の充足待ち|

{timing}

**次の判定**　{next_action}

以下は経過記録。最新の状態は上表に示す。
<!-- CURRENT_END -->'''
f=P/'EXECUTION_STATUS.md';old=f.read_text()
if '<!-- CURRENT_BEGIN -->' in old:
    h,rest=old.split('<!-- CURRENT_BEGIN -->',1);_,tail=rest.split('<!-- CURRENT_END -->',1);updated=h+top+tail
else:
    h,tail=old.split('\n',1);updated=h+'\n\n'+top+'\n'+tail
atomic(f,updated)
print(jst,len(done),gate['pairs'],sum(lat.values()))
