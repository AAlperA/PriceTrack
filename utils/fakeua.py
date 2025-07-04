import random

def set_uagent():
    return (
        f"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 " 
        f"(KHTML, like Gecko) Chrome/123.0.0.{random.randint(0, 9999)}" 
        f" Safari/537.{random.randint(0, 999)}"
    )