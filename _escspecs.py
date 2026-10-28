import fitz

PDFS = {
    "C620": r"C:\Users\31560\Downloads\RoboMaster__C620_无刷电机调速器使用说明.pdf",
    "C610": r"C:\Users\31560\Downloads\RoboMaster__C610_无刷电机调速器使用说明.pdf",
    "C615": r"C:\Users\31560\Downloads\RoboMaster_C615_无刷电机调速器说明书.pdf",
}
KW = ("输入电压", "持续", "峰值", "最大", "通信", "CAN", "控制频率", "重量",
      "尺寸", "电流", "转速", "PWM", "支持电机", "效率")

for name, p in PDFS.items():
    print("=" * 22, name)
    try:
        doc = fitz.open(p)
    except Exception as e:
        print("  打不开", e)
        continue
    print("  页数", len(doc))
    for i in range(len(doc)):
        page = doc[i]
        try:
            tabs = page.find_tables()
        except Exception:
            tabs = None
        if tabs and tabs.tables:
            for t in tabs.tables:
                rows = t.extract()
                flat = " ".join(" ".join(str(c) for c in r if c) for r in rows)
                if not any(k in flat for k in ("输入电压", "持续电流", "重量", "支持")):
                    continue
                print(f"  --- p{i+1} 表")
                for r in rows[:20]:
                    cells = [str(c).strip() if c else "" for c in r]
                    if any(cells):
                        print("     ", " | ".join(cells[:5]))
        else:
            t = page.get_text()
            lines = [l.strip() for l in t.splitlines() if l.strip()]
            hits = [l for l in lines if any(k in l for k in KW)]
            if len(hits) >= 3:
                print(f"  --- p{i+1} 文本")
                for l in hits[:18]:
                    print("     ", l[:90])
