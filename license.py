import time
from datetime import datetime
import hashlib
import sys

def verify_license():
    """Key ထဲတွင် ပါရှိသော အချိန် (Timestamp) အပေါ်မူတည်၍ သက်တမ်းကုန်ဆုံးခြင်း ရှိမရှိ စစ်ဆေးခြင်း"""
    print("=" * 50)
    print("       KHANTv8.3 - LICENSE TIME VERIFICATION       ")
    print("=" * 50)
    
    entered_key = input("\n👉 License Key ထည့်ပါ: ").strip()
    
    if not entered_key.startswith("KHANT-"):
        print("[-] ❌ ပုံစံမမှန်ကန်သော License Key ဖြစ်ပါသည်။")
        sys.exit(1)
        
    parts = entered_key.split("-")
    if len(parts) < 3:
        print("[-] ❌ အချက်အလက်မပြည့်စုံသော Key ဖြစ်ပါသည်။")
        sys.exit(1)
        
    try:
        expire_timestamp = int(parts[1])
        provided_hash = parts[2]
    except ValueError:
        print("[-] ❌ တရားမဝင်သော Key ဖြစ်ပါသည်။")
        sys.exit(1)
        
    # Key မှန်ကန်ကြောင်း ပြန်လည်စစ်ဆေးရန် Hashing လုပ်ခြင်း
    secret_salt = "KHANTv8.3_CUSTOM_TIME_SALT"
    raw = f"{expire_timestamp}-{secret_salt}"
    expected_hash = hashlib.sha256(raw.encode()).hexdigest().upper()[:6]
    
    if provided_hash != expected_hash:
        print("[-] ❌ မှားယွင်းနေသော License Key ဖြစ်ပါသည်။")
        sys.exit(1)
        
    # အချိန်ကုန်ဆုံးသွားပြီလား စစ်ဆေးခြင်း (Real-Time Check)
    current_time = int(time.time())
    if current_time > expire_timestamp:
        expire_date_str = datetime.fromtimestamp(expire_timestamp).strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n[-] ❌ ဤ License Key ၏ သက်တမ်း ကုန်ဆုံးသွားပါပြီ!")
        print(f"📅 ကုန်ဆုံးသွားသည့်အချိန်: {expire_date_str}")
        sys.exit(1)
        
    remaining_seconds = expire_timestamp - current_time
    days = remaining_seconds // 86400
    hours = (remaining_seconds % 86400) // 3600
    
    expire_date_str = datetime.fromtimestamp(expire_timestamp).strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n[+] ✅ License အောင်မြင်စွာ အတည်ပြုပြီးပါပြီ!")
    print(f"📅 သက်တမ်းကုန်မည့်ရက်: {expire_date_str}")
    print(f"⏳ ကျန်ရှိသောအချိန်: ရက် {days} ရက် နှင့် {hours} နာရီ ကျန်ရှိသေးသည်။")
    time.sleep(2)
    return True
