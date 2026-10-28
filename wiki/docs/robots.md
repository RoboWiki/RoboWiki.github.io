---
title: 机器人整机
layout: page
sidebar: false
outline: false
---

<div class="rb-page">
  <header class="rb-hero">
    <div class="rb-kicker">机器人整机</div>
    <h1>部件选完之后，看整机方案。</h1>
    <p>
      这一页与「机器人部件库」平行，不是它的子集。部件比<strong>参数</strong>，
      整机看<strong>方案</strong>：几自由度、带不带算力、电池续航、有没有开源 URDF。
    </p>
    <div class="rb-note">
      <b>进仿真</b> 按钮已留接口但<strong>暂未接入</strong>；每台的 URDF / 仓库链接列在详情页，
      可以自己下载。共 <b>15</b> 台。
    </div>
  </header>

  <RobotGrid />
</div>

<style>
.rb-page { max-width: 1120px; margin: 0 auto; padding: 1.6rem 1.5rem 0; }
.rb-kicker { font-size: .72rem; letter-spacing: .12em; text-transform: uppercase;
  color: var(--vp-c-brand-1); font-weight: 700; margin-bottom: .45rem; }
.rb-hero h1 { font-size: clamp(1.4rem,2.6vw,1.9rem); font-weight: 800; letter-spacing: -.02em;
  margin: 0 0 .6rem; border: none; padding: 0; color: var(--vp-c-text-1); }
.rb-hero p { margin: 0; font-size: .86rem; line-height: 1.85; color: var(--vp-c-text-2); max-width: 74ch; }
.rb-note { margin: 1rem 0 .4rem; padding: .65rem .9rem; border-radius: 8px;
  border-left: 3px solid var(--vp-c-brand-1); background: var(--vp-c-brand-soft);
  font-size: .79rem; line-height: 1.8; color: var(--vp-c-text-2); max-width: 74ch; }
</style>
