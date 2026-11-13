# CI 分层

站点仓只有一条构建链，PR 门禁固定为 `pr-gate`：

```text
PR
 └─ build
     ├─ 拉数据仓锁定 release
     ├─ 从数据仓拉 rating/review Issue 并聚合
     ├─ pipeline build（目录、评分快照、页面数据）
     └─ Astro build
 └─ pr-gate（汇总，分支保护只认这个检查）
```

- 没有 backend、Taro app、Docker 或数据库测试层。
- 数据格式校验仍由数据仓的 `Data gate` 负责；站点仓只验证“拿到锁定数据后能不能构建”。
- 分支保护：PR、1 个批准、解决对话、必须通过 `pr-gate`，禁止强推/删除，管理员保留应急绕过。
- 数据仓主分支保护：PR、1 个批准、解决对话、必须通过 `validate`，禁止强推/删除。
