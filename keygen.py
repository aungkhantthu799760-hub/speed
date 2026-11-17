#!/usr/bin/env python3
"""
KHANTv8.3 - Custom Duration License Key Generator (Admin Tool)
- Compatible with V6 License Module
"""

import random
import string

def generate_v6_key(days: float) -> str:
    """ပေးထားသော ရက် (days) အပေါ်မူတည်၍ V6 Key ပုံစံဖြင့် ထုတ်ပေးခြင်း"""
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    key = f"V6-KAVIN-{days}-{random_str}"
    return key

def main():
    print("=" * 55)
    print("       KHANTv8.3 - V6 LICENSE KEY GENERATOR (ADMIN)      ")
    print("=" * 55)
    print("\n[?] သက်တမ်းအမျိုးအစား ရွေးချယ်ပါ:")
    print("  1. နာရီ (Hours) - ဥပမာ ၂၄ နာရီ = ၁ ရက်")
    print("  2. ရက် (Days)")
    print("  3. လ (Months) - ၁ လ = ရက် ၃၀ ဖြင့် တွက်မည်")
    print("  4. နှစ် (Years) - ၁ နှစ် = ရက် ၃၆၅ ဖြင့် တွက်မည်")
    
    choice = input("\n👉 ရွေးချယ်မှု (1/2/3/4): ").strip()
    
    try:
        amount = float(input("👉 ပမာဏ မည်မျှထုတ်မည်နည်း (ဥပမာ - 7 ရက်ဆိုလျှင် 7 ဟုထည့်ပါ): ").strip())
    except ValueError:
        print("[-] မှားယွင်းသော ထည့်သွင်းမှု ဖြစ်ပါသည်။ နံပါတ်သာ ထည့်ပါ။")
        return

    days_value = 0.0
    unit_label = ""

    if choice == "1":
        days_value = amount / 24.0
        unit_label = f"{amount} နာရီ"
    elif choice == "2":
        days_value = float(amount)
        unit_label = f"{amount} ရက်"
    elif choice == "3":
        days_value = float(amount * 30.0)
        unit_label = f"{amount} လ"
    elif choice == "4":
        days_value = float(amount * 365.0)
        unit_label = f"{amount} နှစ်"
    else:
        print("[-] ရွေးချယ်မှု မမှန်ကန်ပါ။")
        return

    key = generate_v6_key(days_value)

    print("\n" + "=" * 55)
    print(f"[+] ✅ Successfully Generated V6 Key!")
    print(f"🔑 License Key : {key}")
    print(f"⏳ သက်တမ်း     : {unit_label} ({days_value} ရက်စာ)")
    print("=" * 55)

if __name__ == "__main__":
    main()

