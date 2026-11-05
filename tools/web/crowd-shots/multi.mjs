// node multi.mjs <jobs.json>
// jobs: { dpr, w, h, base, out, variants: [{key, query}], views: {name: {eye, at, fov}}, clip: {keys:[], seconds, fps} }
// One page load per variant: the stills at the finish (leader at the post), then an optional clip that tracks
// the leader past the stand, every frame at a fixed step.
import puppeteer from "puppeteer-core";
import fs from "node:fs";
import path from "node:path";
const here = path.dirname(new URL(import.meta.url).pathname);
const J = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
fs.mkdirSync(J.out, { recursive: true });
const browser = await puppeteer.launch({
  executablePath: "/usr/bin/google-chrome", headless: true,
  args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist", "--no-sandbox", "--disable-dev-shm-usage"],
  protocolTimeout: 900000,
});
for (const v of J.variants) {
  const t0 = Date.now();
  const page = await browser.newPage();
  await page.setViewport({ width: J.w, height: J.h, deviceScaleFactor: J.dpr });
  await page.setRequestInterception(true);
  page.on("request", (req) => {
    const u = req.url();
    const m = u.match(/cdn\.jsdelivr\.net\/npm\/((?:three|es-module-shims)@[^/]+)\/(.*)$/);
    if (m) {
      const pkg = m[1].split("@")[0], file = path.join(here, "node_modules", pkg, m[2]);
      if (fs.existsSync(file)) return req.respond({ status: 200, headers: { "Access-Control-Allow-Origin": "*" }, contentType: "application/javascript", body: fs.readFileSync(file) });
      return req.respond({ status: 404, headers: { "Access-Control-Allow-Origin": "*" }, body: "" });
    }
    if (/fonts\.(googleapis|gstatic)\.com/.test(u)) return req.abort();
    req.continue();
  });
  const logs = [];
  page.on("pageerror", (e) => logs.push("ERR " + e.message));
  await page.goto(J.base + "&" + v.query, { waitUntil: "domcontentloaded", timeout: 120000 });
  try { await page.waitForFunction("window.__ready === true", { timeout: 600000, polling: 1000 }); }
  catch (e) { console.log("TIMEOUT", v.key, logs.join("\n")); await page.close(); continue; }
  await page.evaluate(() => { const b = document.getElementById("hideBar"); if (b) b.click(); });
  const info = await page.evaluate(() => window.__crowdInfo);
  // the field at the post
  await page.evaluate((dt) => { window.__setT(window.__T.finish + dt); window.__advance(3, 1 / 25); }, J.atFinish || -0.5);
  const tris = {};
  for (const [name, c] of Object.entries(J.views || {})) {
    await page.evaluate((c) => { window.__cam = c; window.__advance(2, 0); }, c);
    tris[name] = await page.evaluate(() => { try { return window.__count() - window.__count("crowd"); } catch { return null; } });
    await page.screenshot({ path: path.join(J.out, `${name}-${v.key}.png`) });
  }
  if (J.clip && J.clip.keys.includes(v.key)) {
    const dir = path.join(J.out, `clip-${v.key}`);
    fs.mkdirSync(dir, { recursive: true });
    const n = Math.round(J.clip.seconds * J.clip.fps);
    await page.evaluate((s) => { window.__cam = null; window.__setT(window.__T.finish - s); window.__advance(2, 1 / 25); }, J.clip.start);
    for (let k = 0; k < n; k++) {
      await page.evaluate((C) => {
        const [lx, lz] = window.__leader;
        window.__cam = { eye: [lx + C.eye[0], C.eye[1], lz + C.eye[2]], at: [lx + C.at[0], C.at[1], C.at[2]], fov: C.fov };
        window.__advance(1, 1 / C.fps);
      }, { ...J.clip.cam, fps: J.clip.fps });
      await page.screenshot({ path: path.join(dir, `f${String(k).padStart(4, "0")}.jpg`), type: "jpeg", quality: 90 });
    }
  }
  console.log(JSON.stringify({ key: v.key, secs: Math.round((Date.now() - t0) / 1000), tris, mix: info && info.mix, people: info && info.people, errors: logs.slice(0, 3) }));
  await page.close();
}
await browser.close();
