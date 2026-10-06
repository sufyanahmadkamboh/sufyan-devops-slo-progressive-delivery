// Screenshots the live dashboards while the lab runs, so the video shows what really happened.
//   node capture.mjs <out-dir> <browser-profile-dir> <stop-file>
// Every cycle saves grafana-<unix time>.png (the SLO dashboard) and argo-<unix time>.png (the Argo Rollouts
// dashboard), until <stop-file> exists. Both dashboards are reached through kubectl port-forward on localhost.
import { spawn } from "node:child_process";
import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { setTimeout as sleep } from "node:timers/promises";

const BROWSER = process.env.BROWSER || "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const PORT = 9343;
const [out, profile, stop] = process.argv.slice(2);
mkdirSync(out, { recursive: true });
const PAGES = [
  ["grafana", "http://localhost:3000/d/orders-api-slo?orgId=1&kiosk&from=now-15m&to=now", 6000],
  ["argo", "http://localhost:3100/rollouts/rollout/delivery/orders-api", 3500],
];

const browser = spawn(BROWSER, ["--headless=new", "--disable-gpu", "--hide-scrollbars", `--remote-debugging-port=${PORT}`,
  "--disable-extensions", "--disable-sync", "--no-first-run", "--disable-background-networking",
  `--user-data-dir=${profile}`, "about:blank"], { stdio: "ignore" });

let target;
for (let i = 0; i < 80 && !target; i++) {
  try { target = (await (await fetch(`http://127.0.0.1:${PORT}/json`)).json()).find(t => t.type === "page"); } catch { await sleep(250); }
}
if (!target) { console.error("browser did not start"); process.exit(1); }
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise(r => ws.addEventListener("open", r));
let id = 0;
const pending = new Map();
ws.addEventListener("message", e => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } });
const send = (method, params = {}) => new Promise(res => { const i = ++id; pending.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });

await send("Page.enable");
await send("Emulation.setDeviceMetricsOverride", { width: 1920, height: 1080, deviceScaleFactor: 1, mobile: false });
let n = 0;
while (!existsSync(stop)) {
  for (const [name, url, wait] of PAGES) {
    try {
      await send("Page.navigate", { url });
      await sleep(wait);
      const shot = await send("Page.captureScreenshot", { format: "png" });
      if (shot.result) writeFileSync(`${out}/${name}-${Math.floor(Date.now() / 1000)}.png`, Buffer.from(shot.result.data, "base64"));
      n++;
    } catch (e) { console.error(name, e.message); }
  }
}
console.log(`captured ${n} screenshots`);
ws.close();
browser.kill();
process.exit(0);
