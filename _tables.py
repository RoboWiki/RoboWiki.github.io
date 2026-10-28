import re

import fitz

PDFS = {
    "M3508(新版)": r"C:\Users\31560\Downloads\RoboMaster_M3508_直流无刷电机_使用说明（中英）.pdf",
    "GM6020": r"C:\Users\31560\Downloads\RoboMaster_GM6020直流无刷电机使用说明20231013.pdf",
    "M2006": r"C:\Users\31560\Downloads\RM_M2006_P36直流无刷减速电机使用说明.pdf",
}

for name, p in PDFS.items():
    print("=" * 24, name)
    doc = fitz.open(p)
    for i in range(len(doc)):
        page = doc[i]
        try:
            tabs = page.find_tables()
        except Exception:
            continue
        if not tabs.tables:
            continue
        for t in tabs.tables:
            rows = t.extract()
            flat = " ".join(" ".join(str(c) for c in r if c) for r in rows)
            if not any(k in flat for k in ("额定", "转矩", "减速比", "极对")):
                continue
            print(f"--- p{i+1}")
            for r in rows[:26]:
                cells = [str(c).strip() if c else "" for c in r]
                if any(cells):
                    print("   ", " | ".join(cells[:5]))
