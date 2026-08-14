import os, re, time
# pyrefly: ignore [missing-import]
from bs4 import BeautifulSoup
from datetime import datetime
from colorama import Fore, Style
from DrissionPage import ChromiumPage, ChromiumOptions


class console:
    def __init__(self) -> None:
        self.colors = {"green": Fore.GREEN, "red": Fore.RED, "yellow": Fore.YELLOW, "blue": Fore.BLUE,
                       "magenta": Fore.MAGENTA, "cyan": Fore.CYAN, "white": Fore.WHITE, "black": Fore.BLACK,
                       "reset": Style.RESET_ALL, "lightblack": Fore.LIGHTBLACK_EX, "lightred": Fore.LIGHTRED_EX,
                       "lightgreen": Fore.LIGHTGREEN_EX, "lightyellow": Fore.LIGHTYELLOW_EX,
                       "lightblue": Fore.LIGHTBLUE_EX, "lightmagenta": Fore.LIGHTMAGENTA_EX,
                       "lightcyan": Fore.LIGHTCYAN_EX, "lightwhite": Fore.LIGHTWHITE_EX}

    def clear(self):
        os.system("cls" if os.name == "nt" else "clear")

    def timestamp(self):
        return datetime.now().strftime("%H:%M:%S")

    def info(self, msg, obj):
        print(f"{self.colors['lightblack']}{self.timestamp()} » {self.colors['lightblue']}INFO {self.colors['lightblack']}• {self.colors['white']}{msg} : {self.colors['lightblue']}{obj}{self.colors['white']} {self.colors['reset']}")

    def success(self, msg, obj):
        print(f"{self.colors['lightblack']}{self.timestamp()} » {self.colors['lightgreen']}SUCC {self.colors['lightblack']}• {self.colors['white']}{msg} : {self.colors['lightgreen']}{obj}{self.colors['white']} {self.colors['reset']}")

    def error(self, msg, obj):
        print(f"{self.colors['lightblack']}{self.timestamp()} » {self.colors['lightred']}ERRR {self.colors['lightblack']}• {self.colors['white']}{msg} : {self.colors['lightred']}{obj}{self.colors['white']} {self.colors['reset']}")

    def warning(self, msg, obj):
        print(f"{self.colors['lightblack']}{self.timestamp()} » {self.colors['lightyellow']}WARN {self.colors['lightblack']}• {self.colors['white']}{msg} : {self.colors['lightyellow']}{obj}{self.colors['white']} {self.colors['reset']}")


log = console()
log.clear()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1'
}

# remove processed link
def remove_link(processed_link, input_file='input.txt'):
    try:
        with open(input_file, 'r', encoding="utf-8") as f:
            lines = f.readlines()
        with open(input_file, 'w', encoding="utf-8") as f:
            for line in lines:
                clean_line = line.strip()
                if clean_line.startswith("- "):
                    clean_line = clean_line[2:].strip()
                if clean_line != processed_link:
                    f.write(line)
    except Exception as e:
        log.warning("Could not remove link from input.txt", str(e))


# -------- MAIN --------
try:
    with open('input.txt', 'r', encoding="utf-8") as f:
        lines = f.readlines()
except FileNotFoundError:
    log.error("File not found", "input.txt")
    lines = []

links = []
for line in lines:
    line = line.strip()
    if line.startswith("- "):
        line = line[2:].strip()
    if line.startswith("http://") or line.startswith("https://"):
        links.append(line)


output_file = "download_links.txt"

scraper_options = ChromiumOptions()
scraper_options.set_browser_path(r'C:\Program Files\Google\Chrome\Application\chrome.exe')
page = ChromiumPage(scraper_options)

for link in links:
    log.info("Processing", link)

    try:
        page.get(link)
    except Exception as e:
        log.error("Request failed", str(e))
        continue

    # Wait for the download button to appear (meaning we passed the initial CF intercept)
    btn = page.ele('text:DOWNLOAD', timeout=15)
    if not btn:
        log.error("Download button not found", link)
        continue

    # Wait for turnstile to solve (button becomes active/opaque)
    active = False
    for _ in range(30):
        try:
            style = btn.attr('style')
            if not style or ('opacity' not in style and '0.5' not in style):
                active = True
                break
        except Exception:
            pass
        time.sleep(0.5)

    download_url = None
    if active:
        file_id = link.split('/')[-1].split('#')[0]
        js = f'''
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/f/{file_id}/go', false);
            xhr.setRequestHeader('HX-Request', 'true');
            xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
            xhr.send('cf-turnstile-response=' + encodeURIComponent(window.turnstileToken || ''));
            return xhr.getResponseHeader('hx-redirect');
        '''
        try:
            download_url = page.run_js(js)
        except Exception as e:
            log.warning("XHR extraction failed", str(e))
    else:
        log.warning("Turnstile not solved in time", link)

    if not download_url:
        log.error("Download URL not found", link)
        continue

    log.success("Found download URL", download_url)

    # write to file
    with open(output_file, "a", encoding="utf-8") as f:
        f.write(download_url + "\n")

    # remove processed link (disabled so input.txt remains untouched)
    # remove_link(link)

log.success("All links saved to", output_file)
page.quit()
