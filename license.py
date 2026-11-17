# =====================================================================
# license.py - KAVIN V8 License System (1 Key = 1 Device)
# =====================================================================

import os
import json
import hashlib
import hmac
import time
import uuid
from datetime import datetime

LICENSE_FILE = "license_status.json"
USED_KEYS_FILE = "used_keys.json"
SECRET_KEY = b"KavinV8SecretKey2024!@#$%^&*()"

def get_device_id():
    """Get a unique ID for this device"""
    try:
        # Android/Linux မှာ MAC ကို ရှာမယ်
        mac = uuid.getnode()
        return str(mac)
    except:
        return "UNKNOWN_DEVICE"

def generate_key(unit: str, amount: int) -> str:
    if unit == "u":
        payload_str = "V8-KAVIN-UNLIMITED-XXXX"
    else:
        payload_str = f"V8-KAVIN-{unit}{amount}-XXXX"
    
    rand_part = ''.join(os.urandom(4).hex().upper())
    payload = payload_str.replace("XXXX", rand_part)
    
    sig = hmac.new(SECRET_KEY, payload.encode(), hashlib.sha256).hexdigest()[:4].upper()
    return f"{payload}-{sig}"

def verify_key_format(key: str) -> tuple:
    try:
        parts = key.split("-")
        if len(parts) != 5 or parts[0] != "V8" or parts[1] != "KAVIN":
            return False, "", 0
        
        time_part = parts[2]
        rand_part = parts[3]
        sig = parts[4]
        
        payload = f"V8-KAVIN-{time_part}-{rand_part}"
        expected_sig = hmac.new(SECRET_KEY, payload.encode(), hashlib.sha256).hexdigest()[:4].upper()
        
        if sig != expected_sig:
            return False, "", 0
        
        if time_part == "UNLIMITED":
            return True, "u", 0
        
        unit = time_part[0]
        amount = int(time_part[1:])
        
        if unit not in ("h", "d", "m"):
            return False, "", 0
            
        return True, unit, amount
    except:
        return False, "", 0

def load_used_keys() -> dict:
    try:
        with open(USED_KEYS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_used_keys(data: dict):
    try:
        with open(USED_KEYS_FILE, "w") as f:
            json.dump(data, f)
    except:
        pass

def save_status(expiry_ts: float):
    try:
        with open(LICENSE_FILE, "w") as f:
            json.dump({"expiry": expiry_ts}, f)
    except Exception:
        pass

def load_status() -> float:
    try:
        with open(LICENSE_FILE, "r") as f:
            data = json.load(f)
            return data.get("expiry", 0)
    except Exception:
        return 0

def check_approval() -> tuple:
    expiry = load_status()
    if expiry == 0:
        return False, "No License"
    
    if expiry == float('inf'):
        return True, "Unlimited"
        
    if time.time() < expiry:
        dt = datetime.fromtimestamp(expiry).strftime('%Y-%m-%d %H:%M')
        remaining = int(expiry - time.time())
        days = remaining // 86400
        hours = (remaining % 86400) // 3600
        mins = (remaining % 3600) // 60
        
        rem_str = ""
        if days > 0: rem_str += f"{days}d "
        if hours > 0: rem_str += f"{hours}h "
        rem_str += f"{mins}m"
        
        return True, f"Valid ({rem_str.strip()} left)"
    else:
        return False, "Expired"

def activate(key: str) -> tuple:
    valid, unit, amount = verify_key_format(key)
    if not valid:
        return False, "Invalid Key Format"
    
    # ⭐ Key ကို တခြားသူ သုံးပြီးသားလား စစ်မယ်
    used_keys = load_used_keys()
    device_id = get_device_id()
    
    if key in used_keys:
        if used_keys[key] != device_id:
            return False, "❌ This key is already used on another device!"
        # ဒီ Device ပဲဆိုရင် ဆက်သွားမယ်
    
    # ⭐ အသစ်သုံးမယ်ဆိုရင် သိမ်းမယ်
    used_keys[key] = device_id
    save_used_keys(used_keys)
    
    if unit == "u":
        save_status(float('inf'))
        return True, "Activated: Unlimited (This Device Only)"
        
    if unit == "h":
        seconds = amount * 3600
    elif unit == "d":
        seconds = amount * 86400
    elif unit == "m":
        seconds = amount * 30 * 86400
    else:
        return False, "Invalid Unit"
        
    current_expiry = load_status()
    if current_expiry == float('inf'):
        return True, "Already Unlimited"
        
    base_time = current_expiry if current_expiry > time.time() else time.time()
    new_expiry = base_time + seconds
    save_status(new_expiry)
    
    dt = datetime.fromtimestamp(new_expiry).strftime('%Y-%m-%d %H:%M')
    return True, f"Activated until {dt} (This Device Only)"
