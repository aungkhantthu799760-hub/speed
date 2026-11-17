import os
import hashlib
import platform

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
    """Admin ဘက်မှ Device ID တစ်ခုအတွက် သီးသန့် Key ဖန်တီးပေးရန် (မျှဝေ၍မရပါ)"""
    secret_salt = "KHANTv8.3_SECURE_SALT"
    raw = device_id + secret_salt
    key_hash = hashlib.sha256(raw.encode()).hexdigest().upper()
    return f"KHANT-{key_hash[:4]}-{key_hash[4:8]}-{key_hash[8:12]}"
