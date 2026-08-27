# Colorpicker PWA Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把現有 colorpicker 產生成可由 GitHub Pages 發布、可加入主畫面的 PWA，並在進入 App 前加上共用密碼 gate。

**Architecture:** 保留現有 `web/` partials 作為 colorpicker source of truth，擴充 `scripts/build_web.py` 產生第三份 PWA output 到 `public/colorpicker/`。PWA-only 的 manifest、service worker、password gate 與 icon 都放在 `web/pwa/`，build 時注入或複製到 public output，不影響 ESP32 firmware 與 simulator output。

**Tech Stack:** Python standard library build script, static HTML/CSS/JavaScript, Web App Manifest, Service Worker, GitHub Actions Pages deployment.

---

## File Structure

- Modify: `scripts/build_web.py`
  - Keep existing `web/colorpicker.html` and `simulator/colorpicker.html` outputs.
  - Add `public/colorpicker/index.html` generation.
  - Inject PWA head tags, password gate markup, and password gate script only into the public PWA output.
  - Copy manifest, service worker, and icons into the PWA output folder.
- Create: `web/pwa/manifest.webmanifest`
  - Static source manifest with relative `start_url`, `scope`, and icon paths.
- Create: `web/pwa/service-worker.js`
  - Static app-shell cache for `./`, `./index.html`, `./manifest.webmanifest`, and icon files.
- Create: `web/pwa/password-gate.css`
  - CSS that hides the app while locked and shows a full-screen password panel.
- Create: `web/pwa/password-gate.js`
  - Client-side shared-password gate using SHA-256 hash `f88b158ea7a7a1a5e1ab3b1c69f0a3332402de920fe5aee1f02fd54db68947e1`.
- Create: `scripts/test_build_pwa.py`
  - Standard-library regression tests for generated PWA files and injected gate behavior.
- Modify: `package.json`
  - Add convenience scripts for building the generated colorpicker and running the PWA build tests.
- Create: `.github/workflows/deploy-colorpicker-pwa.yml`
  - GitHub Pages deployment from `public/colorpicker/`.
- Create: `docs/colorpicker_pwa_install_zh.md`
  - 繁體中文使用者安裝說明，使用 Money Home 類似流程描述。

---

### Task 1: Add PWA Source Files

**Files:**
- Create: `web/pwa/manifest.webmanifest`
- Create: `web/pwa/service-worker.js`
- Create: `web/pwa/password-gate.css`
- Create: `web/pwa/password-gate.js`

- [ ] **Step 1: Create the PWA source directory**

Run:

```bash
mkdir -p web/pwa
```

Expected: command exits with code 0.

- [ ] **Step 2: Create `web/pwa/manifest.webmanifest`**

Add exactly:

```json
{
  "name": "Penelope Color Picker",
  "short_name": "Color Picker",
  "description": "Penelope LED colorpicker controller",
  "start_url": "./",
  "scope": "./",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#ff385c",
  "orientation": "any",
  "icons": [
    {
      "src": "icons/icon-152.png",
      "sizes": "152x152",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any"
    }
  ]
}
```

- [ ] **Step 3: Create `web/pwa/service-worker.js`**

Add exactly:

```javascript
const CACHE_NAME = 'penelope-colorpicker-v1';
const APP_SHELL = [
  './',
  './index.html',
  './manifest.webmanifest',
  './icons/icon-152.png',
  './icons/icon-192.png',
  './icons/icon-512.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((names) => Promise.all(
        names.filter((name) => name !== CACHE_NAME).map((name) => caches.delete(name))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') {
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) {
        return cached;
      }
      return fetch(event.request);
    })
  );
});
```

- [ ] **Step 4: Create `web/pwa/password-gate.css`**

Add exactly:

```css
html.pwa-gate-pending body > :not(#pwaGate) {
  display: none !important;
}

#pwaGate {
  min-height: 100vh;
  padding: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #ffffff;
  color: #222222;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, system-ui, 'Segoe UI', Roboto, Arial, sans-serif;
}

html:not(.pwa-gate-pending) #pwaGate {
  display: none !important;
}

.pwaGateCard {
  width: min(100%, 360px);
  border: 1px solid #dddddd;
  border-radius: 14px;
  padding: 24px;
  background: #ffffff;
  box-shadow: rgba(0, 0, 0, 0.02) 0 0 0 1px, rgba(0, 0, 0, 0.04) 0 2px 6px 0;
}

.pwaGateTitle {
  margin: 0 0 8px;
  font-size: 22px;
  font-weight: 600;
  letter-spacing: 0;
}

.pwaGateText {
  margin: 0 0 16px;
  color: #6a6a6a;
  font-size: 14px;
}

.pwaGateLabel {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 600;
}

.pwaGateInput {
  width: 100%;
  min-height: 44px;
  padding: 10px 12px;
  border: 1px solid #dddddd;
  border-radius: 8px;
  font: inherit;
}

.pwaGateInput:focus {
  outline: none;
  border-color: #222222;
  box-shadow: 0 0 0 1px #222222;
}

.pwaGateButton {
  width: 100%;
  min-height: 44px;
  margin-top: 14px;
  border: 0;
  border-radius: 8px;
  background: #ff385c;
  color: #ffffff;
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}

.pwaGateButton:active {
  background: #e00b41;
}

.pwaGateError {
  min-height: 20px;
  margin: 10px 0 0;
  color: #c13515;
  font-size: 13px;
}
```

- [ ] **Step 5: Create `web/pwa/password-gate.js`**

Add exactly:

```javascript
(function () {
  const unlockKey = 'penelopeColorpickerUnlocked';
  const passwordHash = 'f88b158ea7a7a1a5e1ab3b1c69f0a3332402de920fe5aee1f02fd54db68947e1';
  const root = document.documentElement;
  const gate = document.getElementById('pwaGate');
  const form = document.getElementById('pwaGateForm');
  const input = document.getElementById('pwaGatePassword');
  const error = document.getElementById('pwaGateError');

  function canUseStorage() {
    try {
      const probe = '__penelope_storage_probe__';
      localStorage.setItem(probe, '1');
      localStorage.removeItem(probe);
      return true;
    } catch (err) {
      return false;
    }
  }

  const storageAvailable = canUseStorage();

  function isUnlocked() {
    try {
      return storageAvailable && localStorage.getItem(unlockKey) === '1';
    } catch (err) {
      return false;
    }
  }

  function showApp() {
    root.classList.remove('pwa-gate-pending');
    if (gate) {
      gate.setAttribute('hidden', 'hidden');
    }
  }

  function showError(message) {
    if (error) {
      error.textContent = message;
    }
  }

  async function sha256Hex(value) {
    const bytes = new TextEncoder().encode(value);
    const digest = await crypto.subtle.digest('SHA-256', bytes);
    return Array.from(new Uint8Array(digest))
      .map((byte) => byte.toString(16).padStart(2, '0'))
      .join('');
  }

  function registerServiceWorker() {
    if (!('serviceWorker' in navigator)) {
      return;
    }
    window.addEventListener('load', function () {
      navigator.serviceWorker.register('./service-worker.js').catch(function () {});
    });
  }

  if (isUnlocked()) {
    showApp();
    registerServiceWorker();
    return;
  }

  root.classList.add('pwa-gate-pending');
  if (gate) {
    gate.removeAttribute('hidden');
  }
  if (input) {
    input.focus();
  }

  if (!form || !input) {
    showError('Password form is unavailable.');
    return;
  }

  form.addEventListener('submit', async function (event) {
    event.preventDefault();
    const value = input.value.trim();
    if (!value) {
      showError('Please enter the password.');
      input.focus();
      return;
    }

    try {
      const hash = await sha256Hex(value);
      if (hash !== passwordHash) {
        showError('Password is incorrect.');
        input.select();
        return;
      }
      if (storageAvailable) {
        localStorage.setItem(unlockKey, '1');
      }
      showApp();
      registerServiceWorker();
    } catch (err) {
      showError('This browser cannot verify the password.');
    }
  });
})();
```

- [ ] **Step 6: Commit PWA source files**

Run:

```bash
git add web/pwa/manifest.webmanifest web/pwa/service-worker.js web/pwa/password-gate.css web/pwa/password-gate.js
git commit -m "feat: add colorpicker pwa source files"
```

Expected: commit succeeds and includes only the four `web/pwa/` files.

---

### Task 2: Generate GitHub Pages PWA Output

**Files:**
- Modify: `scripts/build_web.py`
- Generated by build: `public/colorpicker/index.html`
- Generated by build: `public/colorpicker/manifest.webmanifest`
- Generated by build: `public/colorpicker/service-worker.js`
- Generated by build: `public/colorpicker/icons/icon-152.png`
- Generated by build: `public/colorpicker/icons/icon-192.png`
- Generated by build: `public/colorpicker/icons/icon-512.png`

- [ ] **Step 1: Modify build path constants in `scripts/build_web.py`**

Near the existing `WEB_DIR`, `OUT_PATH`, and `SIM_ALIAS_OUT_PATH` constants, replace that block with:

```python
WEB_DIR = os.path.join(PROJECT_DIR, "web")
PWA_DIR = os.path.join(WEB_DIR, "pwa")
OUT_PATH = os.path.join(PROJECT_DIR, "web", "colorpicker.html")
SIM_ALIAS_OUT_PATH = os.path.join(PROJECT_DIR, "simulator", "colorpicker.html")
PWA_OUT_DIR = os.path.join(PROJECT_DIR, "public", "colorpicker")
PWA_OUT_PATH = os.path.join(PWA_OUT_DIR, "index.html")
```

- [ ] **Step 2: Add imports in `scripts/build_web.py`**

At the top with the existing imports, change:

```python
import os
import re
import json
```

to:

```python
import os
import re
import json
import shutil
import struct
import zlib
```

- [ ] **Step 3: Add helper functions after `_sub`**

Insert this code immediately after `_sub`:

```python
def _read_pwa(rel):
    with open(os.path.join(PWA_DIR, rel), "r", encoding="utf-8") as f:
        return f.read()


def _pwa_head_injection():
    css = _read_pwa("password-gate.css").rstrip("\n")
    return """  <meta name="theme-color" content="#ff385c">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-title" content="Color Picker">
  <meta name="apple-mobile-web-app-status-bar-style" content="default">
  <link rel="manifest" href="manifest.webmanifest">
  <link rel="apple-touch-icon" href="icons/icon-152.png">
  <style>
{css}
  </style>
  <script>
try {{
  if (localStorage.getItem('penelopeColorpickerUnlocked') !== '1') {{
    document.documentElement.classList.add('pwa-gate-pending');
  }}
}} catch (err) {{
  document.documentElement.classList.add('pwa-gate-pending');
}}
  </script>""".format(css=css)


def _pwa_gate_markup():
    return """  <section id="pwaGate" hidden>
    <form class="pwaGateCard" id="pwaGateForm" autocomplete="off">
      <h1 class="pwaGateTitle">Penelope Color Picker</h1>
      <p class="pwaGateText">請輸入密碼以進入 App。</p>
      <label class="pwaGateLabel" for="pwaGatePassword">Password</label>
      <input class="pwaGateInput" id="pwaGatePassword" name="password" type="password" inputmode="text" autocomplete="current-password">
      <button class="pwaGateButton" type="submit">Enter</button>
      <p class="pwaGateError" id="pwaGateError" role="alert" aria-live="polite"></p>
    </form>
  </section>"""


def _inject_pwa_shell(html):
    out = html.replace("<html>", "<html>", 1)
    out = out.replace("</head>", _pwa_head_injection() + "\n</head>", 1)
    out = out.replace("<body>", "<body>\n" + _pwa_gate_markup(), 1)
    out = out.replace("</body>", "  <script>\n" + _read_pwa("password-gate.js").rstrip("\n") + "\n  </script>\n</body>", 1)
    return out
```

- [ ] **Step 4: Add PNG icon generation helpers after `_inject_pwa_shell`**

Insert this code:

```python
def _png_chunk(tag, data):
    return (
        struct.pack(">I", len(data)) +
        tag +
        data +
        struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)
    )


def _write_png_icon(path, size):
    bg = (255, 56, 92, 255)
    fg = (255, 255, 255, 255)
    shadow = (224, 11, 65, 255)
    center = (size - 1) / 2.0
    radius = size * 0.24
    shadow_radius = size * 0.34
    rows = []
    for y in range(size):
        row = bytearray()
        row.append(0)
        for x in range(size):
            dx = x - center
            dy = y - center
            dist = (dx * dx + dy * dy) ** 0.5
            if dist <= radius:
                row.extend(fg)
            elif dist <= shadow_radius:
                row.extend(shadow)
            else:
                row.extend(bg)
        rows.append(bytes(row))

    raw = b"".join(rows)
    png = (
        b"\x89PNG\r\n\x1a\n" +
        _png_chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)) +
        _png_chunk(b"IDAT", zlib.compress(raw, 9)) +
        _png_chunk(b"IEND", b"")
    )
    with open(path, "wb") as f:
        f.write(png)
```

- [ ] **Step 5: Add PWA file copy helper after `_write_png_icon`**

Insert this code:

```python
def _copy_pwa_assets():
    os.makedirs(PWA_OUT_DIR, exist_ok=True)
    shutil.copyfile(
        os.path.join(PWA_DIR, "manifest.webmanifest"),
        os.path.join(PWA_OUT_DIR, "manifest.webmanifest"),
    )
    shutil.copyfile(
        os.path.join(PWA_DIR, "service-worker.js"),
        os.path.join(PWA_OUT_DIR, "service-worker.js"),
    )

    icons_dir = os.path.join(PWA_OUT_DIR, "icons")
    os.makedirs(icons_dir, exist_ok=True)
    for size in (152, 192, 512):
        _write_png_icon(os.path.join(icons_dir, "icon-" + str(size) + ".png"), size)
```

- [ ] **Step 6: Modify `build_colorpicker_html()` to emit PWA output**

Inside `build_colorpicker_html()`, after writing `SIM_ALIAS_OUT_PATH`, add:

```python
    _copy_pwa_assets()
    pwa_out = _inject_pwa_shell(out)
    with open(PWA_OUT_PATH, "w", encoding="utf-8") as f:
        f.write(HEADER_COMMENT)
        f.write(pwa_out)
```

Then add this print line after the existing simulator print:

```python
    print("[build_web] wrote {} (pwa, {} bytes)".format(PWA_OUT_PATH, len(pwa_out) + len(HEADER_COMMENT)))
```

- [ ] **Step 7: Run the build script**

Run:

```bash
python3 scripts/build_web.py
```

Expected output includes:

```text
[build_web] wrote /Users/all.are.mathematics/My Documents/FastLED project/Servo Test/web/colorpicker.html
[build_web] wrote /Users/all.are.mathematics/My Documents/FastLED project/Servo Test/simulator/colorpicker.html
[build_web] wrote /Users/all.are.mathematics/My Documents/FastLED project/Servo Test/public/colorpicker/index.html
```

- [ ] **Step 8: Inspect generated PWA files**

Run:

```bash
find public/colorpicker -maxdepth 3 -type f | sort
```

Expected output:

```text
public/colorpicker/icons/icon-152.png
public/colorpicker/icons/icon-192.png
public/colorpicker/icons/icon-512.png
public/colorpicker/index.html
public/colorpicker/manifest.webmanifest
public/colorpicker/service-worker.js
```

- [ ] **Step 9: Verify icon dimensions**

Run:

```bash
file public/colorpicker/icons/icon-152.png public/colorpicker/icons/icon-192.png public/colorpicker/icons/icon-512.png
```

Expected output contains:

```text
public/colorpicker/icons/icon-152.png: PNG image data, 152 x 152
public/colorpicker/icons/icon-192.png: PNG image data, 192 x 192
public/colorpicker/icons/icon-512.png: PNG image data, 512 x 512
```

- [ ] **Step 10: Commit build generation changes**

Run:

```bash
git add scripts/build_web.py public/colorpicker/index.html public/colorpicker/manifest.webmanifest public/colorpicker/service-worker.js public/colorpicker/icons/icon-152.png public/colorpicker/icons/icon-192.png public/colorpicker/icons/icon-512.png web/colorpicker.html simulator/colorpicker.html
git commit -m "feat: generate colorpicker pwa output"
```

Expected: commit succeeds and includes `scripts/build_web.py`, generated public PWA files, and regenerated colorpicker HTML outputs.

---

### Task 3: Add PWA Build Regression Tests

**Files:**
- Create: `scripts/test_build_pwa.py`
- Modify: `package.json`

- [ ] **Step 1: Create `scripts/test_build_pwa.py`**

Add exactly:

```python
import json
import pathlib
import subprocess
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
PWA_DIR = ROOT / "public" / "colorpicker"


class ColorpickerPwaBuildTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(
            ["python3", "scripts/build_web.py"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    def test_manifest_is_valid_and_installable(self):
        manifest = json.loads((PWA_DIR / "manifest.webmanifest").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "Penelope Color Picker")
        self.assertEqual(manifest["short_name"], "Color Picker")
        self.assertEqual(manifest["start_url"], "./")
        self.assertEqual(manifest["scope"], "./")
        self.assertEqual(manifest["display"], "standalone")
        self.assertEqual(manifest["theme_color"], "#ff385c")
        self.assertEqual(len(manifest["icons"]), 3)

    def test_index_contains_pwa_metadata_and_gate(self):
        html = (PWA_DIR / "index.html").read_text(encoding="utf-8")
        self.assertIn('<link rel="manifest" href="manifest.webmanifest">', html)
        self.assertIn('apple-mobile-web-app-capable', html)
        self.assertIn('id="pwaGate"', html)
        self.assertIn('id="pwaGatePassword"', html)
        self.assertIn('f88b158ea7a7a1a5e1ab3b1c69f0a3332402de920fe5aee1f02fd54db68947e1', html)
        shared_password = "".join(chr(code) for code in (68, 101, 115, 116, 105, 110, 121, 52, 55, 57, 52))
        self.assertNotIn(shared_password, html)

    def test_service_worker_and_icons_exist(self):
        service_worker = (PWA_DIR / "service-worker.js").read_text(encoding="utf-8")
        self.assertIn("CACHE_NAME", service_worker)
        self.assertIn("./index.html", service_worker)
        self.assertTrue((PWA_DIR / "icons" / "icon-152.png").is_file())
        self.assertTrue((PWA_DIR / "icons" / "icon-192.png").is_file())
        self.assertTrue((PWA_DIR / "icons" / "icon-512.png").is_file())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Add package scripts**

Modify `package.json` so it becomes:

```json
{
  "scripts": {
    "build:colorpicker": "python3 scripts/build_web.py",
    "test:pwa": "python3 -m unittest scripts/test_build_pwa.py",
    "build:sim-wasm": "bash simulator/wasm/build.sh",
    "diagnose:effects": "node simulator/diagnose_effects.js"
  }
}
```

- [ ] **Step 3: Run the regression tests**

Run:

```bash
python3 -m unittest scripts/test_build_pwa.py
```

Expected output ends with:

```text
Ran 3 tests

OK
```

- [ ] **Step 4: Commit tests and package scripts**

Run:

```bash
git add scripts/test_build_pwa.py package.json
git commit -m "test: cover colorpicker pwa build output"
```

Expected: commit succeeds and includes only the test file and `package.json`.

---

### Task 4: Add GitHub Pages Deployment Workflow

**Files:**
- Create: `.github/workflows/deploy-colorpicker-pwa.yml`

- [ ] **Step 1: Create `.github/workflows/deploy-colorpicker-pwa.yml`**

Add exactly:

```yaml
name: Deploy Colorpicker PWA

on:
  push:
    branches:
      - main
    paths:
      - "web/**"
      - "scripts/build_web.py"
      - "scripts/test_build_pwa.py"
      - ".github/workflows/deploy-colorpicker-pwa.yml"
      - "data/html/logo.png"
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Pages
        uses: actions/configure-pages@v5

      - name: Build colorpicker PWA
        run: python3 scripts/build_web.py

      - name: Test colorpicker PWA
        run: python3 -m unittest scripts/test_build_pwa.py

      - name: Upload Pages artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: public/colorpicker

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

- [ ] **Step 2: Commit deployment workflow**

Run:

```bash
git add .github/workflows/deploy-colorpicker-pwa.yml
git commit -m "ci: deploy colorpicker pwa to pages"
```

Expected: commit succeeds and includes only the new workflow.

---

### Task 5: Add Traditional Chinese Install Instructions

**Files:**
- Create: `docs/colorpicker_pwa_install_zh.md`

- [ ] **Step 1: Create `docs/colorpicker_pwa_install_zh.md`**

Add exactly:

```markdown
# Penelope Color Picker 安裝說明

這個 Color Picker 可以像 App 一樣放到手機主畫面。它其實是 Web App，所以更新時只需要開發者更新 GitHub Pages，使用者再次打開時就會拿到新版。

第一次進入時需要輸入共用密碼。

## iOS 安裝步驟

1. 複製 GitHub Pages 的 Color Picker 網址，並用 Safari 打開。
2. 輸入共用密碼進入 App。
3. 點 Safari 的分享按鈕。
4. 選擇「加入主畫面」。
5. 名稱可以保留 `Color Picker`，也可以改成自己喜歡的名字。
6. 之後就可以從主畫面直接打開。

## Android 安裝步驟

1. 複製 GitHub Pages 的 Color Picker 網址，並用 Google Chrome 打開。
2. 輸入共用密碼進入 App。
3. 點右上角的三點選單。
4. 選擇「加入主畫面」或「安裝應用程式」。
5. 如果 Chrome 顯示 `Install` 和 `Shortcut`，選擇 `Install`，使用體驗會比較像 App。
6. 之後就可以從主畫面直接打開。

## 使用注意

- 這個密碼畫面是基本阻擋，不是真正的帳號登入。
- 如果清除 Safari 或 Chrome 的網站資料，下次打開會需要重新輸入密碼。
- 如果 App 沒有更新，可以關掉後重新打開，或在瀏覽器中重新整理頁面。
```

- [ ] **Step 2: Commit install instructions**

Run:

```bash
git add docs/colorpicker_pwa_install_zh.md
git commit -m "docs: add colorpicker pwa install guide"
```

Expected: commit succeeds and includes only the install guide.

---

### Task 6: Final Verification

**Files:**
- Verify generated output and docs.

- [ ] **Step 1: Run PWA build tests**

Run:

```bash
python3 -m unittest scripts/test_build_pwa.py
```

Expected output ends with:

```text
Ran 3 tests

OK
```

- [ ] **Step 2: Run existing colorpicker build**

Run:

```bash
python3 scripts/build_web.py
```

Expected output includes all three generated outputs:

```text
web/colorpicker.html
simulator/colorpicker.html
public/colorpicker/index.html
```

- [ ] **Step 3: Serve the PWA locally**

Run:

```bash
python3 -m http.server 8765 --directory public/colorpicker
```

Expected: server starts and prints:

```text
Serving HTTP on :: port 8765
```

Keep this command running until Step 6 completes.

- [ ] **Step 4: Verify HTTP files from another terminal**

Run:

```bash
curl -I http://127.0.0.1:8765/
curl -I http://127.0.0.1:8765/manifest.webmanifest
curl -I http://127.0.0.1:8765/service-worker.js
```

Expected: each command returns `HTTP/1.0 200 OK` or `HTTP/1.1 200 OK`.

- [ ] **Step 5: Verify browser behavior with headless Chrome**

Run:

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --headless=new --disable-gpu --dump-dom http://127.0.0.1:8765/
```

Expected output contains:

```text
id="pwaGate"
Penelope Color Picker
```

Expected output does not contain:

```text
the plaintext shared password
```

- [ ] **Step 6: Stop the local HTTP server**

Press `Ctrl-C` in the terminal running:

```bash
python3 -m http.server 8765 --directory public/colorpicker
```

Expected: server stops.

- [ ] **Step 7: Check git status**

Run:

```bash
git status --short
```

Expected: no output.

If `web/colorpicker.html`, `simulator/colorpicker.html`, or `public/colorpicker/index.html` changed after final build, commit the regenerated files:

```bash
git add web/colorpicker.html simulator/colorpicker.html public/colorpicker/index.html
git commit -m "build: refresh colorpicker pwa artifacts"
```

Expected: final `git status --short` has no output.
