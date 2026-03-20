from engine.language_bank import LANGUAGE_BANK

for key, vals in LANGUAGE_BANK.items():
    print(f"\n[{key}]")
    for v in vals:
        print("-", v)
