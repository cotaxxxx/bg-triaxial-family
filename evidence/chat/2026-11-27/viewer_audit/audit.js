const {chromium}=require('playwright'); const fs=require('fs');
(async()=>{
  const file=process.argv[2], out=process.argv[3];
  const b=await chromium.launch(); const res={};
  for(const [name,vp] of [['desktop',{width:1280,height:900}],['phone',{width:390,height:844}]]){
    const ctx=await b.newContext({viewport:vp,deviceScaleFactor:1,offline:true}); const p=await ctx.newPage();
    const reqs=[],errs=[]; p.on('request',r=>{ if(!r.url().startsWith('file:')) reqs.push(r.url()); }); p.on('console',m=>{ if(m.type()==='error') errs.push(m.text()); }); p.on('pageerror',e=>errs.push(String(e)));
    await p.goto('file://'+file); await p.waitForTimeout(400);
    const keys=await p.evaluate(()=>Object.keys(DATA));
    res[name]={reqs,errs,keys, hscroll: await p.evaluate(()=>document.documentElement.scrollWidth>document.documentElement.clientWidth)};
    if(name==='desktop'){
      res.data=await p.evaluate(()=>DATA);
      // set shapes and read event text
      const probe=async(y,z)=>{ await p.evaluate(([y,z])=>{S.y=y;S.z=z; if(typeof update==='function') update(); else if(typeof render==='function') render();},[y,z]); await p.waitForTimeout(60); return await p.evaluate(()=>[document.getElementById('status').innerText,document.getElementById('event').innerText,document.getElementById('unc')?document.getElementById('uncRow').innerText:'']); };
      res.fn=await p.evaluate(()=>Object.getOwnPropertyNames(window).filter(k=>typeof window[k]==='function'&&/^[a-z]/.test(k)&&!/^(alert|atob|btoa|blur|close|confirm|fetch|find|focus|open|print|prompt|stop|scroll|move|resize|get|set|clear|queue|request|cancel|post|report|structured|match|capture|release|create|webkit|check|show|on)/.test(k)).slice(0,40));
      res.probes={none:await probe(0.8,1.6), z1:await probe(417/1024,257/256), cross:await probe(0.63818,2.2966), cp:await probe(1,4.73), bp:await probe(1,2.07), d2:await probe(0.2520,2.2148), mid:await probe(0.5,3.5)};
      await p.screenshot({path:out+'/chat_desktop_en.png',fullPage:true});
      await p.click('#bJa'); await p.waitForTimeout(100); res.ja=await p.evaluate(()=>[document.title,document.getElementById('event').innerText]);
      await p.screenshot({path:out+'/chat_desktop_ja.png',fullPage:true});
      // real click on the map
      const box=await p.locator('#map').boundingBox(); await p.mouse.click(box.x+box.width*0.6,box.y+box.height*0.5); await p.waitForTimeout(100); res.click=await p.evaluate(()=>[S.y,S.z]);
    } else { await p.screenshot({path:out+'/chat_phone_en.png',fullPage:true}); }
    await ctx.close();
  }
  fs.writeFileSync(out+'/chat_audit.json',JSON.stringify(res,null,1)); await b.close();
})();
