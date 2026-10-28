---
title: AI 中转站
layout: page
sidebar: false
outline: false
---


<div class="ai">
  <header class="ai-hero">
    <div class="ai-kicker">AI 中转站</div>
    <h1>机器人要用的模型 API，从哪儿接。</h1>
    <p>
      这一页不是「哪个模型最强」，而是<strong>接入渠道怎么选</strong>：能不能国内直连、
      是不是 OpenAI 兼容、按量计费还是预充值。选型决定你写多少胶水代码。
    </p>
  </header>

  <table class="ai-table">
    <thead><tr><th>服务</th><th>类型</th><th>可用模型</th><th>协议</th><th>计费</th><th>备注</th></tr></thead>
    <tbody>
<tr>
  <td><a href="https://openrouter.ai/" target="_blank" rel="noopener">OpenRouter</a></td>
  <td>聚合网关</td>
  <td>多厂商文本 / 视觉模型</td>
  <td>OpenAI 兼容</td>
  <td>按 token 预充值</td>
  <td class="ai-note">一个 key 走多家模型，方便做「换个模型对比策略输出」。国内直连不稳定，机器人项目里多用于离线评测而不是在线推理。</td>
</tr>
<tr>
  <td><a href="https://siliconflow.cn/" target="_blank" rel="noopener">硅基流动 SiliconFlow</a></td>
  <td>国内网关</td>
  <td>开源文本 / 多模态 / 语音 / 向量</td>
  <td>OpenAI 兼容</td>
  <td>按 token 计费，有免费额度</td>
  <td class="ai-note">国内直连、延迟低，适合做机器人上的语音指令与视觉描述。开源模型为主，闭源旗舰模型要看当期支持列表。</td>
</tr>
<tr>
  <td><a href="https://www.volcengine.com/product/ark" target="_blank" rel="noopener">火山方舟（豆包）</a></td>
  <td>云厂商</td>
  <td>豆包系列 + 第三方模型</td>
  <td>自有 SDK / OpenAI 兼容</td>
  <td>按 token 计费，企业可走合同</td>
  <td class="ai-note">延迟与稳定性在国内属第一梯队，适合做产品化的语音交互。注意开通需要实名与模型服务激活。</td>
</tr>
<tr>
  <td><a href="https://bailian.console.aliyun.com/" target="_blank" rel="noopener">阿里云百炼（通义）</a></td>
  <td>云厂商</td>
  <td>通义千问系列 + 视觉 / 语音</td>
  <td>DashScope SDK / OpenAI 兼容</td>
  <td>按 token 计费</td>
  <td class="ai-note">多模态能力全，图像理解与语音识别都有；缺点是不同的模型走不同 SDK，接入前先确认是否 OpenAI 兼容。</td>
</tr>
<tr>
  <td><a href="https://open.bigmodel.cn/" target="_blank" rel="noopener">智谱 BigModel</a></td>
  <td>模型厂商</td>
  <td>GLM 系列 + 视觉</td>
  <td>OpenAI 兼容</td>
  <td>按 token 计费</td>
  <td class="ai-note">GLM-4V 一类的视觉模型可用性不错，适合做「看画面说下一步」。有免费档可以先试。</td>
</tr>
<tr>
  <td><a href="https://platform.moonshot.cn/" target="_blank" rel="noopener">Moonshot（Kimi）</a></td>
  <td>模型厂商</td>
  <td>长上下文文本</td>
  <td>OpenAI 兼容</td>
  <td>按 token 计费</td>
  <td class="ai-note">长上下文是强项，适合把整本手册 / 一整套日志丢进去问。机器人控制回路用不上它。</td>
</tr>
    </tbody>
  </table>

  <section class="ai-how">
    <h2>三条实用判断</h2>
    <ol>
      <li><b>先确认是不是 OpenAI 兼容</b>。兼容的话换服务商只改 base_url 与 key，否则要重写一层适配。</li>
      <li><b>机器人上的在线推理只用于「高层决策」</b> —— 语音指令、场景描述、任务拆解。
          关节力矩环绝不能过网络，最差也是本地小模型。</li>
      <li><b>延迟比单价更影响体验</b>。一句话指令多 800 ms，人会觉得机器人「傻」。</li>
    </ol>
  </section>

  <p class="ai-warn">
    价格与可用模型随时会变，<strong>本站不记录具体单价</strong>，也不做返佣推荐 ——
    以各家官网当期公示为准。这一页只列接入形态。
  </p>
</div>

<style>
.ai { max-width: 1040px; margin: 0 auto; padding: 1.8rem 1.5rem 4rem; }
.ai-kicker { font-size: 0.72rem; letter-spacing: 0.12em; text-transform: uppercase;
  color: var(--vp-c-brand-1); font-weight: 700; margin-bottom: 0.5rem; }
.ai-hero h1 { font-size: clamp(1.4rem, 2.6vw, 1.9rem); line-height: 1.3; font-weight: 800;
  letter-spacing: -0.02em; margin: 0 0 0.7rem; border: none; padding: 0; color: var(--vp-c-text-1); }
.ai-hero p { margin: 0; font-size: 0.86rem; line-height: 1.85; color: var(--vp-c-text-2); max-width: 68ch; }
.ai-table { width: 100%; border-collapse: collapse; font-size: 0.78rem; margin: 1.6rem 0; }
.ai-table th { text-align: left; font-weight: 600; color: var(--vp-c-text-3);
  border-bottom: 2px solid var(--vp-c-divider); padding: 0.45rem 0.6rem; white-space: nowrap; }
.ai-table td { border-bottom: 1px solid var(--vp-c-divider); padding: 0.5rem 0.6rem;
  vertical-align: top; color: var(--vp-c-text-2); }
.ai-table td a { color: var(--vp-c-brand-1); font-weight: 600; }
.ai-note { min-width: 220px; color: var(--vp-c-text-3) !important; line-height: 1.7; }
.ai-how h2 { font-size: 1rem; font-weight: 700; margin: 1.6rem 0 0.6rem;
  border: none; padding: 0; color: var(--vp-c-text-1); }
.ai-how ol { font-size: 0.82rem; line-height: 1.9; color: var(--vp-c-text-2); padding-left: 1.2rem; margin: 0; }
.ai-warn { font-size: 0.78rem; color: var(--vp-c-text-3); margin-top: 1.6rem; line-height: 1.8;
  border-left: 3px solid var(--vp-c-divider); padding-left: 0.8rem; }
</style>
