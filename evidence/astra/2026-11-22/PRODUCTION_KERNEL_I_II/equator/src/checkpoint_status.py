"""Refresh the single human-readable position and save completed inner integrals."""
import json
from datetime import datetime,timezone,timedelta
from pathlib import Path
from samples import ROOT
from run_intervals import atomic
from run_references import aggregate,keys,path

P=ROOT/'results';aggregate()
gate=json.loads((P/'E2_REFERENCE_GATE.json').read_text())
done=[f.name for k,i in keys() for d in (80,110) if (f:=path(k,i,d)).exists() and f.stat().st_size]
lat={}
for f in sorted((P/'ref_work').glob('*.jsonl')):
    raw=f.read_bytes();raw=raw[:raw.rfind(b'\n')+1]
    (P/'checkpoints').mkdir(exist_ok=True)
    (P/'checkpoints'/f.name).write_bytes(raw)
    lat[f.name]=len(raw.splitlines())
now=datetime.now(timezone.utc);jst=now.astimezone(timezone(timedelta(hours=9))).strftime('%Y-%m-%d %H:%M:%S JST')
progress={'utc':now.isoformat(timespec='seconds'),'recorded_jst':jst,'completed_pairs':gate['pairs'],'total_pairs':88,
          'completed_precision_runs':len(done),'total_precision_runs':176,'completed_runs':done,
          'checkpoint_latitudes':lat,'reference_gate':gate['reference_gate'],'E3':'PASS_92_OF_92','E4':'NOT_STARTED'}
atomic(P/'REFERENCE_PROGRESS.json',json.dumps(progress,ensure_ascii=False,indent=2)+'\n')
passed=gate['statuses'].get('PASS',0)
blocked=gate['reference_gate']=='STOP_REPORT'
next_action=('未収束または不包含の記録を chat・Judge に報告し、E4 を停止する。' if blocked else
             '完了した80桁・110桁の各組で、絶対差が 10⁻⁵⁵ 未満か、110桁の値を固定済み区間が含むかを判定する。E2c は親箱への包含も照合する。')
top=f'''<!-- CURRENT_BEGIN -->
## 現在地　{jst}

|項目|実測・状態|
|---|---|
|正式参照（純 mpmath、精度別）|**{len(done)} / 176 完了**|
|80桁・110桁が両方完了したペア|**{gate['pairs']} / 88**（包含まで合格 {passed}）|
|E1|測定完了。2,048面の幅は中心 5.99839、全箱 23.39254|
|E3|**92 / 92 合格**（chat 判定 c157cc6）|
|E4|**未開始**。監査済みの八組・予算を維持。E2 群と運用条件の充足待ち|

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
