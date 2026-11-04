# 站点工具

数据采集、清洗、图片处理、ID 注册、数据发布工具已迁到`RoboWiki` 仓
[RoboWiki/RoboWiki](https://github.com/RoboWiki/RoboWiki) 的 `tools/`。

这里只保留不产出数据的站点专用脚本：

- `site/import_competition_pdf.py` / `site/import_competition_docs.py`：把竞赛文档导入 `wiki/docs/competitions/`
- `site/dev.ps1`：本地开发辅助

站点构建的数据来自`RoboWiki` 仓 release，先运行：

```bash
bash scripts/fetch-data-release.sh
```
