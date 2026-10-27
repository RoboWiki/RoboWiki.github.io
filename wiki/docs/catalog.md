---
title: 部件库
layout: page
sidebar: false
outline: false
---

<script setup>
import PartExplorer from './.vitepress/components/PartExplorer.vue'
</script>

<div class="cat-page">
  <header class="cat-hero">
    <h1>部件库</h1>
    <p>
      每个部件一页：左边是<strong>官方参数</strong>（带来源等级与口径），
      右边是<strong>真实使用者的评分与评价</strong>。有优惠条件、有资料链接、能按任意列排序。
    </p>
  </header>
  <PartExplorer />
</div>

<style>
/* 这一页要铺满：卡片是网格，左右留着大片空白纯属浪费 */
.cat-page {
  max-width: 1560px;
  margin: 0 auto;
  padding: 1.4rem 1.5rem 4rem;
}
.cat-hero { margin-bottom: 1.1rem; }
.cat-hero h1 {
  font-size: 1.7rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  margin: 0 0 0.35rem;
  border: none;
  padding: 0;
  background: linear-gradient(135deg, var(--vp-c-text-1) 0%, var(--vp-c-brand-1) 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.cat-hero p {
  margin: 0;
  font-size: 0.84rem;
  color: var(--vp-c-text-3);
  line-height: 1.75;
  max-width: 60ch;
}
</style>
