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

## 🚀 How to Use

### 1. Launching the GUI App
Double-click **`run.bat`** (or run `python app.py` in your terminal).

### 2. Extracting Links
1. **Paste your links** into the input box on the left:
   - You can copy the entire fuckingfast list from the FitGirl repack page (even lines with `- https://...`).
   - Or click **`📂 Load File`** to load your `input.txt`.
2. Click **`▶ Start Fetching Links`**.
3. **Live Progress**:
   - The app will automatically open your Chrome engine, bypass any Cloudflare Turnstile challenges, and extract the real download links.
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

### 1. "Python is NOT installed or NOT found in your system PATH"
- **Cause**: Python is missing or was installed without the PATH environment variable.
- **Fix**: Download Python from [python.org/downloads](https://www.python.org/downloads/). Run the installer, click **Modify** or **Install**, and make sure **`Add python.exe to PATH`** is checked.

### 2. "Turnstile challenge was not resolved in time" / CAPTCHA Popups
- **Cause**: Cloudflare occasionally triggers an interactive "Verify you are human" check if your IP address recently changed or high-security mode is active.
- **Fix**: When the automated Chrome window appears with a checkbox, **simply click the tick box once**. The extractor will immediately detect the solved token and continue automatically.

### 3. "Could not locate Google Chrome or Edge on this system"
- **Cause**: The browser is installed in a non-standard location.
- **Fix**: Ensure Google Chrome or Microsoft Edge is installed in `C:\Program Files` or `C:\Program Files (x86)`.

### 4. "HTTP 403 Forbidden" Error
- **Cause**: Occurs when trying to scrape `fuckingfast.co` with basic HTTP tools (like `curl` or `requests`) without browser fingerprinting.
- **Fix**: Always run extraction through `run.bat` / `app.py` / `download.py`, which utilizes authentic Chromium DevTools Protocol (CDP) to pass Cloudflare checks.

### 5. Why are my files not downloading in the browser?
- The tool is designed to **extract direct links only**, preventing unwanted ad tabs, popups, and random browser downloads. You can feed the final links directly into a download manager like JDownloader 2 for full-speed parallel downloading.

---

## 📂 Project Structure

```
Fitgirl_Local/
│
├── app.py              # Modern GUI application (CustomTkinter + DrissionPage engine)
├── download.py         # Standalone CLI extraction script
├── setup.bat           # Automated environment validator & package installer
├── install.bat         # Alias for setup.bat
├── run.bat             # One-click app launcher
├── requirements.txt    # Python dependencies
├── input.txt           # Working input file for links
├── download_links.txt  # Output file containing direct download URLs
└── README.md           # User guide and documentation
```
