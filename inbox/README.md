# inbox —— 丢图的地方

把要补的产品图丢进这个目录，文件名用**零件 id** 或**型号**都行：

```
inbox/
  dji-rm-board-a.png          ← 用 id
  DM-J4340-2EC V1.1.jpg       ← 用型号（大小写、空格、符号都不敏感）
  IM6014.jpg
```

然后跑：

```bash
python tools/import_from_inbox.py     # 认领 + 登记
python tools/normalize_images.py      # 统一白底、裁掉多余留白
python tools/apply_images.py          # 合并进 data/catalog
python -m pipeline all                # 重新生成站点
```

四条命令可以一次性交给我，你不用自己跑。

## 图片要求

- **白底、产品本体**，不要整机宣传图、不要二维码、不要 logo
- 长边 ≥ 600 px（卡片显示高度约 96–112 px，太小会糊）
- jpg / png / webp 都行，之后会统一转成白底 jpg

## 这个目录会进 git 吗

不会。`inbox/` 是暂存区，认领后图片会进 `frontend/public/parts/` 并纳入版本管理。
暂存区留在本地，避免把「还没确认的图」也提交进去。

## 已经认领过的

认领后文件名会被规范成 `<零件id>.jpg`，落在 `frontend/public/parts/`。
映射关系写在 `data/part_images.json`，谁都能查「这张图对应哪个零件」。
