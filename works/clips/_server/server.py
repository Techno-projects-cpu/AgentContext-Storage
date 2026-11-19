#!/usr/bin/env python3
"""Clip cutter: drop a video in the browser, get vertical clips back.

Runs a small local server that
  * accepts a video upload straight from your browser (drag and drop, no terminal),
  * cuts the launch-day clips with ffmpeg (credit burned in, 1080x1920),
  * lists the finished files so you can download them from the same page.

    python3 server.py [--port 8080]

Nothing leaves this machine: uploads land in works/clips/_incoming/, clips in each pack's shorts/.
"""
import argparse, json, os, re, shutil, subprocess, sys, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, unquote

HERE = os.path.dirname(os.path.abspath(__file__))
CLIPS = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(CLIPS, "..", ".."))
INCOMING = os.path.join(CLIPS, "_incoming")
STATE = {"file": None, "job": "idle", "log": [], "clips": [], "pack": None}
LOCK = threading.Lock()
MAX_BYTES = 12 * 1024 ** 3

PACKS = {
    "boss": {"dir": os.path.join(CLIPS, "gta6-launch"),
             "label": "Mrwhosetheboss — I Tested Every Single GTA",
             "who": "Mrwhosetheboss", "mins": (30, 70)},
    "speed": {"dir": os.path.join(CLIPS, "speed-gta6"),
              "label": "IShowSpeed — GTA 6 early access stream",
              "who": "IShowSpeed", "mins": (60, 800)},
}


def log(msg):
    with LOCK:
        STATE["log"].append(f"{time.strftime('%H:%M:%S')} {msg}")
        STATE["log"] = STATE["log"][-60:]
    print(msg, flush=True)


def env():
    e = dict(os.environ)
    e["PATH"] = "/tmp/fbin:" + e.get("PATH", "")
    e.setdefault("PY", "/tmp/venv/bin/python" if os.path.exists("/tmp/venv/bin/python") else "python3")
    return e


def probe_duration(path):
    try:
        p = subprocess.run(["/tmp/fbin/ffmpeg" if os.path.exists("/tmp/fbin/ffmpeg") else "ffmpeg",
                            "-nostdin", "-hide_banner", "-i", path],
                           capture_output=True, text=True, env=env())
        m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", p.stderr)
        if m:
            return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    except Exception as e:
        log(f"probe failed: {e}")
    return 0.0


def which_pack(dur):
    mins = dur / 60.0
    if mins < 1:
        return None
    best = min(PACKS.items(), key=lambda kv: abs(mins - sum(kv[1]["mins"]) / 2))
    if best[1]["mins"][0] <= mins <= best[1]["mins"][1]:
        return best[0]
    return "boss" if mins < 120 else "speed"


def run_pack(pack_key, src):
    p = PACKS[pack_key]
    d = p["dir"]
    STATE["pack"] = pack_key
    STATE["job"] = "cutting"
    STATE["clips"] = []
    log(f"cutting {p['label']}")
    try:
        if pack_key == "boss":
            ids = ["01", "02", "03", "04", "05"]
            script = [os.path.join(d, "capture.sh"), src, "all"]
        else:
            final = json.load(open(os.path.join(d, "candidates.json"), encoding="utf-8")) \
                .get("capture", {}).get("final", {})
            ids = sorted(final)
            if not ids:
                STATE["job"] = "needs-moments"
                log("no moments recorded yet: pick timestamps on the page")
                return
            script = [os.path.join(d, "capture.sh"), src, ids[0]] if len(ids) == 1 else \
                     [os.path.join(d, "capture.sh"), src, "all"]
        e = env()
        e["FR"] = "60" if pack_key == "speed" else "30000/1001"
        proc = subprocess.run(["bash"] + script, capture_output=True, text=True, env=e,
                              cwd=d, timeout=60 * 60 * 3)
        for line in (proc.stdout or "").splitlines():
            if line.strip():
                log(line.strip()[:160])
        found = sorted(os.listdir(os.path.join(d, "shorts"))) if os.path.isdir(
            os.path.join(d, "shorts")) else []
        STATE["clips"] = [{"name": f, "pack": pack_key} for f in found if f.endswith(".mp4")]
        if proc.returncode != 0:
            log("capture failed; last output: " + (proc.stderr or "")[-400:])
        log(f"done: {len(STATE['clips'])} clip(s)")
        STATE["job"] = "done" if STATE["clips"] else "failed"
    except Exception as e:
        log(f"error: {e}")
        STATE["job"] = "failed"


def cut_timestamps(pack_key, src, moments):
    """Cut specific moments for the speed pack, then re-list the outputs."""
    d = PACKS[pack_key]["dir"]
    py = env()["PY"]
    STATE["job"] = "cutting"
    for m in moments:
        args = [py, os.path.join(d, "tools", "set_moment.py"), m["id"],
                str(m["start"]), str(m["end"])]
        if m.get("hook"):
            args += ["--hook", m["hook"]]
        subprocess.run(args, cwd=d, env=env(), capture_output=True, text=True)
        e = env()
        e["FR"] = "60"
        r = subprocess.run(["bash", os.path.join(d, "capture.sh"), src, m["id"]],
                           cwd=d, env=e, capture_output=True, text=True)
        log(f"clip {m['id']}: {r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.returncode}")
    found = sorted(os.listdir(os.path.join(d, "shorts"))) if os.path.isdir(os.path.join(d, "shorts")) else []
    STATE["clips"] = [{"name": f, "pack": pack_key} for f in found if f.endswith(".mp4")]
    STATE["job"] = "done" if STATE["clips"] else "failed"


PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Clip cutter</title>
<style>
 :root{--y:#FFD400;--ink:#0b0b0d;--paper:#f5f3ee;--mute:#7d7870;--line:#e3dfd5}
 *{box-sizing:border-box}
 body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.6 ui-sans-serif,system-ui,sans-serif}
 .wrap{max-width:820px;margin:0 auto;padding:44px 22px 80px}
 h1{font-size:clamp(26px,4vw,38px);letter-spacing:-.02em;margin:0 0 6px}
 .sub{color:var(--mute);margin:0 0 26px}
 .drop{border:2px dashed #c9c3b6;border-radius:16px;background:#fff;padding:44px 22px;text-align:center;
       transition:.15s;cursor:pointer}
 .drop.hot{border-color:var(--y);background:#fffdf2}
 .drop b{display:block;font-size:19px;margin-bottom:6px}
 .drop small{color:var(--mute)}
 input[type=file]{display:none}
 .bar{height:8px;background:#e8e4da;border-radius:99px;overflow:hidden;margin:18px 0 6px;display:none}
 .bar i{display:block;height:100%;width:0;background:var(--y);transition:width .2s}
 .status{font:13px/1.6 ui-monospace,monospace;color:#55504a;white-space:pre-wrap;
         background:#fff;border:1px solid var(--line);border-radius:12px;padding:14px 16px;
         margin:18px 0;max-height:220px;overflow:auto;display:none}
 .clips{display:grid;gap:12px;margin-top:20px}
 .clip{display:flex;align-items:center;gap:14px;background:#fff;border:1px solid var(--line);
       border-radius:12px;padding:12px 14px}
 .clip b{flex:1;font:600 14px/1.4 ui-monospace,monospace}
 .clip a{background:var(--ink);color:#fff;text-decoration:none;padding:8px 14px;border-radius:8px;
         font-size:13px;font-weight:600}
 .clip a.alt{background:#fff;color:var(--ink);border:1px solid var(--line)}
 video{width:100%;max-width:260px;border-radius:10px;background:#000}
 .row{display:flex;gap:16px;flex-wrap:wrap;align-items:flex-start}
 h2{font:700 12px/1 ui-monospace,monospace;letter-spacing:.14em;text-transform:uppercase;
    color:#6b665e;margin:34px 0 8px}
 .mom{display:grid;grid-template-columns:56px 1fr 1fr auto;gap:8px;margin:8px 0;align-items:center}
 .mom input{width:100%;padding:8px 10px;border:1px solid var(--line);border-radius:8px;
            font:13px ui-monospace,monospace}
 .mom input[type=text]{font-family:ui-sans-serif,system-ui,sans-serif}
 .mom button{background:var(--y);border:0;border-radius:8px;padding:9px 14px;font-weight:700;
             cursor:pointer}
 .hint{color:var(--mute);font-size:13px}
</style></head>
<body><div class="wrap">
  <h1>Drop the video. Take the clips.</h1>
  <p class="sub">Five vertical clips for Mrwhosetheboss's GTA retrospective, or timestamped cuts
  for Speed's stream. Credit is burned in. Nothing is posted anywhere.</p>

  <div class="drop" id="drop">
    <b>Drag the .mp4 here</b>
    <small>or click to choose — 1080p is plenty, any length</small>
    <input type="file" id="file" accept="video/*,.mp4,.mkv,.webm,.mov">
    <div class="bar" id="bar"><i id="fill"></i></div>
    <div class="hint" id="pct"></div>
  </div>

  <div class="status" id="status"></div>
  <h2 id="cliph">Clips</h2>
  <div class="clips" id="clips"><p class="hint">Nothing yet.</p></div>

  <h2>Speed pack: pick moments yourself</h2>
  <p class="hint">Only needed for the Speed stream — its moments have to be seen. Give a start and
  end as <code>1:20:23</code> or seconds. Rows cut as soon as you hit Cut.</p>
  <div id="moments"></div>
</div>
<script>
const $ = s => document.querySelector(s);
const drop = $('#drop'), file = $('#file'), bar = $('#bar'), fill = $('#fill'),
      pct = $('#pct'), status = $('#status');

function logBox(t){ status.style.display='block'; status.textContent = t; }

async function poll(){
  try{
    const r = await fetch('api/status',{cache:'no-store'}); const s = await r.json();
    logBox(s.log.join('\n'));
    if(s.clips.length){
      const el = $('#clips'); el.innerHTML = '';
      for(const c of s.clips){
        const d = document.createElement('div'); d.className='clip';
        d.innerHTML = `<b>${c.name}</b>
          <a class="alt" href="clips/${c.pack}/${c.name}" target="_blank">watch</a>
          <a href="clips/${c.pack}/${c.name}" download>download</a>`;
        el.appendChild(d);
      }
    }
    if(s.job==='cutting' || s.job==='uploading') setTimeout(poll, 2500);
  }catch(e){}
}

async function send(f){
  bar.style.display='block';
  const xhr = new XMLHttpRequest();
  xhr.open('POST','api/upload');
  xhr.upload.onprogress = e => {
    if(e.lengthComputable){
      const p = Math.round(e.loaded/e.total*100);
      fill.style.width = p+'%'; pct.textContent = p+'%  ('+(e.loaded/1048576).toFixed(0)+' MB)';
    }
  };
  xhr.onload = () => { pct.textContent = 'uploaded — cutting now'; poll(); };
  xhr.onerror = () => { pct.textContent = 'upload failed'; };
  xhr.send(f);
  poll();
}

drop.onclick = () => file.click();
file.onchange = () => file.files[0] && send(file.files[0]);
['dragenter','dragover'].forEach(t => drop.addEventListener(t, e => {
  e.preventDefault(); drop.classList.add('hot');}));
['dragleave','drop'].forEach(t => drop.addEventListener(t, e => {
  e.preventDefault(); drop.classList.remove('hot');}));
drop.addEventListener('drop', e => {
  const f = e.dataTransfer.files[0];
  if(f) send(f);
});

function toSec(v, fb){
  if(!v) return fb;
  if(/^\d+(\.\d+)?$/.test(v)) return parseFloat(v);
  const p = v.split(':').map(Number);
  return p.length===3 ? p[0]*3600+p[1]*60+p[2] : p.length===2 ? p[0]*60+p[1] : parseFloat(v);
}

const rows = [
  ['01','First reaction','',''],
  ['02','Police stop rage','',''],
  ['03','Car-theft fail','',''],
  ['04','Leonida at night','',''],
  ['05','The gator','','']
];
const box = $('#moments');
rows.forEach(([id,label,a,b]) => {
  const d = document.createElement('div'); d.className='mom';
  d.innerHTML = `<b>${id}</b>
    <input type="text" placeholder="${label}" value="">
    <input type="text" placeholder="start e.g. 1:20:23" value="${a}">
    <input type="text" placeholder="end" value="${b}">
    <button>Cut</button>`;
  d.querySelector('button').onclick = async () => {
    const [lab, s, e] = d.querySelectorAll('input');
    if(!s.value || !e.value){ lab.placeholder='need a start and end'; return; }
    await fetch('api/cut',{method:'POST',headers:{'Content-Type':'application/json'},
      body: JSON.stringify({id, label: lab.value, start: toSec(s.value,0), end: toSec(e.value,0)})
    });
    logBox('cutting clip '+id+'…'); poll();
  };
  box.appendChild(d);
});
poll();
</script></body></html>
"""


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send(self, code, body, ctype="text/html; charset=utf-8", extra=None):
        b = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        u = urlparse(self.path)
        path = unquote(u.path)
        if path in ("/", "/index.html"):
            return self._send(200, PAGE)
        if path == "/api/status":
            with LOCK:
                return self._send(200, json.dumps(STATE), "application/json")
        m = re.match(r"^/clips/([a-z]+)/([-\w.]+\.mp4)$", path)
        if m:
            pack, name = m.groups()
            f = os.path.join(PACKS[pack]["dir"], "shorts", name)
            if os.path.isfile(f):
                size = os.path.getsize(f)
                self.send_response(200)
                self.send_header("Content-Type", "video/mp4")
                self.send_header("Content-Length", str(size))
                self.send_header("Content-Disposition",
                                 f'attachment; filename="{pack}-{name}"')
                self.end_headers()
                with open(f, "rb") as fh:
                    shutil.copyfileobj(fh, self.wfile)
                return
        return self._send(404, "not found")

    def do_POST(self):
        u = urlparse(self.path)
        if u.path == "/api/upload":
            length = int(self.headers.get("Content-Length") or 0)
            if length <= 0 or length > MAX_BYTES:
                return self._send(413, json.dumps({"error": "bad size"}), "application/json")
            os.makedirs(INCOMING, exist_ok=True)
            name = f"source-{int(time.time())}.mp4"
            dest = os.path.join(INCOMING, name)
            STATE["job"] = "uploading"
            log(f"receiving {length/1048576:.0f} MB")
            got = 0
            with open(dest, "wb") as fh:
                while got < length:
                    chunk = self.rfile.read(min(1024 * 512, length - got))
                    if not chunk:
                        break
                    fh.write(chunk)
                    got += len(chunk)
            log(f"saved {got/1048576:.0f} MB to _incoming/{name}")
            dur = probe_duration(dest)
            pack = which_pack(dur)
            log(f"duration {dur/60:.1f} min -> {pack} pack")
            STATE["file"] = name
            if pack:
                threading.Thread(target=run_pack, args=(pack, dest), daemon=True).start()
            else:
                STATE["job"] = "failed"
                if dur <= 0:
                    log("could not read this as video — try a plain .mp4")
                else:
                    log(f"only {dur:.0f}s long — too short to clip. That was maybe a preview file?")
            return self._send(200, json.dumps({"ok": True, "pack": pack, "minutes": dur / 60}),
                              "application/json")
        if u.path == "/api/cut":
            n = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(n) or b"{}")
            src = os.path.join(INCOMING, STATE["file"]) if STATE["file"] else None
            if not src or not os.path.isfile(src):
                return self._send(400, json.dumps({"error": "upload a video first"}), "application/json")
            m = {"id": body.get("id", "01"), "start": float(body.get("start", 0)),
                 "end": float(body.get("end", 0)), "hook": body.get("label") or ""}
            if m["end"] <= m["start"]:
                return self._send(400, json.dumps({"error": "end must be after start"}), "application/json")
            threading.Thread(target=cut_timestamps, args=("speed", src, [m]), daemon=True).start()
            return self._send(200, json.dumps({"ok": True}), "application/json")
        return self._send(404, "not found")

    def log_message(self, *a):
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8080)
    a = ap.parse_args()
    os.makedirs(INCOMING, exist_ok=True)
    srv = ThreadingHTTPServer(("0.0.0.0", a.port), H)
    print(f"clip cutter on 0.0.0.0:{a.port}", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
