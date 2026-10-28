# tools —— 一次性迁移脚本（**会改数据，谨慎跑**）

这里的脚本不是构建链的一部分。它们做过一次历史迁移就归档了，
留着是为了「当时是怎么从 X 变成 Y 的」可复查、可重放。

## 跑之前先看这条

大部分脚本会**直接改 `data/catalog/**`**，而且是不可幂等的：

| 脚本 | 它会做什么 | 危险点 |
|---|---|---|
| `build_motors.py` | 从 PDF/Draft 采集执行器，写 `motors.json` | 会覆盖采集产物 |
| `build_catalog.py` | 生成上位机/传感器目录 | 会**删掉** focus 之外的品类文件 |
| `focus_data.py` | 按 focus.json 移走不收录的品类 | 移动，不是删除 |
| `restrict_to_focus.py` | 收窄到 focus 里的厂商 | 先备份再重建，可重跑 |
| `keep_only_a.py` | 只留 A 级 | 移出的行写进备份 jsonl |
| `import_archive.py` | 从商城归档导入零件 | 追加；有质量闸门 |
| `rename_vendors.py` | 厂商改名 | 会连带改 URL slug |
| `apply_pricing*.py` | 批量写价格与优惠 | 以脚本里的表为准，会覆盖手改 |

> **2026-10-28 起**：按旧扁平结构写文件的脚本（build_motors / build_catalog /
> split_data / focus_data / restrict_to_focus / build_zju_parts）已加拦截，
> 直接运行会打印废弃说明并退出（exit 2）。因为 data/catalog/ 已是唯一事实源，
> 它们写出的文件没有读取方。确需考古时设 ROBOWIKI_ALLOW_LEGACY=1 放行。

**协作时不要随手跑。** 如果只是加一个型号或改一个参数，
直接改 `data/catalog/` 下的 JSON 然后 `make validate` —— 那才是 PR 该做的事。

## 采集 / 图片

| 脚本 | 用途 |
|---|---|
| `fetch_images.py` | 从厂商产品页抓图（已处理非 ASCII URL） |
| `normalize_images.py` | 统一白底 + 裁掉多余留白 |
| `apply_images.py` | 把映射合并进 catalog（会跳过 `reject_wrong_images` 的剔除项） |
| `reject_wrong_images.py` | 剔除「整机图当电机图」这类错图 |
| `crop_from_screenshot.py` | 从截图按格裁产品图 |

## 归档导入链（三件套，按顺序）

```
inventory_archive.py   合并 products_p*.json → products.jsonl + 盘点报告
normalize_archive.py   英文规格 → 项目字段 + 中文 → normalized.jsonl + glossary.md
import_archive.py      按质量闸门写入 data/catalog/**
```

## 备份 / 回滚

| 脚本 | 用途 |
|---|---|
| `export_local_ratings.py` | 本地库评分导出（不与公开快照同名，避免覆盖） |
| `restore_backup.ps1` | 从 `data/_backup/` 恢复全量数据 |
| `dev.ps1` | 起本地热更（站点 + 控制台） |
