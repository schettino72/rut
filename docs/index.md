---
layout: default
title: rut - Run Unit Tests
---

<div class="badges">
  <a href="https://pypi.org/project/rut/">
    <img src="https://img.shields.io/badge/python-3.12+-3776ab?logo=python&logoColor=white" alt="Python 3.12+">
  </a>
  <a href="https://github.com/schettino72/rut">
    <img src="https://img.shields.io/github/stars/schettino72/rut?style=social" alt="GitHub stars">
  </a>
  <a href="https://github.com/schettino72/rut/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
  </a>
  <a href="https://github.com/schettino72/rut#readme">
    <img src="https://img.shields.io/badge/docs-readme-blue" alt="Documentation">
  </a>
</div>

- **Fast** — dependency-aware ordering, runs only what changed
- **Optimized for AI coding agents** — tight feedback loops matter

```bash
pip install rut
```

<p class="section-header">Core Features</p>

<div class="feature-grid grid-2x2">
  <div class="feature-card">
    <div class="feature-header">
      <span class="feature-icon">⚡</span>
      <h3 class="feature-title">3 Characters</h3>
    </div>
    <p class="feature-desc">The fastest test command you'll ever type. Just <span class="rut">rut</span>.</p>
  </div>

  <div class="feature-card">
    <div class="feature-header">
      <span class="feature-icon">🔄</span>
      <h3 class="feature-title">Async Support</h3>
    </div>
    <p class="feature-desc">Built-in support for async test methods. No plugins needed.</p>
  </div>

  <div class="feature-card">
    <div class="feature-header">
      <span class="feature-icon">🎯</span>
      <h3 class="feature-title">Keyword Filtering</h3>
    </div>
    <p class="feature-desc">Filter tests by name patterns. Run exactly what you need.</p>
  </div>

  <div class="feature-card">
    <div class="feature-header">
      <span class="feature-icon">📈</span>
      <h3 class="feature-title">Coverage</h3>
    </div>
    <p class="feature-desc">Code coverage support without extra configuration.</p>
  </div>
</div>

<p class="section-header">What makes <span class="rut">rut</span> different</p>

<div class="feature-grid grid-2x2">
  <div class="feature-card">
    <div class="feature-header">
      <span class="feature-icon">📊</span>
      <h3 class="feature-title">Dependency Ordering</h3>
    </div>
    <p class="feature-desc">Topological test ordering by import graph. Tests for broken modules fail first.</p>
  </div>

  <div class="feature-card">
    <div class="feature-header">
      <span class="feature-icon">🚀</span>
      <h3 class="feature-title">Incremental Testing</h3>
    </div>
    <p class="feature-desc">Only run tests affected by your changes. Skip the rest.</p>
  </div>
</div>

<!-- Articles section - uncomment when ready to publish
<p class="section-header">Articles</p>

<div class="article-grid">
  <a href="{{ '/articles/why-tests-matter-for-ai-coding' | relative_url }}" class="article-card">
    <span class="card-tag">AI + Testing</span>
    <h3 class="card-title">Why Unit Tests Matter More for AI Coding Than for Humans</h3>
    <p class="card-summary">An AI agent doesn't remember what it broke three iterations ago. Your test suite does. Understanding the agent loop and why fast tests are essential.</p>
    <div class="card-arrow">Read article →</div>
  </a>
</div>
-->
