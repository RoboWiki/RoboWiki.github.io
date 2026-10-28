"""一条命令跑完整构建。

    python -m pipeline validate       数据闸门（PR 与 CI 的必过关）
    python -m pipeline build          生成站点内容 + 静态产物（catalog.json 等）
    python -m pipeline all            validate + build（CI 默认）

为什么收成一个入口：
    重构前 scripts/ 下有 30 个脚本，其中 16 个都能写 data/catalog —— 谁最后跑
    谁说话，多人协作必出事故。现在只有 pipeline/ 能产出**构建产物**；
    data/catalog 里的人工内容只能被 PR 改（或明确的一次性工具）。

模块命名：
    validate        数据闸门（原 check_data）
    build_site      生成 VitePress 内容（原 build_wiki）
    ingest_ratings  评分 issue → 快照
    ingest_reviews  实测 issue → 快照

退出码：0 成功；1 有 ERROR（warning 不阻断，见 validate.py）
"""
from __future__ import annotations

import subprocess
import sys

STEPS = {
    "validate": ["validate"],
    "build": ["build_site"],
    "all": ["validate", "build_site"],
}


def _run(module: str) -> int:
    print(f"\n=== {module} ===", flush=True)
    return subprocess.call([sys.executable, "-m", f"pipeline.{module}"])


def main() -> int:
    args = sys.argv[1:] or ["all"]
    if args[0] in ("-h", "--help", "help"):
        print(__doc__)
        print("可用步骤：" + " / ".join(STEPS))
        return 0

    step = args[0]
    if step not in STEPS:
        print(f"未知步骤 {step!r}，可用：{', '.join(STEPS)}")
        return 2

    for name in STEPS[step]:
        rc = _run(name)
        if rc != 0:
            print(f"\n{name} 失败（退出码 {rc}），后续步骤不再执行")
            return rc
    print("\n完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
