import glob
import re

import fitz

PDFS = [
    r"C:\Users\31560\Downloads\RoboMaster_M3508直流无刷减速电机使用说明V1.0（中英日）.pdf",
    r"C:\Users\31560\Downloads\RoboMaster_M3508_直流无刷电机_使用说明（中英）.pdf",
    r"C:\Users\31560\Downloads\RoboMaster_GM6020直流无刷电机使用说明20231013.pdf",
    r"C:\Users\31560\Downloads\RM_M2006_P36直流无刷减速电机使用说明.pdf",
]
KEYS = ("额定", "空载", "减速比", "重量", "尺寸", "极对数", "转矩常数", "相电阻",
        "相电感", "额定电压", "额定电流", "额定功率", "机械时间常数", "转速常数",
        "持续电流", "最大电流", "通信", "CAN", "控制频率", "编码器", "电调")

for p in PDFS:
    print("=" * 20, p.split("\\")[-1])
    try:
        doc = fitz.open(p)
    except Exception as e:
        print("  打不开", e)
        continue
    print("  页数", len(doc))
    for i in range(len(doc)):
        t = doc[i].get_text()
        hits = [k for k in KEYS if k in t]
        if len(hits) >= 4:
            lines = [l.strip() for l in t.splitlines() if l.strip()]
            keep = [l for l in lines if any(k in l for k in KEYS) or re.match(r"^[\d.]+$", l)]
            print(f"  --- p{i+1} 命中 {len(hits)}")
            print("   ", " | ".join(keep[:26]))
            break
