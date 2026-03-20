import hashlib
from engine.language_bank import LANGUAGE_BANK

def pick_sentence(key, seed_text="default"):
    options = LANGUAGE_BANK.get(key, [])
    if not options:
        return ""
    h = hashlib.md5(seed_text.encode("utf-8")).hexdigest()
    idx = int(h, 16) % len(options)
    return options[idx]
