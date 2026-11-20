#!/usr/bin/env python3
"""gen_docs.py - generate static docs for Kopi."""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs-new"
TPL_FILE = OUT / "assets" / "template.html"

VERSION = "1.54"

# Template
_tpl_cache = {}
def tpl():
    if "t" not in _tpl_cache:
        _tpl_cache["t"] = TPL_FILE.read_text(encoding="utf-8")
    return _tpl_cache["t"]

def render(template, **kw):
    for k, v in kw.items():
        template = template.replace("{{" + k.upper() + "}}", v)
    return template

def esc(s):
    return s.replace("&", "&").replace("<", "<").replace(">", ">")

def highlight(code: str) -> str:
    code = esc(code)
    KW = r"\b(class|void|int|long|float|double|boolean|String|new|return|if|else|while|for|switch|case|default|break|continue|import|static|final|true|false|null|this|malloc|fn|do)\b"
    TP = r"\b(int|long|float|double|boolean|String|fn|byte|uint8|uint16|uint32|uint64|int8|int16|int32|int64)\b"
    out, i = [], 0
    while i < len(code):
        if code.startswith("//", i):
            j = code.find("\n", i)
            if j < 0: j = len(code)
            out.append(f'<span class="tok-com">{code[i:j]}</span>')
            i = j
            continue
        if code.startswith("/*", i):
            j = code.find("*/", i)
            if j < 0: j = len(code)
            out.append(f'<span class="tok-com">{code[i:j+2]}</span>')
            i = j + 2
            continue
        if code[i] == '"':
            j = i + 1
            while j < len(code) and (code[j] != '"' or code[j-1] == '\\'):
                j += 1
            out.append(f'<span class="tok-str">{code[i:j+1]}</span>')
            i = j + 1
            continue
        m = re.match(r'\b\d+\.?\d*[fFLL]?\b', code[i:])
        if m:
            out.append(f'<span class="tok-num">{m.group(0)}</span>')
            i += len(m.group(0))
            continue
        m = re.match(KW, code[i:])
        if m:
            out.append(f'<span class="tok-kw">{m.group(0)}</span>')
            i += len(m.group(0))
            continue
        m = re.match(TP, code[i:])
        if m:
            out.append(f'<span class="tok-type">{m.group(0)}</span>')
            i += len(m.group(0))
            continue
        m = re.match(r'\w+', code[i:])
        if m:
            out.append(m.group(0))
            i += len(m.group(0))
            continue
        out.append(code[i])
        i += 1
    return "".join(out)

def cblock(code: str, lang: str = "kopi") -> str:
    return f'''<div class="code-block">
  <div class="code-header"><span class="code-lang">{lang}</span><button class="code-copy"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg><span>Salin</span></button></div>
  <pre><code>{highlight(code)}</code></pre>
</div>'''

NAV_ITEMS = [
    ("Panduan", "index.html", "home", [
        ("Mulai Cepat", "mulai_cepat.html", "stable"),
        ("Bahasa Kopi", "bahasa_kopi.html", "stable"),
        ("Compiler (kopicc)", "compiler_kopicc.html", "stable"),
        ("Virtual Machine (kopivm)", "virtual_machine_kopivm.html", "stable"),
        ("Build System", "build_system.html", "beta"),
    ]),
    ("Pustaka Inti (lib/)", "api/core/Arrays.html", "package", [
        ("core/", "api/core/Arrays.html", "stable"),
        ("compress/", "api/compress/Compress.html", "beta"),
        ("crypto/", "api/crypto/Crypto.html", "beta"),
        ("data/", "api/data/Json.html", "stable"),
        ("db/", "api/db/Sqlite.html", "beta"),
        ("encoding/", "api/encoding/Base64.html", "stable"),
        ("io/", "api/io/File.html", "stable"),
        ("net/", "api/net/Http.html", "beta"),
        ("system/", "api/system/Chan.html", "stable"),
        ("text/", "api/text/Str.html", "stable"),
        ("web/", "api/web/Http.html", "beta"),
    ]),
    ("Game Engine (lib/game/)", "api/game/core/Engine.html", "cube", [
        ("core/", "api/game/core/Engine.html", "stable"),
        ("math/", "api/game/math/Vec2.html", "stable"),
        ("render/2d/", "api/game/render2d/SpriteBatch.html", "stable"),
        ("render/3d/", "api/game/render3d/Renderer3D.html", "stable"),
        ("render/backend/", "api/game/render_backend/GlesSubmit.html", "stable"),
        ("animation/", "api/game/animation/AnimationClip.html", "beta"),
        ("audio/", "api/game/audio/Audio.html", "beta"),
        ("scene/", "api/game/scene/Scene.html", "beta"),
        ("physics/2d/", "api/game/physics2d/Body2D.html", "beta"),
        ("input/", "api/game/input/InputManager.html", "stable"),
        ("ui/", "api/game/ui/Widget.html", "beta"),
        ("util/", "api/game/util/Fps.html", "beta"),
    ]),
]

ICON_MAP = {
    "home": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
    "package": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>',
    "cube": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="2" width="20" height="20" rx="2"/><path d="M16 2v20"/><path d="M2 16h20"/></svg>',
}

CURRENT_URL = ""

def build_nav():
    parts = []
    for section_title, section_url, section_icon, items in NAV_ITEMS:
        parts.append(f'<div class="nav-section-title">{section_title}</div>')
        for title, url, status in items:
            active = " active" if url == CURRENT_URL else ""
            parts.append(f'<a class="nav-item{active}" href="{url}"><span class="nav-icon">{ICON_MAP.get(section_icon, ICON_MAP["package"])}</span>{title}<span class="nav-badge {status}">{status}</span></a>')
    return "\n".join(parts)

def page(title, category, status, breadcrumb, content, prev="", next_link="", toc=""):
    html = render(tpl(),
        TITLE=title, VERSION=VERSION, CATEGORY=category, STATUS=status,
        ROOT="../", BREADCRUMB=breadcrumb, CONTENT=content,
        PREV=prev, NEXT=next_link, NAV=build_nav(), TOC=toc
    )
    fname = title.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_") + ".html"
    (OUT / fname).write_text(html, encoding="utf-8")
    print(f"Generated {fname}")

# ==================== PAGE CONTENT LOADERS ====================

def load_content(name):
    """Load content from separate files."""
    path = OUT / "content" / f"{name}.txt"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""

def gen_index():
    global CURRENT_URL
    CURRENT_URL = "index.html"
    content = load_content("index") or """
<p class="lead">Kopi \u2014 bahasa & runtime untuk sistem, game, dan layanan jaringan. Kompilasi native (aarch64/x86-64) atau bytecode portable (VM). Tidak ada dependensi runtime; satu binary <code>kopivm</code> menjalankan <code>.kbc</code> di mana saja.</p>
<h2>Cepat Mulai</h2>
""" + cblock("""cd ~/kopi
make            # build kopicc & kopivm
./kopicc hello.kop -t vm -o hello.kbc
./kopivm hello.kbc""", "sh") + """
<h2>Arsitektur Singkat</h2>
<div class="card-grid">
  <a class="card" href="bahasa.html"><div class="card-icon" style="background:rgba(88,166,255,0.15);color:#58a6ff">&#128221;</div><div class="card-title">Bahasa</div><div class="card-desc">Sintaks mirip Java/C#, tipe statis, inferensi lokal, closure, generik, pattern matching.</div></a>
  <a class="card" href="compiler.html"><div class="card-icon" style="background:rgba(188,140,255,0.15);color:#bc8cff">&#9881;</div><div class="card-title">Compiler (kopicc)</div><div class="card-desc">Target a64 (ARM), x64 (PC), vm (bytecode KOP1). Output assembly atau .kbc.</div></a>
  <a class="card" href="vm.html"><div class="card-icon" style="background:rgba(63,185,80,0.15);color:#3fb950">&#128471;</div><div class="card-title">Virtual Machine</div><div class="card-desc">Interpreter register-based, JIT aarch64, builtin Net.* (socket, GL, audio, thread, channel).</div></a>
  <a class="card" href="api/core/Arrays.html"><div class="card-icon" style="background:rgba(255,166,87,0.15);color:#ffa657">&#128187;</div><div class="card-title">Pustaka Inti</div><div class="card-desc">core, compress, crypto, data, db, encoding, io, net, system, text, web.</div></a>
  <a class="card" href="api/game/core/Engine.html"><div class="card-icon" style="background:rgba(255,109,96,0.15);color:#f85149">&#127918;</div><div class="card-title">Game Engine</div><div class="card-desc">ECS, render 2D/3D, physics, audio, UI, scene graph, animation, input, networking.</div></a>
  <a class="card" href="android.html"><div class="card-icon" style="background:rgba(160,210,100,0.15);color:#7ee787">&#128241;</div><div class="card-title">Android</div><div class="card-desc">libkopivm.so + JNI, AAssetManager, OpenSL/OpenAL, Vulkan/GLES.</div></a>
</div>
<h2>Versi & Status</h2>
<div class="table-wrap"><table><thead><tr><th>Komponen</th><th>Versi</th><th>Status</th><th>Catatan</th></tr></thead><tbody>
<tr><td>kopicc</td><td>1.54</td><td><span style="color:#3fb950">Stabil</span></td><td>Target a64/x64/vm, JIT aarch64</td></tr>
<tr><td>kopivm</td><td>1.54</td><td><span style="color:#3fb950">Stabil</span></td><td>Interpreter + JIT, builtin Net.*, GL, audio, thread</td></tr>
<tr><td>lib/core</td><td>1.54</td><td><span style="color:#3fb950">Stabil</span></td><td>Collections, Math, MapStr, Bytes, BigInt</td></tr>
<tr><td>lib/system</td><td>1.54</td><td><span style="color:#3fb950">Stabil</span></td><td>Chan, Mutex, threadspawn, File, Env</td></tr>
<tr><td>lib/game/render</td><td>1.54</td><td><span style="color:#3fb950">Stabil</span></td><td>Renderer2D/3D, SpriteBatch, Camera3D, Mesh</td></tr>
<tr><td>lib/game/physics</td><td>1.54</td><td><span style="color:#d29922">Beta</span></td><td>2D lengkap, 3D eksperimental</td></tr>
<tr><td>lib/game/ui</td><td>1.54</td><td><span style="color:#d29922">Beta</span></td><td>Flex/Grid layout, fokus, virtual list</td></tr>
<tr><td>lib/crypto</td><td>1.54</td><td><span style="color:#d29922">Beta</span></td><td>AES-GCM, ChaCha20-Poly1305, Ascon, BLAKE2b</td></tr>
</tbody></table></div>"""
    page("Dokumentasi Kopi", "Home", "Stable", "", content,
         next_link='<a class="page-link next" href="mulai.html"><span class="page-label">Next</span><span class="page-title">Mulai Cepat &rarr;</span></a>')

def gen_mulai():
    global CURRENT_URL
    CURRENT_URL = "mulai.html"
    content = load_content("mulai") or """
<h2>1. Persiapan</h2>
<p>Kopi butuh compiler C (clang/gcc) dan <code>make</code>. Di Termux (Android):</p>
""" + cblock("""pkg install clang make git python3
git clone https://github.com/kopi-lang/kopi
cd kopi
make""", "sh") + """
<h2>2. Verifikasi Build</h2>
""" + cblock("""./kopicc --version
# kopicc 1.54.0 (Kopi) \u2014 target a64 | x64 | vm
./kopivm --version
# kopivm 1.54.0 (Kopi VM)""", "sh") + """
<h2>3. Program Pertama</h2>
""" + cblock("""class Main {
    static void main() {
        System.out.println("Halo dunia dari Kopi!");
    }
}""", "kopi") + """
<p>Simpan sebagai <code>hello.kop</code>, lalu kompilasi:</p>
<div class="tabs">
  <div class="tab-list">
    <button class="tab-btn active" data-target="#t-vm">VM (Portable)</button>
    <button class="tab-btn" data-target="#t-a64">Native ARM64</button>
    <button class="tab-btn" data-target="#t-x64">Native x86-64</button>
  </div>
  <div class="tab-pane active" id="t-vm">
""" + cblock("""# Bytecode portable (jalan di mana saja ada kopivm)
./kopicc hello.kop -t vm -o hello.kbc
./kopivm hello.kbc
# Halo dunia dari Kopi!""", "sh") + """
<p>Format <code>.kbc</code> adalah bytecode KOP1 v1. Bisa dijalankan di Android via <code>libkopivm.so</code> atau desktop via <code>kopivm</code>.</p></div>
  <div class="tab-pane" id="t-a64">
""" + cblock("""# Native aarch64 (di HP/ARM server)
./kopicc hello.kop -t a64 -o hello.s
cc hello.s -o hello
./hello""", "sh") + """<p>Output assembly ARM64 manual-readable. Cocok untuk embedded/ARM server.</p></div>
  <div class="tab-pane" id="t-x64">
""" + cblock("""# Native x86-64 (di PC Linux/macOS)
./kopicc hello.kop -t x64 -o hello64.s
cc hello64.s -o hello64
./hello64""", "sh") + """<p>Untuk cek sintaks tanpa menjalankan: <code>cc -target x86_64-linux-gnu -c hello64.s -o /dev/null</code></p></div></div>
<h2>4. Multi-file Project</h2>
""" + cblock("""# util.kop
class Util {
    static int kali(int a, int b) { return a * b; }
}
# main.kop
import "util.kop";
class Main {
    static void main() {
        System.out.println(Util.kali(6, 7));  // 42
    }
}
# Compile together
./kopicc main.kop util.kop -t vm -o app.kbc""", "kopi") + """
<div class="alert alert-info"><svg class="alert-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg><div><strong>Tip:</strong> Urutan file di CLI tidak penting \u2014 kopicc resolve dependensi otomatis. File yang sama (realpath) hanya dikompilasi sekali.</div></div>
<h2>5. Import Library</h2>
""" + cblock("""import Str;              # lib/text/Str.kop
import Json;             # lib/data/Json.kop
import Chan;             # lib/system/Chan.kop
import Renderer3D;       # lib/game/render/3d/Renderer3D.kop
import "local_util.kop"; # relatif ke file ini""", "kopi") + """
<p>Urutan pencarian <code>import Nama;</code>:</p>
<ol><li>Folder file pengimpor \u2014 <code>Nama.kop</code>, lalu <code>nama.kop</code> (lokal menang)</li><li><code>lib/</code> di samping <code>kopicc</code> (override dengan <code>KOPPATH</code>)</li><li>Subfolder <code>lib/<kategori>/Nama.kop</code></li></ol>
<h2>6. Argumen Program</h2>
""" + cblock("""import Str;
class Main {
    static void main(String[] args) {
        int port = 8080;
        if (Net.argc() > 0) port = Str.toInt(Net.argv(0));
        System.out.println("Port: " + port);
    }
}""", "kopi") + cblock("""./app 9090           # port = 9090
./kopivm app.kbc 9090""", "sh") + """
<h2>7. Alur Kerja Ringkas</h2>
<pre style="background:var(--bg-code);padding:16px;border-radius:8px;overflow-x:auto;text-align:center;font-family:monospace;font-size:13px;line-height:1.8;color:var(--text-primary)">
source .kop
    |
    +---> lex / parse / type check ---> AST
    |                                     |
    |                     +---------------+---------------+
    |                     v                               v
    |              gen (a64/x64)                      gen (vm)
    |                     |                               |
    |                     v                               v
    |              .s (assembly)                      .kbc (KOP1)
    |                     |                               |
    |                     v                               v
    |              cc (clang/gcc)                     kopivm
    |                     |                               |
    +---------------------> binary <---------------------+
</pre>
<div class="alert alert-success"><svg class="alert-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg><div><strong>Best practice:</strong> Gunakan <code>-t vm</code> untuk iterasi cepat (error runtime VM lebih mudah dibaca). Build native (<code>-t a64</code>/<code>-t x64</code>) hanya untuk rilis performa.</div></div>
<h2>8. Kesalahan Umum</h2>
<div class="table-wrap"><table><thead><tr><th>Gejala</th><th>Sebab / Solusi</th></tr></thead><tbody>
<tr><td><code>tidak ada metode main()</code></td><td>Tidak ada <code>static void main(...)</code> di class manapun</td></tr>
<tr><td><code>variabel lokal wajib diinisialisasi</code></td><td><code>int x;</code> tidak boleh; tulis <code>int x = 0;</code></td></tr>
<tr><td><code>metode String 'trim' butuh 'import Str;'</code></td><td>Tambahkan <code>import Str;</code> di atas file</td></tr>
<tr><td><code>arena malloc habis</code></td><td>Alokasi melewati batas <code>malloc<...></code> (atau 4096 MB untuk <code>malloc{}</code> otomatis)</td></tr>
<tr><td><code>array tidak valid</code></td><td>Indeks negatif / >= panjang; cek <code>.length</code></td></tr>
<tr><td><code>tipe tidak dikenal</code></td><td>Typo nama class, atau import salah (periksa huruf besar/kecil)</td></tr>
<tr><td><code>builtin Net.xxx tidak ada</code></td><td>Versi VM tidak cocok; update <code>kopivm</code> ke versi terbaru</td></tr>
</tbody></table></div>"""
    page("Mulai Cepat", "Panduan", "Stable",
         '<span class="sep">/</span><span class="current">Mulai Cepat</span>',
         content,
         '<a class="page-link" href="index.html"><span class="page-label">Previous</span><span class="page-title">&larr; Dokumentasi</span></a>',
         '<a class="page-link next" href="bahasa.html"><span class="page-label">Next</span><span class="page-title">Bahasa Kopi &rarr;</span></a>',
         "<a href=\"#1-persiapan\">1. Persiapan</a><a href=\"#2-verifikasi-build\">2. Verifikasi Build</a><a href=\"#3-program-pertama\">3. Program Pertama</a><a href=\"#4-multi-file-project\">4. Multi-file Project</a><a href=\"#5-import-library\">5. Import Library</a><a href=\"#6-argumen-program\">6. Argumen Program</a><a href=\"#7-alur-kerja-ringkas\">7. Alur Kerja Ringkas</a><a href=\"#8-kesalahan-umum\">8. Kesalahan Umum</a>")

# Stub implementations for other pages
def gen_bahasa():
    global CURRENT_URL
    CURRENT_URL = "bahasa.html"
    content = load_content("bahasa") or "<p>Bahasa Kopi reference page. Content to be expanded.</p>"
    page("Bahasa Kopi", "Panduan", "Stable",
         '<span class="sep">/</span><span class="current">Bahasa Kopi</span>',
         content,
         '<a class="page-link" href="mulai.html"><span class="page-label">Previous</span><span class="page-title">&larr; Mulai Cepat</span></a>',
         '<a class="page-link next" href="compiler.html"><span class="page-label">Next</span><span class="page-title">Compiler (kopicc) &rarr;</span></a>',
         "")

def gen_compiler():
    global CURRENT_URL
    CURRENT_URL = "compiler.html"
    content = load_content("compiler") or "<p>Compiler reference page. Content to be expanded.</p>"
    page("Compiler (kopicc)", "Panduan", "Stable",
         '<span class="sep">/</span><span class="current">Compiler</span>',
         content,
         '<a class="page-link" href="bahasa.html"><span class="page-label">Previous</span><span class="page-title">&larr; Bahasa Kopi</span></a>',
         '<a class="page-link next" href="vm.html"><span class="page-label">Next</span><span class="page-title">Virtual Machine &rarr;</span></a>',
         "")

def gen_vm():
    global CURRENT_URL
    CURRENT_URL = "vm.html"
    content = load_content("vm") or "<p>VM reference page. Content to be expanded.</p>"
    page("Virtual Machine (kopivm)", "Panduan", "Stable",
         '<span class="sep">/</span><span class="current">Virtual Machine</span>',
         content,
         '<a class="page-link" href="compiler.html"><span class="page-label">Previous</span><span class="page-title">&larr; Compiler</span></a>',
         '<a class="page-link next" href="build.html"><span class="page-label">Next</span><span class="page-title">Build System &rarr;</span></a>',
         "")

def gen_build():
    global CURRENT_URL
    CURRENT_URL = "build.html"
    content = load_content("build") or "<p>Build system reference page. Content to be expanded.</p>"
    page("Build System", "Panduan", "Beta",
         '<span class="sep">/</span><span class="current">Build System</span>',
         content,
         '<a class="page-link" href="vm.html"><span class="page-label">Previous</span><span class="page-title">&larr; Virtual Machine</span></a>',
         '<a class="page-link next" href="android.html"><span class="page-label">Next</span><span class="page-title">Android &rarr;</span></a>',
         "")

def gen_android():
    global CURRENT_URL
    CURRENT_URL = "android.html"
    content = load_content("android") or "<p>Android integration page. Content to be expanded.</p>"
    page("Android Integration", "Platform", "Stable",
         '<span class="sep">/</span><span class="current">Android</span>',
         content,
         '<a class="page-link" href="build.html"><span class="page-label">Previous</span><span class="page-title">&larr; Build System</span></a>',
         '',
         "")

# ==================== API GENERATION ====================

def scan_lib(lib_path: Path):
    classes = {}
    for kop_file in lib_path.rglob("*.kop"):
        text = kop_file.read_text(encoding="utf-8")
        rel = kop_file.relative_to(ROOT / "lib")
        module_name = str(rel).replace("/", ".").replace(".kop", "")
        class_matches = re.findall(r'class\s+(\w+)\s*\{', text)
        for cls in class_matches:
            class_pattern = rf'class\s+{cls}\s*\{{([\s\S]*?)\n\}}'
            class_match = re.search(class_pattern, text)
            if class_match:
                class_body = class_match.group(1)
                methods = re.findall(r'(static\s+)?(\w+(?:\[\])?)\s+(\w+)\s*\(([^)]*)\)', class_body)
                fields = re.findall(r'(static\s+)?(\w+(?:\[\])?)\s+(\w+)\s*[=;]', class_body)
                if cls not in classes:
                    classes[cls] = {"module": module_name, "methods": [], "fields": [], "file": str(rel)}
                for m in methods:
                    classes[cls]["methods"].append({"static": bool(m[0]), "return": m[1], "name": m[2], "params": m[3].strip()})
                for f in fields:
                    classes[cls]["fields"].append({"static": bool(f[0]), "type": f[1], "name": f[2]})
    return classes

def gen_api_page(module_name: str, classes: dict):
    parts = module_name.split(".")
    cat = parts[1] if len(parts) > 1 else "core"
    category_map = {"core": "Core Library", "compress": "Compression", "crypto": "Cryptography",
        "data": "Data Formats", "db": "Database", "encoding": "Encoding",
        "io": "I/O", "net": "Network", "system": "System", "text": "Text",
        "web": "Web", "game": "Game Engine"}
    status_map = {"core": "Stable", "compress": "Beta", "crypto": "Beta", "data": "Stable",
        "db": "Beta", "encoding": "Stable", "io": "Stable", "net": "Beta",
        "system": "Stable", "text": "Stable", "web": "Beta", "game": "Beta"}
    cat_name = category_map.get(cat, cat.title())
    status = status_map.get(cat, "Beta")
    content_parts = [f'<h2>API Reference: <code>lib/{module_name.replace(".", "/")}</code></h2>']
    content_parts.append(f'<p>Module: <strong>{cat_name}</strong> \u2014 Status: <span style="color:{"#3fb950" if status=="Stable" else "#d29922"}">{status}</span></p>')
    for cls_name, info in sorted(classes.items()):
        content_parts.append(f'<h3 id="{cls_name.lower()}">class {cls_name}</h3>')
        content_parts.append(f'<p><small>File: <code>{info["file"]}</code></small></p>')
        if info["fields"]:
            content_parts.append('<h4>Fields</h4><div class="table-wrap"><table><thead><tr><th>Modifier</th><th>Type</th><th>Name</th></tr></thead><tbody>')
            for f in info["fields"]:
                mod = "static " if f["static"] else ""
                content_parts.append(f'<tr><td><code>{mod}</code></td><td><code>{f["type"]}</code></td><td><code>{f["name"]}</code></td></tr>')
            content_parts.append('</tbody></table></div>')
        if info["methods"]:
            content_parts.append('<h4>Methods</h4>')
            for m in info["methods"]:
                mod = "static " if m["static"] else ""
                params = m["params"] if m["params"] else ""
                ret = m["return"] if m["return"] != "void" else ""
                sig = f'<code>{mod}{ret} {m["name"]}({params})</code>'
                content_parts.append(f'<div class="api-sig">{sig}</div>')
                content_parts.append('<div class="api-desc">(Deskripsi dari source \u2014 lihat file untuk detail implementasi)</div>')
    content = "\n".join(content_parts)
    toc = "\n".join([f'<a href="#{cls_name.lower()}">{cls_name}</a>' for cls_name in sorted(classes.keys())])
    breadcrumb = f'<span class="sep">/</span><a href="../../api.html">API</a><span class="sep">/</span><span class="current">{cat_name}</span>'
    html = render(tpl(), TITLE=f"API: {cat_name}", VERSION=VERSION, CATEGORY=cat_name, STATUS=status,
        ROOT="../../", BREADCRUMB=breadcrumb, CONTENT=content, PREV='', NEXT='',
        NAV=build_nav(), TOC=toc)
    out_path = OUT / "api" / f"{module_name.replace('.', '_')}.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    print(f"Generated {out_path}")

def gen_all_api():
    lib_root = ROOT / "lib"
    all_classes = scan_lib(lib_root)
    modules = {}
    for cls_name, info in all_classes.items():
        mod = info["module"]
        if mod not in modules:
            modules[mod] = {}
        modules[mod][cls_name] = info
    for mod, classes in modules.items():
        gen_api_page(mod, classes)
    # API index
    content = '<h2>API Reference Index</h2><p>Semua pustaka standar di <code>lib/</code>.</p>'
    content += '<div class="card-grid">'
    for cat_key, cat_name in [("core", "Core"), ("compress", "Compression"), ("crypto", "Cryptography"),
        ("data", "Data Formats"), ("db", "Database"), ("encoding", "Encoding"),
        ("io", "I/O"), ("net", "Network"), ("system", "System"), ("text", "Text"),
        ("web", "Web"), ("game", "Game Engine")]:
        cnt = len([m for m in modules if m.startswith(cat_key)])
        content += f'<a class="card" href="{cat_key}/Arrays.html"><div class="card-title">{cat_name}</div><div class="card-desc">{cnt} modules</div></a>'
    content += '</div>'
    html = render(tpl(), TITLE="API Reference", VERSION=VERSION, CATEGORY="Reference", STATUS="Stable",
        ROOT="../", BREADCRUMB='<span class="current">API Reference</span>',
        CONTENT=content, PREV='', NEXT='', NAV=build_nav(), TOC="")
    (OUT / "api.html").write_text(html, encoding="utf-8")
    print("Generated api.html")

# ==================== MAIN ====================

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "content").mkdir(exist_ok=True)
    
    gen_index()
    gen_mulai()
    gen_bahasa()
    gen_compiler()
    gen_vm()
    gen_build()
    gen_android()
    gen_all_api()
    
    (OUT / "assets" / "css").mkdir(parents=True, exist_ok=True)
    (OUT / "assets" / "js").mkdir(parents=True, exist_ok=True)
    
    print("\nDocumentation generated in docs-new/")
    print(f"   Open {OUT}/index.html in browser")

if __name__ == "__main__":
    main()