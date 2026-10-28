"""已废弃工具的共用拦截器。

背景：2026-10-28 的架构收敛把 data/catalog/<品类>/<厂商>.json 定为**唯一事实源**，
旧的扁平文件（motors.json / controllers_*.json / sensors.json / focus.json）
已出库归档。但 tools/ 里还留着一批按旧结构写文件的脚本 ——
它们现在跑起来「成功」但**写的文件没人读**，正是这次收敛要消灭的
「改了没生效」困惑。

用法（放在脚本最前面，导入任何项目模块之前）：

    from _deprecated import require_legacy_ok
    require_legacy_ok(__file__)

判定：默认直接退出；设置 ROBOWIKI_ALLOW_LEGACY=1 才放行（考古时用）。
"""
from __future__ import annotations

import os
import pathlib
import sys

MESSAGE = """\
这个脚本按旧的扁平结构（data/motors.json、controllers_*.json、sensors.json、
focus.json）写文件，而这些文件已经在 2026-10-28 出库归档 ——
现在**没有任何读取方**会看到它写出的结果。

要改数据，请直接编辑唯一事实源：
    data/catalog/<品类>/<厂商>.json
然后用闸门验证：
    python -m pipeline validate

确实要考古运行旧脚本（例如重建历史归档），设置环境变量放行：
    set ROBOWIKI_ALLOW_LEGACY=1
"""


def require_legacy_ok(script_file: str) -> None:
    if os.environ.get("ROBOWIKI_ALLOW_LEGACY") == "1":
        print(f"[legacy] ROBOWIKI_ALLOW_LEGACY=1，放行 {pathlib.Path(script_file).name}",
              file=sys.stderr)
        return
    name = pathlib.Path(script_file).name
    print(f"\n[已废弃] {name}\n", file=sys.stderr)
    print(MESSAGE, file=sys.stderr)
    raise SystemExit(2)
