"""把型号页右侧的「实际使用」静态卡片换成评分组件，并把评分快照放进 public。"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
P = ROOT / "scripts" / "build_wiki.py"
s = P.read_text(encoding="utf-8")

# 1) 社区侧：从「写死的空态卡片」换成组件
start = s.index('        # 社区一侧：没有数据就明说，不用示例充数')
end = s.index('        # 关节电机的深度指标')
NEW = '''        # 社区一侧：评分组件（星标 + 分布 + 打分入口），评论由页尾 giscus 承担。
        # 这里不再写死「暂无评分」——组件会自己判断：有后端读实时值，
        # 没有就读构建快照，都没有才显示空态。
        comm = f\'\'\'
<div class="part-comm">
<PartRating part-id="{pid}" />
</div>
\'\'\'

'''
s = s[:start] + NEW + s[end:]

# 2) 评分快照：有就拷进 public（纯静态部署要读它）
anchor = '    print(f"  产品图同步 {copied} 张'
add = '''    # 评分快照：CI 上没有库，用 --empty 写空快照；本地导过就用真值。
    snap = ROOT / "data" / "ratings_snapshot.json"
    if snap.exists():
        (pub / "ratings.json").write_bytes(snap.read_bytes())
        try:
            n = len(json.loads(snap.read_text(encoding="utf-8")).get("parts") or {})
        except Exception:
            n = 0
        print(f"  评分快照 -> public/ratings.json（{n} 个零件有分）")
    else:
        (pub / "ratings.json").write_text(
            json.dumps({"total_ratings": 0, "parts": {}, "snapshot": True},
                       ensure_ascii=False), encoding="utf-8")
        print("  评分快照：无，写空表")

'''
s = s.replace(anchor, add + anchor, 1)

P.write_text(s, encoding="utf-8")
print("型号页已接评分组件 + 快照")
