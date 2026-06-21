import subprocess
import time
import socket
import concurrent.futures
import sys
import requests

# Prefixes ending in 'h'
prefixes = [
    ("tech", "ٹیکنالوجی"),
    ("mech", "میکینیکل"),
    ("arch", "تعمیر / آرک"),
    ("graph", "گراف / تصویر"),
    ("synth", "ہم آہنگی / سنتھ"),
    ("mesh", "جال / میش"),
    ("path", "راستہ"),
    ("dash", "تیزی / ڈیش"),
    ("flash", "چمک / فلیش"),
    ("epoch", "دور / زمانہ"),
    ("morph", "شکل / مورف"),
    ("catch", "پکڑنا / کیچ"),
    ("match", "مماثلت"),
    ("batch", "بیچ / مجموعہ"),
    ("switch", "سوئچ / بدلنا"),
    ("touch", "ٹچ / چھونا"),
    ("launch", "لانچ / آغاز"),
    ("branch", "برانچ / شاخ"),
    ("reach", "پہنچ"),
    ("search", "تلاش / سرچ"),
    ("coach", "کوچ / رہنما")
]

# Suffixes starting with 'h' meaning center, base, core, foundation
suffixes = [
    # English
    ("hub", "مرکز"),
    ("home", "گھر / مرکز"),
    ("house", "گھر / ادارہ"),
    ("heart", "دل / مرکز"),
    ("head", "سر / سربراہ"),
    ("hq", "ہیڈ کوارٹر"),
    ("host", "ہوسٹ / میزبان"),
    ("hive", "چھتہ / مرکز"),
    ("haven", "پناہ گاہ"),
    ("hold", "پکڑ / بنیاد"),
    ("hole", "سوراخ / مرکز"),
    ("hall", "ہال / مرکز"),
    ("hotspot", "ہاٹ سپاٹ / مرکز"),
    ("habitat", "رہائش گاہ"),
    ("harbor", "بندرگاہ / مرکز"),
    ("hut", "جھونپڑی / مرکز"),

    # Latin / Others
    ("hortus", "باغ / مرکز"),
    ("hestia", "گھر کا مرکز / ہیسٹیا"),
    ("hedra", "بنیاد (یونانی)"),
    ("hodos", "راستہ / ہودوس"),
    ("hypo", "بنیاد کے نیچے"),
    ("hyle", "مادہ / بنیاد"),

    # Let's invent a few more "h" words that sound like centers
    ("halo", "ہالہ / مرکز کے گرد"),
    ("helix", "ہیلکس / گھماؤ"),
    ("herd", "ریوڑ / مرکز"),
    ("helm", "قیادت / مرکز"),
    ("hatch", "نکلنا / مرکز"),
]

def check_domain_socket(domain):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect(("whois.verisign-grs.com", 43))
        s.send((domain + "\r\n").encode())
        response = b""
        while True:
            data = s.recv(4096)
            if not data:
                break
            response += data
        s.close()

        output = response.decode('utf-8', errors='ignore').lower()
        if 'no match for' in output or 'not found' in output:
            return True
        return False
    except Exception as e:
        return None

def process_item(item):
    p_eng, p_urdu, s_eng, s_urdu = item

    # Overlap logic: tech + hub = techub
    # They both share 'h'
    domain = f"{p_eng[:-1]}{s_eng}.com"

    is_avail = check_domain_socket(domain)
    if is_avail is None:
        time.sleep(0.5)
        is_avail = check_domain_socket(domain)

    if is_avail:
        return (domain, p_eng, p_urdu, s_eng, s_urdu)
    return None

def run_checks():
    combinations = []
    for p_eng, p_urdu in prefixes:
        for s_eng, s_urdu in suffixes:
            combinations.append((p_eng, p_urdu, s_eng, s_urdu))

    print(f"Total combinations: {len(combinations)}")
    sys.stdout.flush()

    available = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(process_item, item) for item in combinations]
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res:
                available.append(res)
                print(f"Found: {res[0]} (Total: {len(available)})")
                sys.stdout.flush()

    # Sort
    available.sort(key=lambda x: len(x[0]))

    with open('techub_style_domains.md', 'w') as f:
        f.write("| No. | Domain | Prefix (اردو معنی) | Suffix (اردو معنی) |\n")
        f.write("| --- | --- | --- | --- |\n")
        for idx, res in enumerate(available, 1):
            f.write(f"| {idx} | {res[0]} | {res[1]} ({res[2]}) | {res[3]} ({res[4]}) |\n")

if __name__ == "__main__":
    run_checks()
