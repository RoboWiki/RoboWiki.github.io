# CI 分层：PR 门禁按路径分流

> 落地 `docs/ADR-002-monorepo-vs-split.md` 整改清单里的「CI 按路径分层，纯 data PR 不跑前端构建」。
> 实现文件：`.github/workflows/pr-gate.yml`。稳定入口：汇总 job **`pr-gate`**。

## 一句话

**先算这次 PR 动了哪几层，再只跑该层该跑的检查。**
纯数据 PR（只改 `data/**`、`schema/**`）不再装 node、不再跑 pytest 全量；改 `pipeline/`、改站点、改后端各自只跑自己那条线；**任何一层算不出来，就退回全量**。

## 为什么值得做（时间账）

一次数据 PR 的 wall clock 主要由三块构成，而它们跟数据改动是否可能出错毫无关系：

| 环节 | 改数据时是否必要 | 量级 |
| --- | --- | --- |
| `pip install pydantic` + `python -m pipeline validate` | **必要**（数据闸门本体） | 十几秒 |
| `pip install pytest httpx` + `pip install -r backend/requirements.txt` + `python -m pytest` | 不必要（要测的是构建链与 API 行为） | 1~2 分钟 |
| `pip install` + `npm ci` + `vitepress build` | 不必要（数据改动不需要 node） | 1 分钟上下 |

分层后，数据 PR 只剩：

| 环节 | 内容 | 量级 |
| --- | --- | --- |
| `validate` | `python -m pipeline validate` + schema 校验 | 十几秒 |
| `test_data` | `tests/test_data_governance.py`（5 条）+ `tests/test_taxonomy.py`（7 条） | **本地实测 2.1 秒 / 12 条** |
| `build` | 只跑 `python -m pipeline build`（生成器），不跑 VitePress | 十几秒 |

> 量级说明：`test_data` 的 2.1 秒是本地实测（`python -m pytest tests/test_data_governance.py tests/test_taxonomy.py`）；其余是 job 组成推算。作为对照，`tests/` 全部 = 53 条用例，`backend/tests/` 另有 80 个 `test_` 函数，`python -m pytest` 会把这两条线一起跑。

## 判据表（路径 → 命中层 → 跑什么）

判据只有一份真相：`pr-gate.yml` 里 `changes` job 的 `LAYERS` 列表（`id: classify` 步骤，写作时第 77–87 行）。
**前缀匹配，`startswith`，不认 glob、不认扩展名。**

| 改动路径前缀 | 命中层 flag | 会跑哪些 job |
| --- | --- | --- |
| `data/**`（含 `data/catalog/*/*.json`、`data/taxonomy.json`…） | `data` | `validate` → `test_data` → `build`（只有生成器） |
| `schema/**`（json schema、`semantics.json`） | `data` | 同上（schema 是数据契约，改它等同于改数据） |
| `pipeline/**` | `pipeline` | `validate` → `test`（全量 pytest，含 `backend/tests`）→ `build`（生成器 + VitePress） |
| `tools/**` | `pipeline` | 同上 |
| `tests/**` | `pipeline` | 同上 |
| `wiki/**` | `site` | `validate` → `build`（生成器 + VitePress） |
| `frontend/**` | `site` | 同上（目前仓库里还没有这个目录，先按站点对待） |
| `console/**` | `console` | `validate` → `console`（`tsc -b && vite build`） |
| `backend/**` | `backend` | `validate` → `backend`（`import` 冒烟 + `pytest backend/tests`） |
| **上表之外的一切** | `full` | **全部 job** |

「上表之外」明确包含：`docs/**`、`.github/**`、根目录的 `Makefile` / `pyproject.toml` / `README.md` / `PULL_REQUEST_TEMPLATE.md`、以及**任何新加的目录**。
这一档是有意为之：宁可慢，不可漏。想给 `docs/**` 提速的做法见文末「已知遗留」。

## 走一遍：只改 `data/catalog/camera/depth-camera.json`

| job | 结果 | 原因 |
| --- | --- | --- |
| `changes` | 跑 | 算出 `data=true`，其余 false，`full=false` |
| `validate` | 跑 | 不看分层，永远跑 |
| `test_data` | 跑 | `data` 命中 → 12 条数据用例 |
| `test` | **跳过** | `pipeline=false`（pytest 全量不跑） |
| `backend` | **跳过** | `backend=false` |
| `build` | 跑（只生成器） | `DO_SITE=false` → 不装 node、不跑 VitePress |
| `console` | **跳过** | `console=false` |
| `gate` | 跑 | 7 个 job 全 success/skipped → **通过** |

对照改动前的同一次 PR：`测试` 会装 `backend/requirements.txt` 跑 53+80 条用例，`站点构建` 会 `npm ci` 再 `vitepress build`。现在这两块整体消失。

## 每个 job 的明细

| job id | 显示名 | 什么时候跑（`if`） | 具体做什么 | 依赖 |
| --- | --- | --- | --- | --- |
| `changes` | 变更分层 | 总是（无 `if`） | checkout(`fetch-depth: 0`) → `git diff --name-only --no-renames BASE...HEAD` → 打 flag | 无 |
| `validate` | 数据闸门 | **总是**（不看分层） | `python -m pipeline validate` + 用 `schema/part.schema.json` 逐条 `iter_errors` | python 3.12, pydantic, jsonschema |
| `test_data` | 数据测试 | `full` ‖ `data` | `pytest tests/test_data_governance.py tests/test_taxonomy.py` | python 3.12, pydantic, pytest |
| `test` | 测试 | `full` ‖ `pipeline` | `python -m pytest`（`testpaths = tests, backend/tests`） | python 3.12, pydantic, pytest, httpx, `backend/requirements.txt` |
| `backend` | 后端冒烟 | `full` ‖ `backend` | `cd backend && python -c "import app, app.main"` → `pytest backend/tests` | python 3.12, `backend/requirements.txt` |
| `build` | 站点构建 | `full` ‖ `data` ‖ `pipeline` ‖ `site` | 恒跑 `python -m pipeline build`；`DO_SITE=true` 时再 `npm ci` + `vitepress build docs` | python 3.12, pydantic, node 20（仅 DO_SITE） |
| `console` | 选型台构建 | `full` ‖ `console` | `cd console && npm ci && npm run build` | node 20 |
| `gate` | **`pr-gate`** | `always()` | 汇总，见下 | 无 |

两处刻意的不对称，都是为省时间且不丢覆盖：

1. **`validate` 不跟分层。** 它是唯一的必过关，成本只有十几秒；让它无条件跑，等于给「分层算错」留了一道自动兜底。
2. **`backend` 不被 `pipeline` 触发。** `python -m pytest` 的 `testpaths` 已经含 `backend/tests`，改 pipeline 时 `test` 那条线会把后端测试一起跑，不必重复。

## 汇总 job `pr-gate` 的判定规则（fail-closed）

```
skipped            → 通过（这一层没被触发）
success            → 通过
failure / cancelled → 不通过
分层输出为空串      → 不通过（否则 if 全为 false → 全部 skipped → 假通过）
```

最后一条是这套设计里最容易踩的坑：如果 `changes` 没跑起来或表达式拼错，所有下游 job 的 `if` 都会算出 false 从而全部 skipped，而「全部 skipped」在只看结果的判定里和「全部通过」没有区别。
所以汇总脚本里显式检查 6 个 flag 必须是 `true`/`false` 字符串（`pr-gate.yml` 第 360–369 行），空值直接判红。

## 兜底三连（为什么「宁可慢，不可漏」）

`changes` job 里三处会直接置 `full=true`（即全部 job 都跑）：

1. **非 `pull_request` 事件** —— `workflow_dispatch` 手动触发时没有 base 可比。
2. **取不到 base / `git diff` 非零退出 / diff 为空** —— checkout 已经 `fetch-depth: 0`，另有一次 `git fetch origin <base>` 补偿；两者都失败就是算不出来。
3. **有任何一条路径没归到层** —— `.github/**`、`docs/**`、根目录文件、新目录都会落进 `unmapped`，一条就够触发全量。

## 新增目录时要同步改哪里

按顺序改，一处都不能漏（漏第 1 步 = 新目录的 PR 静默跑全量；漏第 4/5/6 步 = 新 job 永远不进汇总）：

1. **判据**：`.github/workflows/pr-gate.yml` → `jobs.changes.steps` 中 `id: classify` 步骤里的 `LAYERS` 列表（第 77–87 行）。加一行
   `("newdir/", ["层名"]),`，层名必须是 `data` / `pipeline` / `site` / `console` / `backend` 之一。
2. **（仅当要开新层）flag 名**：同一段脚本的 `KEYS` 列表（第 88 行）加入新层名。
3. **（仅当要开新层）输出**：`jobs.changes.outputs`（第 51–58 行）加一行
   `newdir: ${{ steps.classify.outputs.newdir }}`。
4. **（仅当要开新层）新 job**：照现有 job 抄，`needs: [changes]`，`if:` 写成
   `needs.changes.outputs.full == 'true' || needs.changes.outputs.newdir == 'true'`。
5. **（仅当要开新层）汇总接入**，三处都要：
   - `jobs.gate.needs`（第 334 行）加入新 job id；
   - `jobs.gate.steps[0].env`（第 339–353 行）加 `R_NEWDIR: ${{ needs.newdir.result }}`；
   - `jobs.gate.steps[0].run` 的 heredoc 名单（第 382–390 行）加一行 `newdir|$R_NEWDIR`。
6. **（仅当新目录也要部署）** `.github/workflows/pages.yml` 的 `on.push.paths`（第 12–16 行）加该目录。
7. **本文档**：上面的判据表 + job 明细表各加一行。

改完自检：

```bash
# 1) 结构/表达式/图（最有用，能查出 needs 拼错、outputs 名拼错、表达式语法错）
actionlint .github/workflows/*.yml

# 2) 只跑 5 秒的分层逻辑（不需要 GH 环境）
python - <<'PY'
import pathlib, re, yaml
wf = yaml.safe_load(pathlib.Path('.github/workflows/pr-gate.yml').read_text(encoding='utf-8'))
step = [s for s in wf['jobs']['changes']['steps'] if s.get('id') == 'classify'][0]
src = re.search(r"python3 - <<'PY'\n(.*?)\n\s*PY\s*$", step['run'], re.S).group(1)
pathlib.Path('/tmp/classify.py').write_text(src, encoding='utf-8')
PY
EVENT_NAME=pull_request BASE_SHA=$(git rev-parse HEAD) GITHUB_OUTPUT=/dev/stdout python3 /tmp/classify.py
```

> `pyyaml` 会把顶层的 `on:` 解析成布尔 `True`（YAML 1.1 语义），GitHub 用的是 YAML 1.2，`on:` 就是字符串。本地解析看到 `True` 属于工具差异，不是文件写错；用 `actionlint` 复核即可。

## 已知遗留（本次没动，避免扩大改动面）

1. **`concurrency.group: pr-check` 是全局的**，两个 PR 同时跑会互相 `cancel-in-progress`，把对方的门禁取消掉。更合理的是 `pr-check-${{ github.ref }}`，但那是行为变更，值得单独一次改动 + 一次实测。
2. **`docs/**` 走全量**：文档 PR 目前也会跑全部 job。要提速就把 `("docs/", ["docs"])` 加进 `LAYERS` 并给各 job 加条件（多数 job 应判 false），按上面第 2–5 步操作。
3. **`pages.yml` 未改**：部署只看 push 到 main 的路径，与 PR 分层无关，没有同步修改的必要。
4. **VitePress 未对数据 PR 设卡**：纯数据 PR 只跑生成器。死链风险由三道提前拦：`test_data_governance`（注册表里的 id 消失 / 未登记 id）、`test_taxonomy`（精选清单含不存在的部件、品类与 schema enum 不一致）、生成器本身（`build_site` 遇到缺字段直接抛）。万一漏网，`pages.yml` 在 main 上会红。
5. **本地跑不了 `backend` 那条线**：本机 Python 3.9 的 `cryptography` DLL 坏了，`pytest backend/tests` 收集即报错。这不影响 CI（ubuntu + python 3.12 全新安装），只是本地复现要用干净环境。
6. **`test_taxonomy.py` 里有一条比对「已提交产物」的用例**（`test_catalog_json_carries_categories` 读 `wiki/docs/public/catalog.json`）：所以改 `data/taxonomy.json` 的 PR 必须同时重新生成产物，否则 `test_data` 会红。这是原有语义，不是分层引入的；实际上这类 PR 会同时命中 `wiki/**` → `site` 层，VitePress 也会跑。
