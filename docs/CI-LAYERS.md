# CI 分层：RoboWiki.github.io

本仓的 PR 门禁按路径分流，稳定入口是汇总 job **`pr-gate`**：

```text
changes（算层） → validate（数据闸门，必跑） → 按层跑 test / backend / web / app → pr-gate
```

数据与 schema 在`RoboWiki` 仓；本仓只保留 `data.lock.json` 与消费逻辑。
判据真相在 `.github/workflows/pr-gate.yml` 的 `LAYERS` 列表。

## 判据

| 改动路径 | 层 | 跑什么 |
|---|---|---|
| `pipeline/**`、`tools/**`、`tests/**` | `pipeline` | validate + pytest 全量 + 生成器 + Astro |
| `apps/web/**`、`packages/**` | `web` | validate + 生成器 + Astro 构建 |
| `apps/app/**` | `app` | Taro 类型检查 + H5 构建 |
| `backend/**` | `backend` | validate + import 冒烟 + 后端 pytest |
| `data/**`、`schema/**`（历史路径，现应改`RoboWiki` 仓） | `data` | validate + 数据测试 + 生成器 |
| `clients/**` | `clients` | validate + QQ 机器人/SDK 静态检查 |
| 其他（`deploy/**`、`docs/**`、根配置等） | `full` | 全部 |

`validate` 不看分层，永远跑；任何路径算不出来也退回全量。

## 各 job

| job | 内容 |
|---|---|
| `validate` | `python -m pipeline validate`；本仓校验器已同步材质库 |
| `test` | `python -m pytest`（站点 + 后端） |
| `backend` | `cd backend && python -c "import app.main"` + `pytest backend/tests` |
| `build` | `python -m pipeline build`；`web` 层再 `pnpm --filter @robowiki/web build` |
| `app` | `pnpm --filter @robowiki/app typecheck` + `build:h5` |
| `clients` | QQ 机器人/SDK 的静态检查 |
| `pr-gate` | 汇总；skipped 视为通过，空输出判红 |

## 本地等价

```bash
bash scripts/fetch-data-release.sh
python -m pipeline validate
python -m pytest
python -m pipeline build
pnpm install
pnpm --filter @robowiki/web build
APP_BASE=/app/ pnpm --filter @robowiki/app build:h5
```

## 注意

- 纯文档 PR 目前走全量；为省时间可后续加 `docs` 层，但不要牺牲 `validate`。
- 数据改动不要在本仓做：改`RoboWiki` 仓 → 发 release → 更新 `data.lock.json`。
- `backend` 与 `test` 有重叠；pipeline 层的改动跑 `test` 时已包含后端用例。
- 新增目录时同步更新 `pr-gate.yml` 的 `LAYERS`、汇总 job 和本表。
