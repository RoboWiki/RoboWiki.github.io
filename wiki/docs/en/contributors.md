---
title: Contributors
layout: page
sidebar: false
outline: false
---

<div class="cd">
  <header class="cd-hero">
    <div class="cd-kicker">Contributors</div>
    <h1>These numbers did not fall from the sky.</h1>
    <p>Every spec was checked page by page against a vendor manual; every “—” is someone confirming it is genuinely not published. Names stay here because <strong>when a number is wrong, someone must be findable</strong>.</p>
  </header>

  <ContributorGrid lang="en" />

  <section class="cd-hand">
    <h2>Who did what</h2>
    <p class="cd-sub">Not generated from git log: machines can count commits, but they cannot say who verified which datasheet.</p>
    <div class="ct-grid"><div class="ct">
  <div class="ct-head"><b>zeitvex</b><span class="ct-role">创始维护者</span></div>
  <p>Built and maintains the whole engineering side: the data gate and validation, generated pages, and the parts/robots/software/suppliers/materials catalogues; verified A-tier specs for DAMIAO, RobStride, DJI, Unitree and others (torque normalised to the output side, missing values as null), and turned traceability into machine-checked rules. Scaled the catalogue to 14 categories, 326 catalogued parts (329 records, 3 C-tier leads excluded), 114 A-tier parts, 27 materials + 9 processes, 21 robots, 22 software items, 207 suppliers and 425 images; added the connector category, official CubeMars images and the materials library. Led the split into a core data repo and a site repo with data-v* releases and a data.lock; built the /api/v1 contract, the submission→review→outbox→worker-PR flow, Docker Compose deployment, PWA/share cards and the in-site correction form.</p>
  <a href="https://github.com/zeitvex" target="_blank" rel="noopener">GitHub</a>
</div>
<div class="ct">
  <div class="ct-head"><b>Dichen33</b><span class="ct-role">Founding contributor</span></div>
  <p>15 whole-robot entries with URDF/repo links, a bulk expansion of high- and low-level controllers plus IMU/camera/LiDAR — 50 data rows in total — and the part-data collection guide. The remote-controller category came from the ccc branch (5 transmitters + 2 CAN modules with 7 photos), together with the grouped-card layout for part notes and the home-page category preselect. He also added the software section's two groups: algorithms & methods (DreamWaQ, BeamDojo, AMP, PPO) and model architectures (MLP/MoE). Later filled 42 missing product images (40 parts) from official sources — DAMIAO JH/S, High Torque, MyActuator, Stackforce, Xiaomi, DJI TB47/TB48, Movella MTi-3, LDROBOT, Livox and RoboSense — bringing the site's missing-image count from 61 down to 21, with traceable documentation/store links for JH20, Stackforce 8108 and MTi-3. This round also rechecked 72 data files and 234 records: 216 links migrated or remapped (LCSC global product pages, vendor pages, official Gitee), 42 manual PDFs added, 14 third-party mirrors replaced, and 12 unlinkable URLs set to null; verified DAMIAO (36), High Torque (9, promoted to A-tier), Unitree GO-M8010-6/A1, Feetech ST-3215 and Sunlord parameters/links.</p>
  <a href="https://github.com/Dichen33" target="_blank" rel="noopener">GitHub</a>
</div>
<div class="ct">
  <div class="ct-head"><b>JadeCrane</b><span class="ct-role">Founding contributor</span></div>
  <p>Expanded the chip category from 14 to 18 parts (STM32H723 / TCAN334G / TMC2209 / AS5600), added official doc pages, datasheet PDFs and official repos for all 18 (each link verified), domestic 1+ prices for 17 of them with source and collection date, and 12 product photos. Also registered the doc_url / doc_pdf / repo_urls keys, clearing 20 false warnings (82 → 62).</p>
  <a href="https://github.com/Beni-537" target="_blank" rel="noopener">GitHub</a>
</div>
<div class="ct">
  <div class="ct-head"><b>WUSI321</b><span class="ct-role">Founding contributor</span></div>
  <p>Fixed the unit-conversion and comparability tables on /method and /semantics rendering as raw pipe-delimited text inside a VitePress raw-HTML block: the pipeline now generates HTML &lt;table&gt; elements from schema/semantics.json, the supplier questionnaire is emitted as &lt;ol&gt;, and a regression test (test_semantics_tables_are_html) guards the fix. Verified with pipeline build, VitePress build, validate and pytest. PR #5.</p>
  <a href="https://github.com/wusi321" target="_blank" rel="noopener">GitHub</a><a href="https://github.com/RoboWiki/RoboWiki.github.io/pull/5" target="_blank" rel="noopener">PR #5</a>
</div></div>
  </section>

  <section class="cd-how">
    <h2>How to get listed</h2>
    <ul><li>Add a spec, fix a unit, supply a correct product photo — your name goes on the list</li><li>Write a review with real operating conditions — it goes on that part's page too</li><li>Report an error with evidence — that counts as well</li></ul>
    <p class="cd-note">No contribution leaderboard. This site does not run a points game — ordering is always by spec and measured data, never by who contributed more.</p>
  </section>

  <p class="cd-foot"><a href="/submit">Go to submission →</a></p>
</div>
