# ADR-009：互动端构建链迁到 VPT（Vite 8 + React 19）

日期：2026-11-09
状态：已完成

## 背景

`apps/app` 原先用 Taro CLI（webpack5）构建，`@tarojs/react@4.3.2` 依赖 `react-reconciler@0.29`（React 18 专用）并声明 `peer react: ^18`。仓库其他前端已是 React 19，两条 React 大版本并存；把小程序端升到 React 19 会让 Taro 渲染层在启动时报 `ReactCurrentBatchConfig` 未定义，`App()` 不注册，所有页面空白。

Taro 当前最新版（4.3.2，含 alpha/beta）仍是 React 18 reconciler，上游没有 React 19 支持。

## 决策

互动端改用 [vite-plugin-taro（VPT）](https://github.com/sep2/vite-plugin-taro) 0.8.7：

```text
Vite 8 + Rolldown        → 构建
React 19.3.1             → 渲染（react-reconciler 0.34）
Taro 4.3.2 runtime 补丁   → virtual:taro/api / virtual:taro/components
```

- 全仓 React 统一为 19.3.1；删除 React 18 锁定与 `react-dom` 兼容 shim。
- 业务代码只改导入：`@tarojs/taro` → `virtual:taro/api`，`@tarojs/components` → `virtual:taro/components`。
- 配置从 `app.config.ts` + 页面 `*.config.ts` + `config/index.ts` 合并进 `vite.config.ts` 的 `vpt({ pages, appJson, projectConfigJson })`。
- 产物目录改为 `dist/wx`，微信开发者工具直接导入该目录；H5 仍为 `dist/h5`。
- 样式保持 375 设计稿：小程序 `px→rpx`（ratio 2），H5 `px→vw`。

## 代价与边界

- VPT 是 Taro runtime 的补丁 fork，不是上游；升级路径跟随 VPT 版本，而不是 Taro CLI。
- 不再使用 Taro 的 webpack 配置、`@tarojs/cli`、`babel-preset-taro`；相关依赖已移除。
- 未使用 Skyline，仍为 webview 渲染与原生 tabBar，保持与迁移前一致。

## 验证门槛

- `pnpm --filter @robowiki/app typecheck`；
- `build:wx`、`build:h5` 均通过；
- 微信开发者工具：首页渲染与迁移前一致（375 稿尺寸），扫码确认页 E2E（scene → `wx.login` → 后端 confirmed → 签发 token）；
- H5 预览可加载部件数据（本地 API + CORS 白名单端口）。
