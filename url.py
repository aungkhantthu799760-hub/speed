import requests
import urllib3
import socket
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
console = Console()

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

def find_portal_info():
    # 🌟 Header Banner
    console.print(Panel.fit(
        "[bold cyan]★ KSTAR3 ★[/bold cyan]\n[bold yellow]Portal URL & Device Finder[/bold yellow]\n[dim]Owens @ar0thua | KAVIN FAST SPEED[/dim]",
        border_style="green"
    ))
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36'
    })
    
    detected_url = None
    device_type = "Ruijie / Generic Gateway"
    
    # 1. Test via connectivity check
    TEST_URL = "http://connectivitycheck.gstatic.com/generate_204"
    with console.status("[bold green]🔍 Scanning network for Portal URL...", spinner="dots"):
        try:
            r = session.get(TEST_URL, allow_redirects=True, timeout=5)
            if r.history or "login" in r.url or "ruijie" in r.url or r.status_code == 200:
                if r.url != TEST_URL:
                    detected_url = r.url
        except:
            pass

        # 2. Test common gateway IPs if not found
        if not detected_url:
            gateways = [get_gateway_ip(), "192.168.110.1", "192.168.0.1", "10.44.77.254", "192.168.1.1"]
            for gw in list(dict.fromkeys(gateways)):
                try:
                    target = f"http://{gw}"
                    res = session.get(target, timeout=3, allow_redirects=True)
                    if res.history or res.status_code in [200, 302]:
                        detected_url = res.url
                        break
                except:
                    continue

    # 📊 Result Table Display
    table = Table(title="[bold magenta]Network Scan Results[/bold magenta]", border_style="blue")
    table.add_column("Category", style="cyan", no_wrap=True)
    table.add_column("Details", style="green")

    if detected_url:
        # Router အမျိုးအစား စစ်ဆေးခြင်း
        if "ruijie" in detected_url.lower() or "eportal" in detected_url.lower():
            device_type = "Ruijie Networks Gateway"
        elif "mikrotik" in detected_url.lower():
            device_type = "MikroTik Router"
        else:
            device_type = "Captive Portal / Wi-Fi Router"

        table.add_row("Status", "[bold green]Success ✅[/bold green]")
        table.add_row("Device Type", f"[bold yellow]{device_type}[/bold yellow]")
        table.add_row("Portal URL", f"[underline blue]{detected_url}[/underline blue]")
        
        console.print(table)
        rprint(Panel(f"[bold green][+] URL တွေ့ရှိပါပြီ။[/bold green]\n`{detected_url}`", border_style="green"))
    else:
        table.add_row("Status", "[bold red]Failed ❌[/bold red]")
        table.add_row("Reason", "Unable to resolve or reach portal.")
        console.print(table)
        rprint(Panel("[bold red][-] URL မတွေ့ပါ။ Wi-Fi သို့ အရင်ချိတ်ဆက်ထားကြောင်း သေချာစေပါ။[/bold red]", border_style="red"))

if __name__ == "__main__":
    find_portal_info()
