"""数据库：engine、建表、种子灌入。"""
from __future__ import annotations

import json
import pathlib

from sqlmodel import Session, SQLModel, create_engine, select

from .config import settings
from ..models import Offer, Part, Post, User
from .security import hash_password

_engine = None


def engine():
    global _engine
    if _engine is None:
        settings.db_path.parent.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
        )
    return _engine


def reset_engine() -> None:
    """测试用：换库后重建。"""
    global _engine
    if _engine is not None:
        _engine.dispose()
    _engine = None


def create_tables() -> None:
    SQLModel.metadata.create_all(engine())


def session() -> Session:
    return Session(engine())


# ── 种子 ────────────────────────────────────────────────────────────────────
SEED_FILES = ["motors.json", "controllers_high.json", "controllers_low.json",
              "sensors.json"]


def _search_blob(r: dict) -> str:
    sp = r.get("specs") or {}
    return " ".join(str(x) for x in (
        r.get("vendor"), r.get("vendor_cn"), r.get("model"), r.get("title"),
        sp.get("comm"), sp.get("encoder"), r.get("notes"),
    ) if x).lower()


def iter_seed_files():
    """按优先级产出数据文件。

    1. data/catalog/<品类>/<厂商>.json —— 人工维护的源，一家一文件（PR 友好）
    2. 旧的扁平文件（motors.json / controllers_* / sensors.json）—— 兼容老部署

    这和 scripts/load_catalog.py 是同一套优先级；两边都改会漂移，
    所以这里只做「哪个目录存在」的判断，解析逻辑保持一致。
    """
    cat_dir = settings.data_dir / "catalog"
    files = sorted(cat_dir.glob("*/*.json")) if cat_dir.exists() else []
    if files:
        return files
    return [settings.data_dir / fn for fn in SEED_FILES]


def seed_catalog(db: Session) -> dict[str, int]:
    """灌零件与优惠。幂等；种子里没有的行会被删掉（评论随之级联）。"""
    stats: dict[str, int] = {}
    keep: list[str] = []
    for p in iter_seed_files():
        fn = p.name
        if not p.exists():
            stats[fn] = 0
            continue
        rows = json.loads(p.read_text(encoding="utf-8"))
        stats[fn] = len(rows)
        for r in rows:
            keep.append(r["id"])
            obj = db.get(Part, r["id"])
            if obj is None:
                obj = Part(id=r["id"])
                db.add(obj)
            obj.category = r["category"]
            obj.subtype = r["subtype"]
            obj.vendor = r["vendor"]
            obj.vendor_cn = r.get("vendor_cn")
            obj.model = r["model"]
            obj.title = r["title"]
            obj.url = r.get("url")
            obj.source_tier = r.get("source_tier", "B")
            obj.verified = bool(r.get("verified"))
            obj.last_checked = r.get("last_checked")
            obj.price_cny = r.get("price_cny")
            obj.specs = r.get("specs") or {}
            obj.notes = r.get("notes") or ""
            obj.origin = r.get("origin")
            obj.search = _search_blob(r)

    # 清扫旧 id
    stale = [p for p in db.exec(select(Part)).all() if p.id not in set(keep)]
    for p in stale:
        db.delete(p)
    stats["removed_stale"] = len(stale)

    offers_path = settings.data_dir / "offers.json"
    if offers_path.exists():
        offers = json.loads(offers_path.read_text(encoding="utf-8"))
        for o in offers:
            obj = db.get(Offer, o["id"])
            if obj is None:
                obj = Offer(id=o["id"])
                db.add(obj)
            obj.part_id = o.get("part_id")
            obj.vendor = o.get("vendor")
            obj.kind = o["kind"]
            obj.title = o["title"]
            obj.detail = o.get("detail", "")
            obj.url = o.get("url")
            obj.starts_on = o.get("starts_on")
            obj.expires_on = o.get("expires_on")
            obj.demo = bool(o.get("demo"))
        stats["offers"] = len(offers)

    db.commit()
    return stats


DEMO_USERS = [
    # 站方账号：编者按的署名主体。本站是一个真实存在的实体，不冒充任何用户。
    ("roboselect", "RoboSelect 编辑部", "本站编辑。只写编者按，不改用户评价。", 0, True),
    # 演示账号：仅供试功能，不产生任何「使用经历」类内容
    ("demo1", "演示用户 A", "用于功能演示，不代表真实使用经历。", 0, False),
]

#: 种子内容只有**站方署名的编者按**，且每句话都要能指回数据本身。
#: 刻意不写「我跑了三个月」「外壳 62℃」这类无法核实的个人经历 ——
#: 本站的立意是真实使用信息，编造的体验比空着更糟。
DEMO_POSTS = [
    dict(kind="discussion", author="roboselect", part_id=None,
         title="编者按：选关节时，先把 ω_NL × 腿长 算出来，再看扭矩",
         tags="方法论,选型",
         body="""这是站方按目录数据整理的判断顺序，不是个人使用经验。

1. **先算 `ω_NL × 腿长`**，它决定腿尖速度的天花板。目录里 80:1 的谐波件（如 eRob110H-80）
   空载转速 3.93 rad/s，配 1.3 m 腿长时腿尖上限约 5.1 m/s。
2. **再看 `转子惯量`（armature）占关节表观惯量的比例**。高减速比件的反射惯量常占 40–80%，
   膝部更高——它错了，策略到真机上会高频振荡。
3. **最后才看扭矩密度**。它是结果不是原因，由定子尺寸与减速比共同决定。

想看具体数字：在部件库按 `转子惯量` 排序，或调 `GET /api/semantics` 拿口径定义。"""),
    dict(kind="discussion", author="roboselect", part_id=None,
         title="编者按：「峰值扭矩」在采购合同里要写清四件事",
         tags="采购,口径",
         body="""本站目录里 `tau_peak_Nm` 存在多种口径。评审规格书或谈合同时要求写清：

1. 分子是**峰值**还是**额定**；
2. 峰值对应的**允许持续时间**与**初始温度**；
3. 分母是否**整机含线缆**称重；
4. 测量端是**电机端**还是**输出端**。

写不进合同的参数，验收时不具备约束力。详见 `/semantics` 页的 RL-01 / RL-02 两条红线。"""),
]

def seed_community(db: Session) -> dict[str, int]:
    """造几个示例用户与帖子，让社区不空。真实部署可关掉。"""
    users: dict[str, User] = {}
    for handle, name, bio, rep, staff in DEMO_USERS:
        u = db.exec(select(User).where(User.handle == handle)).first()
        if u is None:
            u = User(handle=handle, display_name=name, bio=bio,
                     password_hash=hash_password("roboselect"),
                     avatar_hue=(abs(hash(handle)) % 360), is_staff=staff,
                     reputation=rep)
            db.add(u)
        users[handle] = u
    db.commit()

    n = 0
    for spec in DEMO_POSTS:
        exists = db.exec(select(Post).where(Post.title == spec["title"])).first()
        if exists:
            continue
        author = users.get(spec["author"])
        if author is None:
            continue
        db.add(Post(kind=spec["kind"], title=spec["title"], body=spec["body"],
                    author_id=author.id, part_id=spec.get("part_id"),
                    tags=spec.get("tags", ""), rating=spec.get("rating"),
                    use_case=spec.get("use_case"),
                    own_hardware=spec.get("own_hardware", False),
                    score=spec.get("score", 0)))
        n += 1
    db.commit()
    # 刻意不灌任何示例评价。这个站的立意是「真实使用信息」，
    # 编造的种子评价一旦被当真，比一条评价都没有坏得多。
    return {"users": len(users), "posts": n}
