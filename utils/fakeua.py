import random

def set_uagent():
    platforms = [
        "Windows NT 10.0; Win64; x64",
        "Macintosh; Intel Mac OS X 10_15_7",
        "X11; Linux x86_64"
    ]
    chrome_version = f"{random.randint(115, 118)}.0.{random.randint(5000, 5999)}.{random.randint(0, 150)}"
    platform = random.choice(platforms)
    return f"Mozilla/5.0 ({platform}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36"
