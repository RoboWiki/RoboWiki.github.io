# 数据版本化（DATA-VERSIONING）

`data/` 是这个仓库的唯一事实源，但它现在**只跟着站点发布节奏走**：想引用「2026 年 10 月
那版零件目录」的人，只能 clone main 然后赌那天之后没人再改。这份文档说的是怎么把
`data/` + `schema/` 变成可 pin 的发布物，以及 pin 的时候要记什么。

实现只有两处：

| 位置 | 作用 |
|---|---|
| [`tools/export_data.py`](../tools/export_data.py) | 打包 + 生成 MANIFEST + 自检，**唯一实现** |
| [`.github/workflows/data-release.yml`](../.github/workflows/data-release.yml) | 校验数据 → 调上面的脚本 → 发 GitHub Release |

本地与 CI 跑的是同一个脚本。workflow 里不再有内联的打包/清单逻辑，所以不存在
「CI 的 MANIFEST 和本地不一样」这种漂移。

---

## 1. 为什么要给数据发版本

三条具体理由，都能对上仓库里已经存在的东西：

1. **站点版本 ≠ 数据口径版本。** 站点每次提交都会重新构建，但 `schema/semantics.json`
   的 `version` 是口径契约的版本（当前 `1.0.0`）。用数据做选型或复现的人，需要钉住的是
   口径，不是某次前端改版。
2. **下游需要可引用的快照。** 论文复现、别人 fork 出去的选型脚本、MCP/API 的回归基线，
   都需要一句「我用的是 `data-v2026.11.01`，parts=242」而不是「我用的是 main」。
3. **拆仓的信号先于动作。** [ADR-002](ADR-002-monorepo-vs-split.md) 的裁定是「不物理拆仓，
   但让 `data/` 具备随时能干净拆出去的能力」。发布物是这条裁定的兑现形式：真要拆的那天，
   下游已经按版本引用了一年了，切换只是换下载地址。

反过来说，**clone main 不是版本引用**：clone 之后仓库还会前进，你也拿不到「当时是什么样」。

---

## 2. 发布物长什么样

一次导出产出三个文件（都在 `--out` 目录下）：

| 文件 | 内容 | 谁读 |
|---|---|---|
| `robowiki-data-<tag-去 data- 前缀>.tar.gz` | 只含 `data/` 与 `schema/` 两个前缀的文件 | 下游解包 |
| `MANIFEST.json` | 口径指纹：条目数 + semantics 版本 + 生成时间 | 下游人读 + 脚本断言 |
| `SHA256SUMS.txt` | `<sha256>  <文件名>`（两个空格，`sha256sum -c` 格式），覆盖上面两个文件 | 解包前校验 |

tag 与附件名的映射只有一条规则：**附件名 = `robowiki-data-` + tag 去掉 `data-` 前缀**。

| 发布 tag | 附件名 |
|---|---|
| `data-2026.10.30` | `robowiki-data-2026.10.30.tar.gz` |
| `data-v2026.11.01` | `robowiki-data-v2026.11.01.tar.gz` |

### MANIFEST.json 的七个字段

| 字段 | 含义 | 取自 |
|---|---|---|
| `generated_at` | 导出时刻，UTC，`%Y-%m-%dT%H:%M:%SZ` | 导出时取系统时间 |
| `parts` | 零件条目数 | `data/catalog/*/*.json` 各数组长度求和 |
| `robots` | 整机条目数 | `data/robots/*.json` 各数组长度求和 |
| `software` | 软件条目数 | `data/software.json` 的 `items` 长度 |
| `ids` | 永久 ID 数 | `data/_id_registry.json` 的 `ids` 长度 |
| `semantics_version` | 口径版本 | `schema/semantics.json` 的 `version` |
| `note` | 一句话提示（记录本清单的理由） | 脚本常量 |

示例（2026-10-30 的一次真实导出：140 个文件、154,330 字节）：

```json
{"generated_at": "2026-10-30T16:23:42Z", "parts": 242, "robots": 21,
 "software": 22, "ids": 439, "semantics_version": "1.0.0",
 "note": "按版本引用数据时请一并记录本清单，便于回溯口径。"}
```

你自己的 MANIFEST 数字一定和上面不同：`parts`/`robots`/`software`/`ids` 是随数据增长的量，
`ids` 涨得最快（每次新增条目都会登记进 `data/_id_registry.json`）。**别把数字写死进脚本当断言**，
要么断言 `semantics_version`，要么像 §4 那样用 MANIFEST 里的值去比。

这些数字与站点产物是同源的：`wiki/docs/public/catalog.json` 的 `count` 与
`meta.record_count` 等于同一时刻的 `parts`（同一次 `pipeline build` 算出来的）。

### 归档里有什么、没有什么

- **有**：`data/` 全部已跟踪文件（catalog 当前 88 个、robots 12 个、offers 4 个、`_id_registry.json`、
  `taxonomy.json`…）、`schema/` 全部已跟踪文件（当前 10 个）。数字会随数据增长，**判断标准是
  「git 跟踪了什么」，不是这几个具体数**。
- **没有**：代码（`pipeline/`）、站点产物（`wiki/docs/public/*.json`）、图片
  （`console/public/parts/`）、厂商原始 PDF。
- 即使本地存在，也**不会**被打进去的东西（都在 `.gitignore` 里，打进去会让发布物多一个数量级）：
  `data/raw/`、`data/_backup/`、`data/_inventory/*.jsonl`、`data/motors*.json`、
  `data/focus.json`、`__pycache__/`。

---

## 3. 怎么发

### 3.1 本地先跑一遍（推荐每次都跑）

```bash
python -m pipeline validate                     # 数据闸门，红了就别发
python tools/export_data.py --out dist          # tag 默认 data-<UTC 日期>
python tools/export_data.py --out dist --tag data-v2026.11.01
```

- `--out dist` 是默认值；试跑建议 `--out .tmp-data-export`，跑完直接删目录。
- `dist/` 与 `.tmp-data-export/` 已在 `.gitignore` 里，**tar.gz 不进仓库历史**。
- 脚本最后会自检并把结果打出来，失败时退出码 1：

```
[export] 取样    git 已跟踪（与 CI checkout 一致） → 140 个文件
[export] 归档    dist/robowiki-data-2026.10.30.tar.gz  (150.71 KB, 140 个条目)
[export] 自检通过：归档只含 data/ 与 schema/；MANIFEST 五项计数与归档内容一致
```

自检做四件事，任何一条不满足就退出码 1：归档里只出现 `data/`、`schema/` 前缀；
条目集合与取样集合完全一致；把归档内容重新读出来重算五项计数与 MANIFEST 比对；
重算 SHA256SUMS 里的每个校验值。

**取样范围**：默认只打 `git` 已跟踪的文件——CI 上 `actions/checkout` 出来的正是这份集合，
所以本地与 CI 的内容一致。刚新建还没 `git add` 的 JSON 会被跳过并打印告警；确需包含加
`--include-untracked`。

**可复现性**：条目按路径排序，`mtime`/`uid`/`gid` 归零，gzip 头不写文件名与时间戳。
同一台机器、同一份数据上重复导出，tar.gz 的 sha256 逐字节相同（实测连续两次一致）；
`MANIFEST.json` 里的 `generated_at` 是真实时间，所以 MANIFEST 自己的 sha256 每次都变——
这是预期，不是 bug。数据一旦变化，tar 的 sha256 必然变化，这正是它有用之处。

**但跨平台不要指望逐字节一致**：本仓 `core.autocrlf=true`，工作区里几个 `data/*.json`
是 CRLF，而 CI（Linux checkout）是 LF，所以同一提交在 Windows 上导出的 tar.gz 与 CI 的
sha256 不同——**MANIFEST 的计数一致、语义一致，只有换行字节不同**。要比字节就在 Linux
（或 `core.autocrlf=false` 的干净工作区）里导出；要比「内容有没有变」，比 MANIFEST 的四个计数。

### 3.2 手动触发 workflow

GitHub → Actions → **Data release** → *Run workflow*。

- `tag` 留空：用 `data-<UTC 日期>`（注意是 UTC，北京时间早上 8 点前会落到前一天）。
- `tag` 填值：就用你填的，同时会建/更新同名 Release。

### 3.3 打 tag（发布物的名字能对上 git 历史）

```bash
git tag data-v2026.11.01
git push origin data-v2026.11.01
```

`on.push.tags: data-v*` 是触发器；workflow 会自动把 tag 名当作发布 label
（`GITHUB_REF_NAME`）——**2026-10-31 之前这里有个坑**：tag 触发时
`github.event.inputs.tag` 是空的，Release 会被挂到日期名上而不是你的 tag 上，现已修正。

### 3.4 发布前的四条自查

```bash
git status --porcelain data schema          # 必须为空，否则本地导出 ≠ CI 导出
python -m pipeline validate                 # 数据闸门
git diff <上一个 data-v*> -- schema/semantics.json   # 口径动过就必须升 version，见 §5
cat dist/MANIFEST.json                      # 和上一期的 parts/robots/software/ids 对一下增减
```

---

## 4. 下游怎么用

以 `data-v2026.11.01` 为例（仓库地址见 `pyproject.toml` 的 `[project.urls]`）：

```bash
TAG=data-v2026.11.01
BASE=https://github.com/RoboWiki/RoboWiki.github.io/releases/download/$TAG
ASSET=robowiki-data-v2026.11.01.tar.gz

curl -fLO "$BASE/$ASSET"
curl -fLO "$BASE/SHA256SUMS.txt"
curl -fLO "$BASE/MANIFEST.json"

sha256sum -c SHA256SUMS.txt        # 两个 OK 才算拿到完整快照
mkdir -p vendor/robowiki
tar -xzf "$ASSET" -C vendor/robowiki
```

`curl` 必须带 `-L`/`-fLO`：Release 附件是 302 到 `objects.githubusercontent.com`。

Windows PowerShell 等价：

```powershell
$TAG="data-v2026.11.01"
$BASE="https://github.com/RoboWiki/RoboWiki.github.io/releases/download/$TAG"
Invoke-WebRequest "$BASE/robowiki-data-v2026.11.01.tar.gz" -OutFile "robowiki-data-v2026.11.01.tar.gz"
(Get-FileHash .\robowiki-data-v2026.11.01.tar.gz -Algorithm SHA256).Hash.ToLower()
# 与 SHA256SUMS.txt 里那一行逐字符比对（大小写不敏感），再 tar -xzf 解包
```

### 用的时候记哪三样

引用这份数据的地方（论文、脚本、README、issue）请写全：

```
数据集：robowiki-data-v2026.11.01（tag data-v2026.11.01）
口径：semantics_version 1.0.0，parts=242 / robots=21 / software=22 / ids=439
导出时间：2026-10-30T16:23:42Z
```

前两行来自 MANIFEST，第三行也来自 MANIFEST 的 `generated_at`。**只写 tag 不写
semantics_version 是不够的**：tag 一样但口径变了的情况不该发生，真发生了，MANIFEST 是唯一
能证明你当时读的是哪套口径的东西。

### 在代码里断言（防止数据集被换掉而不自知）

```python
import json
from pathlib import Path

man = json.loads(Path("MANIFEST.json").read_text(encoding="utf-8"))
assert man["semantics_version"] == "1.0.0", "口径版本变了，对比逻辑要重跑"

root = Path("vendor/robowiki")
parts = sum(len(json.loads(p.read_text(encoding="utf-8")))
            for p in (root / "data/catalog").glob("*/*.json"))
assert parts == man["parts"], f"快照里的条目数对不上：{parts} != {man['parts']}"
```

---

## 5. 什么时候要升 semantics 的 version

`schema/semantics.json` 的 `version` 是**口径契约**的版本，只管「字段怎么读」，
**不管「有多少条数据」**。条目增减由 MANIFEST 的 `parts`/`robots`/`software`/`ids` 承担指纹作用。
两个版本号各管各的，别混。

**规则本身以 [`schema/semantics.README.md`](../schema/semantics.README.md) §3「version 升级规则」为准**
（那份文档是 `semantics.json` 的 owner 说明，跟代码一起改）。这里只说发布物这一侧：
为什么要升、升了之后下游会怎样、Release 里要不要解释。

| 改动 | 要升 version | 本期发布物要做的事 |
|---|---|---|
| 只改错别字、标点、`note` 文案，不动语义 | 要（patch） | 无。MANIFEST 记下新版本，下游无感 |
| 新增字段语义 / 新增红线 / 新增换算条目 | 要（minor） | Release 说明里列出新增字段名，下游可以按需接 |
| 改某字段的 `meaning` / `missing_means` / `higher_is_better` | 要（minor） | Release 说明写清「哪个字段、旧值→新值、哪些结论需要重算」 |
| 改 `enum` 取值：**新增**取值 | 要（minor） | 同上，注明多出的取值 |
| **删除**字段 / **改单位** / 改键名 / 改顶层结构 / 删除 enum 取值 | 要（major） | Release 说明必须写「旧 → 新 + 受影响的页面与接口」；按旧版写的解析代码会读错或读不到键 |
| 只增删数据条目（`parts`/`robots`/`software`/`ids` 变化） | **不要** | 由 MANIFEST 四个计数反映；semantics 版本保持不变 |

判据一句话：**下游拿旧解析代码读新数据会不会读错？会 → 必须 major 并在 Release 里解释；
只是读不到新东西 → minor；读法完全不变 → patch。** 这也是「为什么每次导出都要带 MANIFEST」的
原因：它把「这一期数据配哪一版口径」写死在发布物里，事后不用翻提交历史去猜。

升版本时**只改一个地方**：`schema/semantics.json` 的 `version`。两个消费者都读这个文件：

- 文档站：[`pipeline/build_site.py`](../pipeline/build_site.py) 直接读它生成
  `wiki/docs/semantics.md`（口径页 `/semantics`）；
- API：[`backend/app/api/routes/semantics.py`](../backend/app/api/routes/semantics.py) 从同一个文件读，
  被 `/api/semantics` 与 MCP 工具 `get_parameter_semantics` 复用。

改一处、两边同时生效，**不要在任何 markdown 里手写字段说明**（会变成第二份事实源）。
`catalog.json` 或 `MANIFEST.json` 里的 `semantics_version` 是从这个文件读出来的，workflow 不用改。

### 顺带说清另外两个版本号（容易被当成同一个）

| 版本号 | 在哪 | 什么时候动 |
|---|---|---|
| `semantics.version`（semver） | `schema/semantics.json` | 口径变了（上表） |
| `schema_version`（整数） | `pipeline/meta.py` 的 `SCHEMA_VERSION`，写进 `wiki/docs/public/catalog.json` 的 `meta` | **产物** JSON 的形状变了（键增删改名），前端按它决定怎么解析 |
| 包版本 | `pyproject.toml` 的 `version` | Python 包/API 的发布语义 |

`catalog.json` 的 `meta.schema_version` 当前是 `1`，和 `semantics_version: "1.0.0"` 不是一回事：
前者管「产物长什么样」，后者管「字段值怎么理解」。
