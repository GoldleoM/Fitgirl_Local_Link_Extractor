import os
import sys
import time
import queue
import threading
from datetime import datetime
from colorama import Fore, Style
from DrissionPage import ChromiumPage, ChromiumOptions

# Add parent directory to sys.path so it can find app.py helpers
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import find_browser_path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


class console:
    def __init__(self) -> None:
        self.colors = {
            "green": Fore.GREEN, "red": Fore.RED, "yellow": Fore.YELLOW, "blue": Fore.BLUE,
            "magenta": Fore.MAGENTA, "cyan": Fore.CYAN, "white": Fore.WHITE, "black": Fore.BLACK,
            "reset": Style.RESET_ALL, "lightblack": Fore.LIGHTBLACK_EX, "lightred": Fore.LIGHTRED_EX,
            "lightgreen": Fore.LIGHTGREEN_EX, "lightyellow": Fore.LIGHTYELLOW_EX,
            "lightblue": Fore.LIGHTBLUE_EX, "lightmagenta": Fore.LIGHTMAGENTA_EX,
            "lightcyan": Fore.LIGHTCYAN_EX, "lightwhite": Fore.LIGHTWHITE_EX
        }
        self.lock = threading.Lock()

    def clear(self):
        os.system("cls" if os.name == "nt" else "clear")

    def timestamp(self):
        return datetime.now().strftime("%H:%M:%S.%f")[:-3]

    def info(self, msg, obj=""):
        with self.lock:
            print(f"{self.colors['lightblack']}{self.timestamp()} » {self.colors['lightblue']}INFO {self.colors['lightblack']}• {self.colors['white']}{msg} {self.colors['lightblue']}{obj}{self.colors['reset']}")

    def success(self, msg, obj=""):
        with self.lock:
            print(f"{self.colors['lightblack']}{self.timestamp()} » {self.colors['lightgreen']}SUCC {self.colors['lightblack']}• {self.colors['white']}{msg} {self.colors['lightgreen']}{obj}{self.colors['reset']}")

    def error(self, msg, obj=""):
        with self.lock:
            print(f"{self.colors['lightblack']}{self.timestamp()} » {self.colors['lightred']}ERRR {self.colors['lightblack']}• {self.colors['white']}{msg} {self.colors['lightred']}{obj}{self.colors['reset']}")

    def warning(self, msg, obj=""):
        with self.lock:
            print(f"{self.colors['lightblack']}{self.timestamp()} » {self.colors['lightyellow']}WARN {self.colors['lightblack']}• {self.colors['white']}{msg} {self.colors['lightyellow']}{obj}{self.colors['reset']}")


log = console()
log.clear()

# ================= SMART PACING CONFIG =================
STEALTH_MODE = True        # Set to False to see the Chrome window on screen (for debugging)
MAX_CONCURRENCY = 8        # Safe parallel tabs (6-8 is ideal for 100+ links on single IP)
INTER_REQUEST_DELAY = 0.20 # 200ms delay between link requests (prevents rate limits)
PAGE_LOAD_TIMEOUT = 16     # Max seconds to wait for page to reach download button
TURNSTILE_TIMEOUT = 20     # Max seconds for Turnstile bot-check to clear
MICRO_POLL_INTERVAL = 0.02 # 20ms high-frequency check
MAX_RETRIES = 3            # Auto-retry attempts on temporary Cloudflare challenges
# =======================================================

# Resolve input and output paths
script_dir = os.path.dirname(os.path.abspath(__file__))
if os.path.exists(os.path.join(script_dir, "input.txt")):
    input_path = os.path.join(script_dir, "input.txt")
    output_path = os.path.join(script_dir, "download_links.txt")
elif os.path.exists("input.txt"):
    input_path = "input.txt"
    output_path = "download_links.txt"
else:
    input_path = os.path.join(script_dir, "..", "input.txt")
    output_path = os.path.join(script_dir, "..", "download_links.txt")

try:
    with open(input_path, 'r', encoding="utf-8") as f:
        raw_lines = f.readlines()
except FileNotFoundError:
    log.error("Input file not found", input_path)
    raw_lines = []

links = []
for line in raw_lines:
    line = line.strip()
    if line.startswith("- "):
        line = line[2:].strip()
    if line.startswith("http://") or line.startswith("https://"):
        links.append(line)

total_links = len(links)
log.info(f"Loaded {total_links} links from {input_path}")

if not links:
    log.error("No valid URLs found. Exiting.")
    sys.exit(0)

# Clear existing output file
with open(output_path, "w", encoding="utf-8") as f:
    pass

pool_size = min(MAX_CONCURRENCY, total_links)
mode_str = "Invisible Stealth (Off-Screen)" if STEALTH_MODE else "Visible Debugging Window"
log.info(f"🚀 Launching {pool_size} paced parallel workers | Mode: {mode_str}...")

# High-Performance Chromium Options
browser_path = find_browser_path()
scraper_options = ChromiumOptions()
if browser_path:
    scraper_options.set_browser_path(browser_path)

if STEALTH_MODE:
    # Run completely invisible off-screen
    scraper_options.set_argument('--window-position=-32000,-32000')
    scraper_options.set_argument('--window-size=1280,800')
else:
    # Centered and large on screen for easy debugging
    scraper_options.set_argument('--window-position=50,50')
    scraper_options.set_argument('--window-size=1440,900')
    scraper_options.set_argument('--start-maximized')

scraper_options.set_argument('--blink-settings=imagesEnabled=false')
scraper_options.set_argument('--disable-gpu')
scraper_options.set_argument('--disable-extensions')
scraper_options.set_argument('--disable-notifications')
scraper_options.set_argument('--mute-audio')
scraper_options.set_load_mode('eager')

page = ChromiumPage(scraper_options)

# Warm up Cloudflare clearance cookie on the first tab
log.info("🔥 Warming up Cloudflare session clearance...")
try:
    page.latest_tab.get(links[0], retry=1, timeout=PAGE_LOAD_TIMEOUT)
    warm_btn = page.latest_tab.ele('text:DOWNLOAD', timeout=8)
    if warm_btn:
        for _ in range(100):
            style = warm_btn.attr('style')
            if not style or ('opacity' not in style and '0.5' not in style):
                break
            time.sleep(0.05)
    log.success("Session warmed up! Launching parallel pipeline...")
except Exception as e:
    log.warning("Warmup step noticed:", str(e))

# Create worker tabs up to pool size
worker_tabs = [page.latest_tab]
while len(worker_tabs) < pool_size:
    worker_tabs.append(page.new_tab())

links_queue = queue.Queue()
for item in enumerate(links, start=1):
    links_queue.put((*item, 0))  # (index, url, retry_count)

extracted_results = []
file_lock = threading.Lock()
rate_limit_lock = threading.Lock()
start_time_all = time.time()


def worker_thread(worker_id: int, tab):
    """Worker thread with adaptive pacing and automatic rate-limit backoff."""
    while True:
        try:
            idx, link, retries = links_queue.get_nowait()
        except queue.Empty:
            break

        file_id = link.split('/')[-1].split('#')[0]
        retry_msg = f" (Retry {retries}/{MAX_RETRIES})" if retries > 0 else ""
        log.info(f"[{idx:03d}/{total_links:03d}] [T#{worker_id:02d}] Navigating ->", f"{link}{retry_msg}")
        start_t = time.time()

        try:
            # Controlled pacing to prevent WAF burst flags
            time.sleep(INTER_REQUEST_DELAY)

            tab.get(link, retry=1, timeout=PAGE_LOAD_TIMEOUT)

            # Locate DOWNLOAD button
            btn = tab.ele('text:DOWNLOAD', timeout=PAGE_LOAD_TIMEOUT)
            if not btn:
                if retries < MAX_RETRIES:
                    backoff = 1.5 * (retries + 1)
                    log.warning(f"[{idx:03d}/{total_links:03d}] [T#{worker_id:02d}] Button missing, backing off {backoff:.1f}s and retrying...", link)
                    time.sleep(backoff)
                    links_queue.put((idx, link, retries + 1))
                else:
                    log.error(f"[{idx:03d}/{total_links:03d}] [T#{worker_id:02d}] Download button not found:", link)
                continue

            # Micro-polling for Turnstile completion
            active = False
            for _ in range(int(TURNSTILE_TIMEOUT / MICRO_POLL_INTERVAL)):
                try:
                    style = btn.attr('style')
                    if not style or ('opacity' not in style and '0.5' not in style):
                        active = True
                        break
                except Exception:
                    pass
                time.sleep(MICRO_POLL_INTERVAL)

            if not active:
                if retries < MAX_RETRIES:
                    backoff = 2.0 * (retries + 1)
                    log.warning(f"[{idx:03d}/{total_links:03d}] [T#{worker_id:02d}] Turnstile slow, re-queuing with {backoff:.1f}s pause...", link)
                    time.sleep(backoff)
                    links_queue.put((idx, link, retries + 1))
                else:
                    log.warning(f"[{idx:03d}/{total_links:03d}] [T#{worker_id:02d}] Turnstile failed permanently for", link)
                continue

            # Instant direct XHR header extraction
            js_extract = f'''
                var xhr = new XMLHttpRequest();
                xhr.open('POST', '/f/{file_id}/go', false);
                xhr.setRequestHeader('HX-Request', 'true');
                xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
                xhr.send('cf-turnstile-response=' + encodeURIComponent(window.turnstileToken || ''));
                return xhr.getResponseHeader('hx-redirect');
            '''

            dl_url = tab.run_js(js_extract)
            elapsed_ms = (time.time() - start_t) * 1000

            if dl_url:
                with file_lock:
                    extracted_results.append((idx, dl_url))
                    with open(output_path, "a", encoding="utf-8") as f:
                        f.write(dl_url + "\n")
                log.success(f"[{idx:03d}/{total_links:03d}] [T#{worker_id:02d}] Extracted in {elapsed_ms:.0f}ms ->", dl_url)
            else:
                if retries < MAX_RETRIES:
                    log.warning(f"[{idx:03d}/{total_links:03d}] Empty XHR response, retrying...", link)
                    time.sleep(1.5)
                    links_queue.put((idx, link, retries + 1))
                else:
                    log.warning(f"[{idx:03d}/{total_links:03d}] [T#{worker_id:02d}] Empty URL permanently for", link)

        except Exception as e:
            if retries < MAX_RETRIES:
                time.sleep(1.5)
                links_queue.put((idx, link, retries + 1))
            else:
                log.error(f"[{idx:03d}/{total_links:03d}] [T#{worker_id:02d}] Error:", str(e))
        finally:
            links_queue.task_done()


# Start all worker threads with smooth stagger
threads = []
for w_id, w_tab in enumerate(worker_tabs, start=1):
    t = threading.Thread(target=worker_thread, args=(w_id, w_tab), daemon=True)
    threads.append(t)
    t.start()
    time.sleep(0.15)  # 150ms smooth start stagger

# Wait for all links to be extracted with graceful Ctrl+C handling
try:
    while not links_queue.empty() or any(t.is_alive() for t in threads):
        time.sleep(0.2)
except KeyboardInterrupt:
    log.warning("\n[INTERRUPTED] Stopping workers gracefully...")

# Ensure final output file is sorted in exact numerical order (Part 01 -> Part 120+)
extracted_results.sort(key=lambda x: x[0])
with open(output_path, "w", encoding="utf-8") as f:
    for _, url in extracted_results:
        f.write(url + "\n")

total_elapsed = time.time() - start_time_all
avg_ms = (total_elapsed / total_links) * 1000 if total_links else 0

log.success("=" * 65)
log.success(f"⚡ FLASH COMPLETE! {len(extracted_results)}/{total_links} links extracted in {total_elapsed:.3f}s ({avg_ms:.0f}ms avg/link).")
log.success(f"📁 Output file (sorted in order): {output_path}")

try:
    page.quit()
except Exception:
    pass
