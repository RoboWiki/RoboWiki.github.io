# 缺图清单

以 `data-v2026.11.2` 为准：**目录内只有 1 件没有产品图**（乐动 LD14）；
另有 2 条 C 级电池线索没有图，它们不投影进站点目录。

> 补图在核心仓做：图片放核心仓 `inbox/`，在核心仓根目录跑
> `python tools/import_from_inbox.py`，产物写入 `assets/parts/`，
> 并在条目的 `specs.image_source` 写清出处。不要在本仓提交图片副本。

## 当前缺图

| 范围 | 零件 id | 型号 | 原因 |
|---|---|---|---|
| 目录内 | `sens-ldrobot-ld14` | LD14 | 官方产品图待核；LD19 已用 Wayback 快照补图 |
| C 级线索（不入目录） | `feifei-6s-222v-xt60` | 6S 22.2V XT60 | 采购清单线索，无官方图 |
| C 级线索（不入目录） | `fulaixiang-6s4p-21700-20000` | 6S4P 21700 20000mAh | 淘宝截图线索，无官方图 |

## 补图流程

```bash
# 在核心仓根目录
# 1) 把图片放进 inbox/（文件名用零件 id 或型号）
python tools/import_from_inbox.py     # 认领 + 登记 image_source
python tools/normalize_images.py      # 统一白底/尺寸
python tools/apply_images.py          # 合并进 data/catalog
python -m pipeline validate
python tools/export_data.py --out dist --tag data-vYYYY.MM.N
```

发布后本仓更新 `data.lock.json`，再 `pipeline build`。

## 口径

- 不拿同系列图、整机宣传图或商城图冒充某型号产品图。
- 没有官方图就保持 `image_url: null`，页面用材料色块/示意图，不放假图。
- 图片版权归原方；`image_source` 必填，权利人要求下架先撤图再讨论。
