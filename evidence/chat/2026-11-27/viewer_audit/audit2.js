const {chromium}=require('playwright'); const fs=require('fs');
(async()=>{
  const file=process.argv[2], out=process.argv[3];
  const b=await chromium.launch(); const ctx=await b.newContext({viewport:{width:1280,height:900},offline:true}); const p=await ctx.newPage();
  await p.goto('file://'+file); await p.waitForTimeout(300);
  const probe=async(y,z)=>{ await p.evaluate(([y,z])=>{S.path=0;S.y=y;S.z=z; drawMapOverlay(); updateText(); drawView();},[y,z]); await p.waitForTimeout(50); return await p.evaluate(()=>document.getElementById('event').innerText); };
  const res={};
  res.probes={cross:await probe(0.63818,2.2966), justOutsideCrossBox:await probe(0.6375,2.2966), cp:await probe(1,4.73), cpNear:await probe(0.999,4.73), bp:await probe(1,2.07), cornerBall:await probe(1,1), far:await probe(0.3,6.9)};
  res.strips=await p.evaluate(()=>DATA.strips); res.side=await p.evaluate(()=>DATA.side); res.meta=await p.evaluate(()=>DATA.meta); res.marks=await p.evaluate(()=>DATA.marks); res.ends=await p.evaluate(()=>DATA.ends); res.edgeEnds=await p.evaluate(()=>DATA.edgeEnds);
  res.inStripsSrc=await p.evaluate(()=>inStrips.toString()+'\n'+events.toString());
  // zoom screenshot near crossing
  await probe(0.63818,2.2966); for(let i=0;i<6;i++){ await p.click('#zIn'); } await p.waitForTimeout(150); await p.screenshot({path:out+'/chat_zoom_cross.png'});
  fs.writeFileSync(out+'/chat_audit2.json',JSON.stringify(res)); await b.close();
})();
