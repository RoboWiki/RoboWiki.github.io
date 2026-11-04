---
title: 登录 / 注册
description: 邮箱注册登录、GitHub 登录与邮箱验证
layout: page
sidebar: false
outline: false
---

<AuthPanel />

::: tip 登录方式
- **邮箱账号**始终可用：注册、登录、邮箱验证与找回密码都在上面的面板里。
- **GitHub 登录**按钮只在服务端配置了 `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET`
  后出现；未配置时按钮禁用，不会发起无效请求。
- 开发环境（`EMAIL_MODE=log`）的验证/重置令牌打印在 API 日志里，不会出现在接口响应中。
:::
