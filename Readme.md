# ⚡ FitGirl Link Extractor

An automated, high-speed link generator that extracts direct `fuckingfast.co` download URLs from FitGirl Repacks, seamlessly handling Cloudflare Turnstile bot protection in the background.

---

## 📋 Requirements

Before using the tool, ensure you have:

1. **Python 3.10+** installed on your system.
   - ⚠️ **Important during Python installation**: Make sure to check the box **`"Add python.exe to PATH"`**.
2. **A Chromium-based browser** installed (e.g. **Google Chrome**, **Microsoft Edge**, or **Brave**).
   - Chrome or Edge are already pre-installed on most Windows PCs.

---

## 📦 Quick Installation

### Option 1: Automated Installer (Recommended)
Simply double-click:
- **`setup.bat`** (or **`install.bat`**)

The installer will automatically:
1. Verify your Python installation.
2. Upgrade and install all dependencies from `requirements.txt`.
3. Confirm setup readiness and offer to launch the app immediately.

### Option 2: Manual Installation (Command Line)
If you prefer running commands manually in your terminal / PowerShell:
```bash
pip install -r requirements.txt
```

---

## 🚀 Ways to Run the App

### Option A: Standalone Executable (Zero Setup - Runs on Any Windows PC)
If you want to share this tool with friends or use it without installing Python:
1. Double-click **`FitGirl_Link_Extractor.exe`** directly.
2. No Python, terminal, or setup script is needed!

---

### Option B: Automated Script Launcher (With Python)
If running from source:
1. Double-click **`setup.bat`** once to install dependencies.
2. Double-click **`run.bat`** (or run `python app.py` in your terminal).

---

### 🔨 Rebuilding the Standalone Executable
To build a fresh `.exe` from source:
- Double-click **`build.bat`**.
- The script will compile everything and output `FitGirl_Link_Extractor.exe`.

---

## 🕹️ How to Use

### 1. Extracting Links
1. **Paste your links** into the input box on the left:
   - You can copy the entire fuckingfast list from the FitGirl repack page (even lines with `- https://...`).
   - Or click **`📂 Load File`** to load your `input.txt`.
2. Click **`▶ Start Fetching Links`**.
3. **Live Progress**:
   - The app will automatically open your Chromium engine (Chrome, Edge, or Brave), bypass any Cloudflare Turnstile challenges, and extract the real download links.
   - The **Live Activity Console** will show real-time progress for each part.
4. **Get Your Links**:
   - Extracted direct download URLs (`https://dl.fuckingfast.co/dl/...`) will appear in the right panel.
   - Click **`📑 Copy All Links`** to paste them straight into your download manager (**JDownloader 2**, **Internet Download Manager (IDM)**, or browser).
   - All links are also automatically saved to **`download_links.txt`**.

---

## 💻 CLI Mode (Alternative)

If you prefer running without a GUI:
1. Paste your raw links into `input.txt`.
2. Run:
   ```bash
   python download.py
   ```
3. Direct download links will be appended to `download_links.txt`.

---

## 🛠️ Troubleshooting & FAQ

### 1. "Turnstile challenge was not resolved in time" / CAPTCHA Popups
- **Cause**: Cloudflare occasionally triggers an interactive "Verify you are human" check if your IP address recently changed or high-security mode is active.
- **Fix**: When the automated browser window appears with a checkbox, **simply click the tick box once**. The extractor will immediately detect the solved token and continue automatically.

### 2. "Could not locate Google Chrome or Edge on this system"
- **Cause**: No Chromium-based browser is installed.
- **Fix**: Ensure Google Chrome, Microsoft Edge, or Brave is installed. The tool automatically searches Windows Registry, System PATH, Program Files, and AppData directories.

### 3. "HTTP 403 Forbidden" Error
- **Cause**: Occurs when trying to scrape `fuckingfast.co` with basic HTTP tools (like `curl` or `requests`) without browser fingerprinting.
- **Fix**: Always run extraction through `FitGirl_Link_Extractor.exe`, `run.bat`, `app.py`, or `download.py`, which utilizes authentic Chromium DevTools Protocol (CDP) to pass Cloudflare checks.

---

## 📂 Project Structure

```
Fitgirl_Local/
│
├── FitGirl_Link_Extractor.exe # Standalone executable (runs on any Windows PC without Python)
├── app.py                     # Modern GUI application (CustomTkinter + DrissionPage engine)
├── download.py                # Standalone CLI extraction script
├── build.bat                  # One-click PyInstaller standalone builder
├── setup.bat                  # Automated environment validator & package installer
├── install.bat                # Alias for setup.bat
├── run.bat                    # One-click app launcher
├── requirements.txt           # Python dependencies (including pyinstaller)
├── input.txt                  # Working input file for links
├── download_links.txt         # Output file containing direct download URLs
└── README.md                  # User guide and documentation
```

