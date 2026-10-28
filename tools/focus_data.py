"""数据收敛：备份全量，只留关节电机，且只留 4 家。

为什么这么做（产品决策，不是技术）：
    全量目录 191 行铺得太开 —— 14 家厂商、4 个品类、参数口径各不相同，
    结果哪一块都做不深。改成「先把关节电机做精」：只留
    达妙 DM / DJI RoboMaster / 灵足 RobStride / Unitree 四家，
    参数完整度和可比性都最高，能支撑「官方参数 + 用户评价」的双栏页。

怎么做的：
    1. data/_backup/<date>/ 存全量快照（可回滚）
    2. data/focus.json 写明保留范围；build_motors.py 会读它做过滤，
       所以以后重新跑采集脚本也不会把移出的厂商带回来
    3. 其它品类的 json 移到备份区，data/ 里不再存在

回滚：pwsh tools/restore_backup.ps1
"""
from __future__ import annotations

import sys as _sys
from legacy_guard import require_legacy_ok
require_legacy_ok(__file__)

import json
import pathlib
import shutil
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
BK = DATA / "_backup" / date.today().isoformat()

KEEP_VENDORS = ["达妙 DM", "DJI RoboMaster", "灵足 RobStride", "Unitree"]
KEEP_CATEGORIES = ["actuator"]
#: 整份移走的文件（它们只含非关节电机品类）
MOVE_FILES = ["controllers_high.json", "controllers_low.json", "sensors.json"]


def main() -> None:
    BK.mkdir(parents=True, exist_ok=True)

    # 1) 全量备份
    for f in sorted(DATA.glob("*.json")):
        shutil.copy2(f, BK / f.name)
    print(f"备份 {len(list(BK.glob('*.json')))} 个 json -> {BK.relative_to(ROOT)}")

    # 2) 写焦点声明（采集脚本据此过滤，防止回滚式长回来）
    focus = {
        "note": "当前只做关节电机，且只保留四家 —— 先把一类做精，而不是十四家各一半",
        "categories": KEEP_CATEGORIES,
        "vendors": KEEP_VENDORS,
        "as_of": date.today().isoformat(),
        "backup": str(BK.relative_to(ROOT)).replace("\\", "/"),
    }
    (DATA / "focus.json").write_text(json.dumps(focus, ensure_ascii=False, indent=1),
                                     encoding="utf-8")
    print("写 data/focus.json")

    # 3) 过滤执行器
    motors = json.loads((DATA / "motors.json").read_text(encoding="utf-8"))
    kept = [r for r in motors if r["vendor"] in KEEP_VENDORS]
    (DATA / "motors.json").write_text(
        json.dumps(kept, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"motors.json：{len(motors)} -> {len(kept)} 行")

    # 4) 移走其它品类
    for name in MOVE_FILES:
        p = DATA / name
        if p.exists():
            p.unlink()
            print(f"移出 data/{name}（备份区有）")

    # 5) 图片映射只留仍在库的 id
    ids = {r["id"] for r in kept}
    for name in ("part_images.json", "part_images_fetched.json"):
        p = DATA / name
        if not p.exists():
            continue
        m = json.loads(p.read_text(encoding="utf-8"))
        m2 = {k: v for k, v in m.items() if k in ids}
        p.write_text(json.dumps(m2, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{name}：{len(m)} -> {len(m2)} 条")

    # 6) 备份里也留一份「被移走的行」，方便回滚时对照
    moved = [r for r in motors if r["vendor"] not in KEEP_VENDORS]
    (BK / "moved_out_actuators.json").write_text(
        json.dumps(moved, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"被移出的执行器 {len(moved)} 行 -> 备份区 moved_out_actuators.json")

    print("\n结果：data/ 现只含 " + "、".join(KEEP_VENDORS))
    print("回滚：pwsh tools/restore_backup.ps1")


if __name__ == "__main__":
    main()
