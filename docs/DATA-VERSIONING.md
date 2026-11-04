# 数据版本化：站点如何消费核心仓 release

本仓不发布数据，只消费核心仓 `RoboWiki/RoboWiki` 的 `data-vYYYY.MM.N`。
事实源的版本规则、导出脚本与 MANIFEST 字段见核心仓
[docs/DATA-VERSIONING.md](https://github.com/RoboWiki/RoboWiki/blob/main/docs/DATA-VERSIONING.md)。

## 锁定文件

`data.lock.json` 是站点唯一的数据版本入口：

```json
{
  "data_version": "data-v2026.11.2",
  "source_repo": "RoboWiki/RoboWiki",
  "release_asset": "robowiki-data-v2026.11.2.tar.gz",
  "sha256": "<tar.gz 的 SHA-256>",
  "manifest_sha256": "<MANIFEST 的 SHA-256>",
  "schema_version": "1.1.0",
  "counts": {"parts": 329, "robots": 21, "software": 22,
             "materials": 27, "processes": 9, "ids": 622,
             "semantics_version": "1.1.0", "assets": 425}
}
```

`counts` 是给人和 CI 对照的，不作为运行时数据源；页面与 API 以实际解包内容为准。

## 构建流程

```bash
bash scripts/fetch-data-release.sh
# 等价于：gh release download -> sha256sum -c -> tar -xzf .data

ROBOWIKI_DATA_DIR="$PWD/.data/data" \
ROBOWIKI_SCHEMA_DIR="$PWD/.data/schema" \
ROBOWIKI_ASSETS_DIR="$PWD/.data/assets/parts" \
python -m pipeline build

cd wiki && npm run build
```

- `fetch-data-release.sh` 校验 tar.gz 与 MANIFEST 两个 sha256，并把 MANIFEST 计数与 `data.lock.counts` 对表；失败即停止。
- 构建脚本不访问 GitHub，不读 `raw.githubusercontent.com`；离线可用。
- Pages workflow 每次构建都重新下载锁定版本，不用仓库里的缓存。

## 升级数据版本

1. 核心仓合并数据 → 打 `data-v*` tag → `Data release` 成功；
2. 记录新 release 的 `SHA256SUMS.txt` 与 `MANIFEST.json`；
3. 更新本仓 `data.lock.json`（版本、附件名、两个 sha256、counts）；
4. 本地跑 `fetch-data-release.sh`、`pipeline build`、`pytest`；
5. 提 PR，CI 会重新下载新 release 并构建站点。

**不要**只改 `data_version` 不改 sha256；也不要直接复制核心仓 `data/` 到本仓。

## 页面与 API 的版本标识

- 静态页脚/分享 JSON 带 `data_version`；
- API 响应头：`X-RoboWiki-Data-Version: data-v2026.11.2`；
- `/api/v1/meta` 返回同一值；
- PWA 缓存按访问更新，数据版本变化不要求用户手动清缓存。

## 回滚

- 数据有问题：把 `data.lock.json` 指回上一版，重新构建；核心仓历史不动。
- 页面有问题：revert 站点 PR；数据版本不变。
- 不要移动或覆盖已发布的 `data-v*` tag。

## 口径与计数

- `parts` 是核心仓数据条数（含 C 级线索）；站点目录只投影 A/B，当前 **326 件入库**。
- `materials` / `processes` 是材质库条目数；页面 `/materials` 与 `public/materials.json` 同源。
- `semantics_version` 是字段口径；只增删条目不升它。
- 任何页面上的“共 N 件”必须来自构建产物，不手写。
