<<<<<<< HEAD
<p align="center">
  <img src="GBrowser.ico" alt="GBrowser Logo" width="96" height="96">
</p>

<h1 align="center">🌐 GBrowser</h1>

<p align="center">
  <strong>A full-featured, privacy-first web browser built with Python</strong><br>
  <em>Ported from the original Ceprkac C# browser — now cross-platform with PyQt6</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-5.4-blue?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/python-3.13+-green?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/engine-Chromium%20(QtWebEngine)-orange?style=flat-square" alt="Engine">
  <img src="https://img.shields.io/badge/license-proprietary-red?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/platform-Windows-0078D6?style=flat-square&logo=windows&logoColor=white" alt="Platform">
</p>

---

## 📖 About

GBrowser is a lightweight desktop web browser with a strong focus on **ad blocking** and **privacy**. It ships with a built-in ad blocker covering 300+ tracking and advertising domains, a password manager with encrypted storage, and a Chrome-style dark UI — all in a single Python file.

Originally written in C# as **Ceprkac**, the browser has been fully ported to Python 3.13 using PyQt6 and PyQt6-WebEngine, keeping feature parity with the original while gaining the flexibility of the Python ecosystem.

---

## ✨ Features

### 🛡️ Privacy & Ad Blocking
- **Built-in ad blocker** — blocks 300+ ad/tracking domains at the network level via request interception
- **DOM-level ad removal** — injects CSS and JavaScript to hide ad elements on pages
- **YouTube-specific ad blocking** — dedicated blocker that skips video ads, removes overlay ads, and strips ad data from YouTube API responses
- **Main-world script injection** — intercepts `JSON.parse`, `fetch`, and `XMLHttpRequest` to block ads before they render
- **Custom blocklist support** — load additional domains from `blocklist.txt`
- **Whitelist system** — banking, auth, AI services, gaming platforms, and other essential sites are never blocked

### 🔐 Password Manager
- **Encrypted credential storage** — uses Windows DPAPI on Windows, Fernet (AES-128) fallback on other platforms
- **Auto-fill** — detects login forms and fills saved credentials automatically
- **Multi-account picker** — choose between multiple saved accounts for the same site
- **CSV import** — import passwords from Chrome/Edge export format
- **Input sanitization** — length limits and control character filtering on import

### 🗂️ Tabs
- **Chrome-style custom tab strip** — owner-drawn tabs with hover effects, loading progress bars, and close buttons
- **Drag-to-reorder** tabs
- **Middle-click to close** tabs
- **Tab restore** — reopen recently closed tabs with `Ctrl+Shift+T`
- **Tab cycling** — `Ctrl+Tab` / `Ctrl+Shift+Tab` to switch between tabs
- **Per-tab zoom** — each tab remembers its own zoom level

### 🔖 Bookmarks
- **Bookmark bar** with overflow menu (`»`) for large collections
- **Folder support** — organize bookmarks into nested folders
- **HTML import/export** — compatible with Netscape bookmark format (Chrome, Firefox, Edge)
- **One-click toggle** — `Ctrl+D` to add or remove a bookmark
- **Incremental UI updates** — bookmark bar only redraws when data changes

### 🔍 Navigation & Search
- **Smart address bar** — auto-detects URLs vs search queries
- **6 search engines** — Google, Bing, DuckDuckGo, Yahoo, Brave Search, Startpage
- **Autocomplete** — suggestions from history and bookmarks as you type
- **Find in page** — `Ctrl+F` with live search, next/prev navigation
- **Zoom controls** — `Ctrl+Plus` / `Ctrl+Minus` / `Ctrl+0`

### 🔑 OAuth & Authentication
- **OAuth popup handling** — Google, Apple, Microsoft, Twitter/X, and other OAuth flows open correctly in new tabs
- **Auth callback auto-close** — OAuth callback tabs close automatically after authentication completes
- **Auth domain whitelist** — login flows are never blocked by the ad blocker

### 📥 Downloads
- **Download manager** — dialog showing recent downloads with progress tracking
- **Save-as dialog** — choose where to save each download
- **Status bar progress** — live download progress in the status bar

### 🎨 Interface
- **Dark theme** — Chrome-dark inspired color palette throughout
- **Dark title bar** — native Windows dark title bar integration via DWM API
- **DevTools** — built-in Chromium DevTools accessible via `Ctrl+I`
- **Window state persistence** — remembers position, size, and maximized state
- **Status bar** — shows ad block count, loading status, zoom level, and download progress

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+T` | New tab |
| `Ctrl+W` | Close current tab |
| `Ctrl+Shift+T` | Restore closed tab |
| `Ctrl+Tab` | Next tab |
| `Ctrl+Shift+Tab` | Previous tab |
| `Ctrl+L` | Focus address bar |
| `Ctrl+D` | Toggle bookmark |
| `Ctrl+F` | Find in page |
| `Ctrl+I` | Open DevTools |
| `Ctrl+Plus` | Zoom in |
| `Ctrl+Minus` | Zoom out |
| `Ctrl+0` | Reset zoom |

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.13+**
- **Windows 10/11** (primary platform; other OS may work without DPAPI)

### Install Dependencies

```bash
pip install PyQt6 PyQt6-WebEngine pywin32
```

> 💡 `pywin32` is optional but recommended on Windows — it enables DPAPI password encryption and dark title bar support.

### Run from Source

```bash
python GBrowser.py
```

### Build Standalone Executable

```bash
build.bat
```

This will:
1. Install dependencies
2. Build with PyInstaller (`--onedir --windowed`)
3. Package with Inno Setup into `releases/5.4/GBrowser-5.4-Setup.exe`

> ⚙️ Requires [PyInstaller](https://pyinstaller.org/) and [Inno Setup 6](https://jrsoftware.org/isinfo.php) to be installed.

---

## 📁 Project Structure

```
GBrowser/
├── GBrowser.py        # Entire browser — single-file architecture
├── GBrowser.ico       # Application icon
├── GBrowser.spec      # PyInstaller build spec
├── GBrowser.iss       # Inno Setup installer script
├── build.bat          # One-click build script
├── blocklist.txt      # External ad/tracker domain blocklist (300+ domains)
└── README.md
```

### User Data

All user data is stored in `~/.gorstak_browser/`:

```
~/.gorstak_browser/
├── config.json        # Window geometry and state
├── settings.txt       # Homepage and search engine
├── bookmarks.txt      # Bookmarks (with folder support)
├── history.txt        # Browsing history (last 100 URLs)
├── passwords.dat      # Encrypted credentials (DPAPI or Fernet)
├── storage/           # WebEngine persistent storage
└── cache/             # WebEngine cache
```

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.13 |
| UI Framework | PyQt6 |
| Browser Engine | Chromium (via QtWebEngine) |
| Encryption | Windows DPAPI / Fernet (AES) |
| Build Tool | PyInstaller |
| Installer | Inno Setup 6 |

---

## ⚠️ Legal Disclaimer

```
IMPORTANT — PLEASE READ CAREFULLY BEFORE USING THIS SOFTWARE

THIS SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.

IN NO EVENT SHALL THE AUTHORS, COPYRIGHT HOLDERS, OR CONTRIBUTORS BE LIABLE
FOR ANY CLAIM, DAMAGES, OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
THE USE OR OTHER DEALINGS IN THE SOFTWARE.

AD BLOCKING DISCLAIMER:
This software includes built-in ad and tracker blocking functionality. The use
of ad blocking may violate the terms of service of certain websites. Users are
solely responsible for ensuring their use of this software complies with
applicable laws and the terms of service of websites they visit. The developers
assume no liability for any consequences arising from the use of the ad
blocking features.

CREDENTIAL STORAGE DISCLAIMER:
This software stores user credentials locally using platform-specific
encryption (Windows DPAPI or Fernet AES). While reasonable measures are taken
to protect stored data, no encryption method is infallible. Users store
credentials at their own risk. The developers are not responsible for any
unauthorized access to stored credentials resulting from system compromise,
malware, or other security breaches.

THIRD-PARTY CONTENT:
This software uses the Chromium browser engine via QtWebEngine. Chromium is an
open-source project by Google and The Chromium Authors, governed by its own
license terms. The developers of GBrowser are not affiliated with Google,
The Chromium Authors, or The Qt Company.

PRIVACY:
GBrowser does not collect, transmit, or share any user data. All browsing
data, credentials, bookmarks, and history are stored locally on the user's
machine and are never sent to external servers by the application itself.
Websites visited may independently collect data according to their own
privacy policies.

Copyright (c) 2025 Gorstak. All rights reserved.
```

---

<p align="center">
  Made with ☕ and 🐍 by <strong>Gorstak</strong>
</p>
=======
<p align="center">
  <img src="GBrowser.ico" alt="GBrowser Logo" width="96" height="96">
</p>

<h1 align="center">🌐 GBrowser</h1>

<p align="center">
  <strong>A full-featured, privacy-first web browser built with Python</strong><br>
  <em>Ported from the original Ceprkac C# browser — now cross-platform with PyQt6</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-5.4-blue?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/python-3.13+-green?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/engine-Chromium%20(QtWebEngine)-orange?style=flat-square" alt="Engine">
  <img src="https://img.shields.io/badge/license-proprietary-red?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/platform-Windows-0078D6?style=flat-square&logo=windows&logoColor=white" alt="Platform">
</p>

---

## 📖 About

GBrowser is a lightweight desktop web browser with a strong focus on **ad blocking** and **privacy**. It ships with a built-in ad blocker covering 300+ tracking and advertising domains, a password manager with encrypted storage, and a Chrome-style dark UI — all in a single Python file.

Originally written in C# as **Ceprkac**, the browser has been fully ported to Python 3.13 using PyQt6 and PyQt6-WebEngine, keeping feature parity with the original while gaining the flexibility of the Python ecosystem.

---

## ✨ Features

### 🛡️ Privacy & Ad Blocking
- **Built-in ad blocker** — blocks 300+ ad/tracking domains at the network level via request interception
- **DOM-level ad removal** — injects CSS and JavaScript to hide ad elements on pages
- **YouTube-specific ad blocking** — dedicated blocker that skips video ads, removes overlay ads, and strips ad data from YouTube API responses
- **Main-world script injection** — intercepts `JSON.parse`, `fetch`, and `XMLHttpRequest` to block ads before they render
- **Custom blocklist support** — load additional domains from `blocklist.txt`
- **Whitelist system** — banking, auth, AI services, gaming platforms, and other essential sites are never blocked

### 🔐 Password Manager
- **Encrypted credential storage** — uses Windows DPAPI on Windows, Fernet (AES-128) fallback on other platforms
- **Auto-fill** — detects login forms and fills saved credentials automatically
- **Multi-account picker** — choose between multiple saved accounts for the same site
- **CSV import** — import passwords from Chrome/Edge export format
- **Input sanitization** — length limits and control character filtering on import

### 🗂️ Tabs
- **Chrome-style custom tab strip** — owner-drawn tabs with hover effects, loading progress bars, and close buttons
- **Drag-to-reorder** tabs
- **Middle-click to close** tabs
- **Tab restore** — reopen recently closed tabs with `Ctrl+Shift+T`
- **Tab cycling** — `Ctrl+Tab` / `Ctrl+Shift+Tab` to switch between tabs
- **Per-tab zoom** — each tab remembers its own zoom level

### 🔖 Bookmarks
- **Bookmark bar** with overflow menu (`»`) for large collections
- **Folder support** — organize bookmarks into nested folders
- **HTML import/export** — compatible with Netscape bookmark format (Chrome, Firefox, Edge)
- **One-click toggle** — `Ctrl+D` to add or remove a bookmark
- **Incremental UI updates** — bookmark bar only redraws when data changes

### 🔍 Navigation & Search
- **Smart address bar** — auto-detects URLs vs search queries
- **6 search engines** — Google, Bing, DuckDuckGo, Yahoo, Brave Search, Startpage
- **Autocomplete** — suggestions from history and bookmarks as you type
- **Find in page** — `Ctrl+F` with live search, next/prev navigation
- **Zoom controls** — `Ctrl+Plus` / `Ctrl+Minus` / `Ctrl+0`

### 🔑 OAuth & Authentication
- **OAuth popup handling** — Google, Apple, Microsoft, Twitter/X, and other OAuth flows open correctly in new tabs
- **Auth callback auto-close** — OAuth callback tabs close automatically after authentication completes
- **Auth domain whitelist** — login flows are never blocked by the ad blocker

### 📥 Downloads
- **Download manager** — dialog showing recent downloads with progress tracking
- **Save-as dialog** — choose where to save each download
- **Status bar progress** — live download progress in the status bar

### 🎨 Interface
- **Dark theme** — Chrome-dark inspired color palette throughout
- **Dark title bar** — native Windows dark title bar integration via DWM API
- **DevTools** — built-in Chromium DevTools accessible via `Ctrl+I`
- **Window state persistence** — remembers position, size, and maximized state
- **Status bar** — shows ad block count, loading status, zoom level, and download progress

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+T` | New tab |
| `Ctrl+W` | Close current tab |
| `Ctrl+Shift+T` | Restore closed tab |
| `Ctrl+Tab` | Next tab |
| `Ctrl+Shift+Tab` | Previous tab |
| `Ctrl+L` | Focus address bar |
| `Ctrl+D` | Toggle bookmark |
| `Ctrl+F` | Find in page |
| `Ctrl+I` | Open DevTools |
| `Ctrl+Plus` | Zoom in |
| `Ctrl+Minus` | Zoom out |
| `Ctrl+0` | Reset zoom |

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.13+**
- **Windows 10/11** (primary platform; other OS may work without DPAPI)

### Install Dependencies

```bash
pip install PyQt6 PyQt6-WebEngine pywin32
```

> 💡 `pywin32` is optional but recommended on Windows — it enables DPAPI password encryption and dark title bar support.

### Run from Source

```bash
python GBrowser.py
```

### Build Standalone Executable

```bash
build.bat
```

This will:
1. Install dependencies
2. Build with PyInstaller (`--onedir --windowed`)
3. Package with Inno Setup into `releases/5.4/GBrowser-5.4-Setup.exe`

> ⚙️ Requires [PyInstaller](https://pyinstaller.org/) and [Inno Setup 6](https://jrsoftware.org/isinfo.php) to be installed.

---

## 📁 Project Structure

```
GBrowser/
├── GBrowser.py        # Entire browser — single-file architecture
├── GBrowser.ico       # Application icon
├── GBrowser.spec      # PyInstaller build spec
├── GBrowser.iss       # Inno Setup installer script
├── build.bat          # One-click build script
├── blocklist.txt      # External ad/tracker domain blocklist (300+ domains)
└── README.md
```

### User Data

All user data is stored in `~/.gorstak_browser/`:

```
~/.gorstak_browser/
├── config.json        # Window geometry and state
├── settings.txt       # Homepage and search engine
├── bookmarks.txt      # Bookmarks (with folder support)
├── history.txt        # Browsing history (last 100 URLs)
├── passwords.dat      # Encrypted credentials (DPAPI or Fernet)
├── storage/           # WebEngine persistent storage
└── cache/             # WebEngine cache
```

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.13 |
| UI Framework | PyQt6 |
| Browser Engine | Chromium (via QtWebEngine) |
| Encryption | Windows DPAPI / Fernet (AES) |
| Build Tool | PyInstaller |
| Installer | Inno Setup 6 |

---

## ⚠️ Legal Disclaimer

```
IMPORTANT — PLEASE READ CAREFULLY BEFORE USING THIS SOFTWARE

THIS SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.

IN NO EVENT SHALL THE AUTHORS, COPYRIGHT HOLDERS, OR CONTRIBUTORS BE LIABLE
FOR ANY CLAIM, DAMAGES, OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
THE USE OR OTHER DEALINGS IN THE SOFTWARE.

AD BLOCKING DISCLAIMER:
This software includes built-in ad and tracker blocking functionality. The use
of ad blocking may violate the terms of service of certain websites. Users are
solely responsible for ensuring their use of this software complies with
applicable laws and the terms of service of websites they visit. The developers
assume no liability for any consequences arising from the use of the ad
blocking features.

CREDENTIAL STORAGE DISCLAIMER:
This software stores user credentials locally using platform-specific
encryption (Windows DPAPI or Fernet AES). While reasonable measures are taken
to protect stored data, no encryption method is infallible. Users store
credentials at their own risk. The developers are not responsible for any
unauthorized access to stored credentials resulting from system compromise,
malware, or other security breaches.

THIRD-PARTY CONTENT:
This software uses the Chromium browser engine via QtWebEngine. Chromium is an
open-source project by Google and The Chromium Authors, governed by its own
license terms. The developers of GBrowser are not affiliated with Google,
The Chromium Authors, or The Qt Company.

PRIVACY:
GBrowser does not collect, transmit, or share any user data. All browsing
data, credentials, bookmarks, and history are stored locally on the user's
machine and are never sent to external servers by the application itself.
Websites visited may independently collect data according to their own
privacy policies.

Copyright (c) 2025 Gorstak. All rights reserved.
```

---

<p align="center">
  Made with ☕ and 🐍 by <strong>Gorstak</strong>
</p>
>>>>>>> e56f08a31ecaeba7b69dbcaf56d5d61d93745691
