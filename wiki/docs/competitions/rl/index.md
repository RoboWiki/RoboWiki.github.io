---
title: 强化学习
---

# 强化学习

足式运动的策略越来越依赖学习：从 MDP 与策略梯度，到 PPO / SAC，再到域随机化与
Sim-to-Real。这一模块收**学习类方法**的材料；模型控制（MPC / WBC、状态估计）仍在
[电控](/competitions/ec)。

## 现有材料

<MaterialGrid :items="[
  {
    title: '达妙科技足式强化学习笔记',
    href: 'https://my.feishu.cn/wiki/Sn4iwqtREio1llkzJ6Vc9wIwnmf',
    meta: '飞书 · 05-09 更新',
    tags: ['足式 RL', 'Sim2Real'],
    what: '从 MDP、动态规划、蒙特卡洛、TD / Sarsa / Q-Learning 到策略梯度、PPO、SAC、DDPG / TD3，再到模仿学习、特权学习、域随机化、课程学习与 RMA 等 Sim2Real 方法。',
    when: '入门按章节顺序读；做足式 RL 时把「足式强化学习算法概览」和 Sim2Real 部分当索引。',
  },
]" />

::: tip 这份笔记怎么用
原文托管在飞书，作者会持续更新；本站只做入口与范围说明，不复制正文，
内容以飞书原文为准（查看可能需要飞书账号）。
:::

## 想供稿？

这一块最缺的是「训练配置 + 失败复盘」，不是又一篇算法介绍：

- 一份能复现的训练配置：环境、并行数、奖励项与权重、课程与域随机化范围
- 一次 Sim2Real 失败：仿真里正常、上机就摔，最后定位到哪个建模误差
- 一套评测口径：成功率、速度、能耗、恢复能力分别在什么条件下测

投稿入口：[投一篇强化学习实战](https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=article.yml&labels=article) 或看 [全部投稿方式](/submit)。
