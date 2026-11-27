const {chromium}=require('playwright'); const fs=require('fs');
(async()=>{
  const file=process.argv[2], out=process.argv[3];
  const b=await chromium.launch(); const res={};
  for(const [name,vp] of [['desktop',{width:1280,height:900}],['phone',{width:390,height:844}]]){
    const ctx=await b.newContext({viewport:vp,offline:true}); const p=await ctx.newPage(); const reqs=[],errs=[];
    p.on('request',r=>{ if(!r.url().startsWith('file:')) reqs.push(r.url()); }); p.on('console',m=>{ if(m.type()==='error') errs.push(m.text()); }); p.on('pageerror',e=>errs.push(String(e)));
    await p.goto('file://'+file); await p.waitForTimeout(300);
    const state=async()=>p.evaluate(()=>({checked:document.getElementById('unc').checked, ev:document.getElementById('event').innerText, legC:getComputedStyle(document.getElementById('legCrow')).display, note:getComputedStyle(document.getElementById('uncNote')).display}));
    const r={reqs,errs,hscroll:await p.evaluate(()=>document.documentElement.scrollWidth>document.documentElement.clientWidth)};
    await p.evaluate(()=>{S.path=0;S.y=0.5;S.z=3.5;drawMapOverlay();updateText();drawView();}); await p.waitForTimeout(80);
    r.off=await state(); await p.screenshot({path:out+'/chat_'+name+'_default.png'});
    if(name==='desktop'){
      r.strips=await p.evaluate(()=>DATA.strips); r.cross=await p.evaluate(()=>DATA.cross);
      await p.check('#unc'); await p.waitForTimeout(150); r.on=await state(); await p.screenshot({path:out+'/chat_desktop_unc_on.png'});
      await p.uncheck('#unc'); await p.waitForTimeout(100); r.offAgain=await state();
      await p.evaluate(()=>{S.y=417/1024;S.z=257/256;drawMapOverlay();updateText();}); await p.waitForTimeout(60); r.z1=(await state()).ev;
      await p.click('#bJa'); await p.waitForTimeout(80); r.z1ja=(await state()).ev; r.foot=await p.evaluate(()=>document.body.innerText.split('\n').filter(l=>/論文：/.test(l))[0]);
    }
    res[name]=r; await ctx.close();
  }
  fs.writeFileSync(out+'/chat_audit3.json',JSON.stringify(res)); await b.close();
})();
