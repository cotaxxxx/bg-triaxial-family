// Browser checks of the built viewer (Playwright + Chromium, offline).  Usage: node browser_check.js VIEWER.html OUT_DIR
const { chromium } = require('playwright');
const path = require('path'), fs = require('fs');
(async () => {
  const file = 'file://' + path.resolve(process.argv[2]), out = process.argv[3];
  const browser = await chromium.launch();
  const report = { requests_other_than_the_file: [], console_errors: [], functional: {}, screens: [] };
  for (const [name, vp] of [['desktop', { width: 1280, height: 900 }], ['phone', { width: 390, height: 844 }]]) {
    const ctx = await browser.newContext({ viewport: vp, offline: true, deviceScaleFactor: 1 });
    const page = await ctx.newPage();
    page.on('request', r => { if (r.url() !== file) report.requests_other_than_the_file.push(r.url()); });
    page.on('console', m => { if (m.type() === 'error') report.console_errors.push(m.text()); });
    page.on('pageerror', e => report.console_errors.push(String(e)));
    await page.goto(file); await page.waitForTimeout(300);
    if (name === 'desktop') {
      report.functional = await page.evaluate(() => {
        const V = window.__viewer, D = V.DATA, r = {};
        const mid = s => [(s[0] + s[1]) / 2, (s[2] + s[3]) / 2];
        for (const q of ['Z1', 'Z2', 'D1', 'D2']) {
          let ok = 0; for (const s of D.strips[q]) { const m = mid(s); V.setShape(m[0], m[1]); if (V.events()[q]) ok++; }
          r['strip_centres_flag_' + q] = ok + '/' + D.strips[q].length;
        }
        V.setShape((D.cross.y[0] + D.cross.y[1]) / 2, (D.cross.z[0] + D.cross.z[1]) / 2); let e = V.events();
        r.crossing = { x: e.x, Z1: e.Z1, D2: e.D2, Z2: e.Z2, D1: e.D1, text_on: document.getElementById('event').className };
        V.setShape(1, (D.edgeEnds.cp[0] + D.edgeEnds.cp[1]) / 2); e = V.events(); r.cp = { cp: e.cp, bp: e.bp };
        V.setShape(1, (D.edgeEnds.bp[0] + D.edgeEnds.bp[1]) / 2); e = V.events(); r.bp = { cp: e.cp, bp: e.bp };
        V.setShape(0.8, 1.6); e = V.events(); r.generic_point = { any: Object.values(e).some(Boolean), text: document.getElementById('event').textContent.slice(0, 60) };
        V.setShape(0.1, 9); r.clamped_to_R = [V.S.y, V.S.z];
        r.strip_rects_in_svg = document.querySelectorAll('#map g rect').length;
        const box = document.getElementById('unc'), vis = id => getComputedStyle(document.getElementById(id)).display !== 'none';
        V.setShape(0.6, 2.05);
        r.uncertified_default = { checked: box.checked, legend_C_visible: vis('legCrow'), note_visible: vis('uncNote') };
        return r;
      });
    }
    for (const lang of ['en', 'ja']) {
      await page.click(lang === 'en' ? '#bEn' : '#bJa');
      await page.evaluate(() => { const D = window.__viewer.DATA; window.__viewer.setShape(0.6, 2.05); });
      await page.waitForTimeout(250);
      const f = `${name}_${lang}.png`; await page.screenshot({ path: path.join(out, f), fullPage: true }); report.screens.push(f);
    }
    if (name === 'desktop') {
      await page.click('#bEn'); await page.waitForTimeout(200);
      report.functional.uncertified_default.event_text_has_uncertified_line = await page.evaluate(() => /Uncertified/.test(document.getElementById('event').textContent));
      await page.check('#unc'); await page.waitForTimeout(300);
      report.functional.uncertified_checked = await page.evaluate(() => ({ legend_C_visible: getComputedStyle(document.getElementById('legCrow')).display !== 'none', note_visible: getComputedStyle(document.getElementById('uncNote')).display !== 'none', event_text_has_uncertified_line: /Uncertified/.test(document.getElementById('event').textContent) }));
      await page.screenshot({ path: path.join(out, 'desktop_en_uncertified_on.png'), fullPage: true }); report.screens.push('desktop_en_uncertified_on.png');
      await page.uncheck('#unc'); await page.waitForTimeout(200);
      await page.evaluate(() => { const D = window.__viewer.DATA; window.__viewer.setShape((D.cross.y[0] + D.cross.y[1]) / 2, (D.cross.z[0] + D.cross.z[1]) / 2); });
      await page.click('#zIn'); await page.click('#zIn'); await page.click('#zIn'); await page.waitForTimeout(250);
      await page.screenshot({ path: path.join(out, 'desktop_en_zoom64_crossing.png'), fullPage: true }); report.screens.push('desktop_en_zoom64_crossing.png');
      report.horizontal_scroll_desktop = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
    } else report.horizontal_scroll_phone = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
    await ctx.close();
  }
  await browser.close();
  fs.writeFileSync(path.join(out, '..', 'browser_check.json'), JSON.stringify(report, null, 1));
  console.log(JSON.stringify(report, null, 1));
})();
