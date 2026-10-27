"""参数口径规范（可机读版）。

把 README 里那段「为什么参数不可比」变成结构化数据，供前端、校验器、
以及 MCP 的 `get_parameter_semantics` 工具共用同一份。

设计参考 roboparts.cc/mcp 的同名工具：口径规范必须**可被机器读取**，
否则每个使用者都要自己重新理解一遍。
"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["semantics"])

#: 参数语义：每个字段是什么意思、单位、方向、缺失含义
FIELD_SEMANTICS = {
    "tau_peak_Nm": {
        "label": "峰值扭矩", "unit": "N·m", "higher_is_better": True,
        "meaning": "分子通常是堵转或短时过载值，必须配持续时间与初始温度才有工程意义",
        "missing_means": "未公布峰值扭矩，不能按额定代替",
    },
    "tau_rated_Nm": {
        "label": "额定扭矩", "unit": "N·m", "higher_is_better": True,
        "meaning": "可连续输出且热稳定的扭矩，需注明母线电压与环境温度",
        "missing_means": "未公布额定值；此时峰值/额定比不可计算，不要假设为 2",
    },
    "tau_basis": {
        "label": "扭矩口径", "enum": ["peak", "rated"],
        "meaning": "本行 tau_peak_Nm 对应的是峰值还是额定；两者混比会让排序整体反转",
        "missing_means": "口径不明，该行不应参与跨厂商比较",
    },
    "mass_kg": {
        "label": "质量", "unit": "kg", "higher_is_better": False,
        "meaning": "整机（含减速器、编码器、刹车、外壳、线缆）称重值",
        "missing_means": "未公布；用扭矩反推质量会让误差进入 tau^0.666 的杠杆",
        "known_bias": "同一机座换绕组时质量不变但扭矩会变，按扭矩估质量会多收 30–47%",
    },
    "gear": {
        "label": "减速比", "unit": ":1", "higher_is_better": None,
        "meaning": "给定时 armature 随 N² 放大；不判优劣——高减速比换扭矩但压死速度",
        "missing_means": "未公布；无法由转速反解，armature 不可计算",
    },
    "speed_noload_rpm": {
        "label": "空载转速", "unit": "rpm", "higher_is_better": True,
        "meaning": "输出端空载转速；与减速比由速度律耦合，决定腿尖速度上限",
        "missing_means": "未公布；不能与 sec/60° 直接按数值比（量纲互逆）",
    },
    "rotor_inertia_kgm2": {
        "label": "转子惯量", "unit": "kg·m²", "higher_is_better": False,
        "meaning": "电机侧转子惯量。若厂商直接给折算值，见 inertia_basis=output",
        "missing_means": "未公布；不要用质量或包络估算后当成实测",
    },
    "inertia_basis": {
        "label": "惯量口径", "enum": ["rotor", "output"],
        "meaning": "rotor=电机侧；output=厂商已折算到输出侧（等于 N²·J）",
        "missing_means": "口径不明，armature 无法确定",
    },
    "armature_kgm2": {
        "label": "关节反射惯量", "unit": "kg·m²", "higher_is_better": None,
        "meaning": "MuJoCo 关节的 armature，等于 N²·J。高减速比时常占关节表观惯量 40–80%",
        "missing_means": "无法用于仿真；不要填 0，0 表示「理想无惯量电机」",
    },
    "frictionloss_Nm": {
        "label": "库仑摩擦", "unit": "N·m", "higher_is_better": False,
        "meaning": "几乎无厂商公布。留空比填一个估计值诚实",
        "missing_means": "未公布，仿真中该项应标为「假设值 0」而非「实测 0」",
    },
    "source_tier": {
        "label": "来源等级", "enum": ["A", "B", "C"],
        "meaning": "A=官方 datasheet 逐项核对；B=厂商页面或广泛引用，未逐项复核；C=二手来源",
        "missing_means": "来源不明",
    },
    "price_cny": {
        "label": "参考价", "unit": "¥", "higher_is_better": False,
        "meaning": "挂牌或公开报价，不含运费税费，不是实时价",
        "missing_means": "无公开报价；不等于买不到",
    },
}

#: 物理红线：超阈值需人工复核，不构成合规判定
RED_LINES = [
    {"id": "RL-01", "name": "扭矩密度",
     "formula": "tau_peak_Nm / mass_kg",
     "review_above": 120.0, "absurd_above": 200.0, "unit": "N·m/kg",
     "why": "受永磁体剩磁、铜损散热与减速器许用扭矩共同限制，控制算法无法突破材料极限",
     "common_trick": "用峰值除以裸电机质量（不含减速器/外壳/编码器/刹车），可把数字做大 2–4 倍",
     "how_to_check": "确认分子是额定还是峰值、分母是否为整机含线缆称重值"},
    {"id": "RL-02", "name": "峰值/额定比",
     "formula": "tau_peak_Nm / tau_rated_Nm",
     "review_above": 3.0, "absurd_above": 5.0, "unit": ":1",
     "why": "峰值受绕组热容与磁路饱和限制，是时间的函数而非常数",
     "common_trick": "标注 1 秒甚至 100 ms 的瞬时值作为峰值，且不说明",
     "how_to_check": "问：这个峰值能持续几秒？起始温度多少？连续做多少次循环？"},
    {"id": "RL-03", "name": "背隙测量条件",
     "why": "背隙随加载扭矩变化，空载值可显著优于 ±3% 额定扭矩下的测量值",
     "how_to_check": "问：测量加载扭矩是多少？是减速器背隙还是含轴承与法兰的整机回差？"},
    {"id": "RL-04", "name": "重复定位 vs 绝对精度",
     "why": "两者通常相差 1–2 个数量级，混用即失去意义",
     "how_to_check": "要求分别给出 repeatability 与 absolute accuracy，并注明测量温度"},
    {"id": "RL-05", "name": "防护等级作用范围",
     "why": "关节薄弱点通常在出线口与输出轴动密封；动密封还会带来附加摩擦扭矩",
     "how_to_check": "问：出线口是否同等级？动密封带来的附加摩擦扭矩是多少？"},
    {"id": "RL-06", "name": "编码器位数≠系统精度",
     "why": "分辨率是量化步长下界，不含齿隙、柔轮变形、热漂移与安装误差",
     "how_to_check": "要求给出输出端（而非电机端）实测重复定位精度"},
]

#: 单位换算（数学恒等式，可无损）
CONVERSIONS = [
    {"from": "rpm", "to": "rad/s", "formula": "rad_s = rpm * pi / 30"},
    {"from": "sec/60deg", "to": "rad/s", "formula": "rad_s = (pi/3) / t_sec",
     "warning": "与 rad/s 量纲互逆：数值越小越快。直接按数值排序会得到相反结论"},
    {"from": "kgf·cm", "to": "N·m", "formula": "Nm = kgf_cm * 0.0980665"},
    {"from": "arcmin", "to": "deg", "formula": "deg = arcmin / 60"},
    {"from": "g·cm²", "to": "kg·m²", "formula": "kgm2 = gcm2 * 1e-7"},
    {"from": "bit(单圈)", "to": "deg(量化步长)", "formula": "deg_step = 360 / 2**bits",
     "warning": "这是分辨率下界，不是定位精度（见 RL-06）"},
]

#: 可比性分级
COMPARABILITY = [
    {"grade": "A", "name": "可直接比较",
     "condition": "同一物理量 + 同一负载/温度/电压工况 + 同一测量端（输出端）+ 声明额定或峰值"},
    {"grade": "B", "name": "换算后可比",
     "condition": "同一物理量，单位不同但换算关系确定，且工况声明一致"},
    {"grade": "C", "name": "仅同厂商内可比",
     "condition": "有数值但缺工况声明；同厂商内部口径通常自洽"},
    {"grade": "D", "name": "不可比",
     "condition": "定性描述、缺失、或物理量本身不同；放进对比表就是选型事故的起点"},
]

#: 向供应商问询的清单（可直接复制进技术协议）
SUPPLIER_QUESTIONS = [
    "额定扭矩：同时索取母线电压、环境温度、连续运行时长、测量端（电机端/输出端）",
    "峰值扭矩：同时索取允许持续时间、起始温度、循环占空比",
    "背隙：同时索取测量加载扭矩、是减速器背隙还是整机回差",
    "精度：区分重复定位精度与绝对定位精度，并注明测量温度",
    "质量：确认是否含减速器、编码器、刹车、外壳、线缆",
    "IP 等级：确认是否覆盖出线口与输出轴动密封",
    "写不进技术协议的参数，验收时不具备约束力",
]

#: 三态语义：本平台所有判定只有这三种，且「不知道」不等于「不能」
TRINARY = {
    "values": ["yes", "no", "unknown"],
    "rules": [
        "unknown 表示证据不足，既不计入兼容也不计入不兼容",
        "null 字段表示未公布，不等于「不支持该特性」",
        "只有明确标注不自持时才给 no；猜测一律 unknown",
    ],
    "why": "把「不知道」误判成「不能」会淘汰可用方案；误判成「能」会造成装机失败。前者更常见，也更贵。",
}


@router.get("/semantics")
def get_semantics():
    """参数口径规范（机读版）。前端「口径说明」页与 MCP 工具共用这一份。"""
    return {
        "fields": FIELD_SEMANTICS,
        "red_lines": RED_LINES,
        "conversions": CONVERSIONS,
        "comparability": COMPARABILITY,
        "supplier_questions": SUPPLIER_QUESTIONS,
        "trinary": TRINARY,
        "invariants": [
            "armature == rotor_inertia_kgm2 * gear**2（读错 inertia_basis 会差 10⁴ 倍）",
            "同一 subtype 内键集必须完全同构，缺失写 null",
            "派生量在读取时计算，不落库",
        ],
        "note": "口径规范由本站（中立、不卖零件）发布；把参数口径写进合同附件，验收才有约束力。",
    }
