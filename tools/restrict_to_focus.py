"""收窄部件库：只留「关节电机」品类下的四家厂商，其余全部移进备份区。

为什么要这一步：
    上一轮把归档里能过闸门的 868 条全导进来了（102 家厂商、6 个品类），
    结果部件库变成一锅粥：厂商筛选挤三行、B 级未核对数据和 A 级手册数据混在一起。
    先把范围收回到「关节电机 + 四家」，让 A 级数据重新成为主体。

保留：
    data/catalog/actuator/damiao.json           达妙 DAMIAO
    data/catalog/actuator/dji-robomaster.json   大疆 DJI
    data/catalog/actuator/unitree.json          宇树 Unitree
    data/catalog/actuator/lingzu-robstride.json 灵足 RobStride

顺带合并同名厂商的分裂文件：
    dji.json        -> dji-robomaster.json      （同一家的两个 slug）
    robstride.json  -> lingzu-robstride.json
    high-torque.json -> damiao.json             （达妙的英文品牌名，之前没并上）

移到：
    data/_backup/<date>-archive-import/catalog/**   完整快照，路径不变，可整棵拷回
    data/_backup/<date>-archive-import/offers/**

回滚：把 catalog/ 与 offers/ 整棵拷回 data/ 即可。
"""
from __future__ import annotations

import sys as _sys
from _deprecated import require_legacy_ok
require_legacy_ok(__file__)

import json
import pathlib
import shutil
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CAT = DATA / "catalog"
OFF = DATA / "offers"
BK = DATA / "_backup" / f"{date.today().isoformat()}-archive-import"

KEEP_CATEGORY = "actuator"
KEEP_VENDORS = ["达妙 DAMIAO", "大疆 DJI", "宇树 Unitree", "灵足 RobStride"]
#: 目标文件名（一家一个文件）
TARGET = {
    "达妙 DAMIAO": "damiao",
    "大疆 DJI": "dji-robomaster",
    "宇树 Unitree": "unitree",
    "灵足 RobStride": "lingzu-robstride",
}
#: 归档里同一家的别名，合并时按这个归一
ALIAS = {
    "DAMIAO": "达妙 DAMIAO", "High Torque": "达妙 DAMIAO",
    "HIGH TORQUE": "达妙 DAMIAO", "hightorque": "达妙 DAMIAO",
    "高擎": "达妙 DAMIAO", "达妙 DM": "达妙 DAMIAO",
    "DJI": "大疆 DJI", "RoboMaster": "大疆 DJI", "DJI RoboMaster": "大疆 DJI",
    "RobStride": "灵足 RobStride", "Unitree": "宇树 Unitree",
}


def main() -> None:
    if not CAT.exists():
        print("没有 data/catalog")
        return

    # 1) 全量快照（先备份再动）
    (BK / "catalog").parent.mkdir(parents=True, exist_ok=True)
    if not (BK / "catalog").exists():
        shutil.copytree(CAT, BK / "catalog")
        print(f"备份 catalog -> {BK.relative_to(ROOT)}/catalog")
    if OFF.exists() and not (BK / "offers").exists():
        shutil.copytree(OFF, BK / "offers")
        print(f"备份 offers  -> {BK.relative_to(ROOT)}/offers")

    # 2) 收集四家的 actuator 行（跨文件合并 + 厂商名归一）
    merged: dict[str, dict[str, dict]] = {v: {} for v in KEEP_VENDORS}
    for f in sorted((CAT / KEEP_CATEGORY).glob("*.json")):
        for r in json.loads(f.read_text(encoding="utf-8")):
            v = ALIAS.get(r["vendor"], r["vendor"])
            if v not in merged:
                continue
            r["vendor"] = v
            merged[v][r["id"]] = r          # 同 id 覆盖，天然去重

    n_kept = sum(len(x) for x in merged.values())
    if n_kept == 0:
        print("没找到四家的关节电机，什么都没动")
        return

    # 3) 清空后重建（只留 actuator 下的四家）
    shutil.rmtree(CAT)
    (CAT / KEEP_CATEGORY).mkdir(parents=True)
    for v, rows in merged.items():
        items = sorted(rows.values(), key=lambda r: (r.get("source_tier") != "A",
                                                    r["model"]))
        p = CAT / KEEP_CATEGORY / f"{TARGET[v]}.json"
        p.write_text(json.dumps(items, ensure_ascii=False, indent=1) + "\n",
                     encoding="utf-8")
        a = sum(1 for r in items if r.get("source_tier") == "A")
        print(f"  保留 {p.name:24s} {len(items):3d} 条（A 级 {a} / B 级 {len(items) - a}）")

    # 4) 优惠只留这四家 + 站点级
    keep_offer = {"damiao", "unitree", "lingzu-robstride", "site"}
    for f in sorted(OFF.glob("*.json")):
        if f.stem not in keep_offer:
            f.unlink()
            print(f"  移出 offers/{f.name}（备份区有）")

    # 5) 收录范围写回 focus.json
    fp = DATA / "focus.json"
    d = json.loads(fp.read_text(encoding="utf-8")) if fp.exists() else {}
    d.update({
        "categories": [KEEP_CATEGORY],
        "vendors": KEEP_VENDORS,
        "note": "只收关节电机，且只留四家。归档导入的 868 条已整批移入 "
                f"{BK.relative_to(ROOT)}，需要时可整棵拷回。",
    })
    fp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\n结果：{n_kept} 件 / {len(KEEP_VENDORS)} 家")
    print(f"备份：{BK.relative_to(ROOT)}（catalog/ 与 offers/ 整棵可拷回）")


if __name__ == "__main__":
    main()
