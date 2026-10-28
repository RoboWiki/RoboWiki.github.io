"""pipeline —— 确定性的内容构建链。

设计原则（决定了这个项目能不能被别人 fork 后自建）：

    1. **纯函数式**：给定 data/ 的输入，产出固定。同样的输入跑两次，
       产物字节级一致 —— 这样 PR 里的产物 diff 才是可信的。
    2. **单一入口**：只有 `python -m pipeline build` 一条路能产生产物。
       一次性迁移脚本全部在 tools/，不参与构建。
    3. **只用产物做接口**：站点与 API 都消费 emit 出来的 JSON，
       谁也不直接读 data/catalog 的原始文件 —— 读侧理解不可能漂移。

模块：
    load      读 data/，返回统一的零件 / 优惠结构
    validate  数据闸门（口径、量程、键集、跨行不变量）
    emit_site 生成 VitePress 内容（型号页、首页、口径、侧边栏、catalog.json）
    ingest_*  把 GitHub issue 的评分 / 实测聚合成快照
"""
