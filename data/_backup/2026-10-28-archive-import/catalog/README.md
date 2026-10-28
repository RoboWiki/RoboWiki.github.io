# data/catalog —— 零件数据（人工维护的唯一入口）

一家厂商一个文件：`data/catalog/<品类>/<厂商slug>.json`。

```
catalog/
  actuator/
    damiao.json            达妙 DM（31 个型号）
    dji-robomaster.json    DJI RoboMaster
    lingzu-robstride.json  灵足 RobStride
    unitree.json           Unitree
  controller_high/         上位机（暂未收录，见 data/focus.json）
  ...
```

## 加一个型号 = 改一个文件

在对应厂商文件末尾加一条，然后跑：

```bash
python pipeline/validate.py     # 数据闸门
python pipeline/build_site.py     # 重新生成站点
```

字段说明与硬规则见仓库根的 [CONTRIBUTING.md](../../CONTRIBUTING.md)。

## 为什么不按型号分文件

按型号分文件（一个型号一个 json）会让「加 10 个型号」变成 10 个新文件，
PR diff 很大、评审困难；按厂商分文件则是往数组里加 10 条，一个文件一个 diff。

## 不要手改的文件

| 文件 | 谁生成 |
|---|---|
| `data/motors.json` | `tools/build_motors.py`（采集产物，兼容用） |
| `data/part_images.json` / `part_images_fetched.json` | 抓图脚本 |
| `data/ratings_snapshot.json` | GitHub Actions（从 issue 聚合） |
| `data/focus.json` | `scripts/focus_data.py`（当前收录范围） |

## 价格与优惠

- **价格**写在零件的 `price_cny`，并在 `notes` 里注明来源与抓取日期
- **优惠**写在 `data/offers/<厂商slug>.json`，必须带 `detail`（获取条件）
- 只改价格用 `tools/apply_pricing.py` 的表，改动可复查
