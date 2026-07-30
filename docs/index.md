---
layout: default
title: Run Unit Tests
description: "A Python unittest runner with test impact analysis and dependency ordering. Run only affected tests, skip what hasn't changed."
---
<!-- Icons: Lucide (ISC License) https://lucide.dev -->

<div class="hero">
  <div class="hero-logo">
    <img src="{{ '/assets/images/logo.png' | relative_url }}" alt="rut logo">
  </div>
  <div class="hero-content">
    <div class="badges">
      <a href="https://pypi.org/project/rut/"
         data-g4d="click" data-g4d-target="badge-pypi">
        <img src="https://img.shields.io/badge/python-3.10+-3776ab?logo=python&logoColor=white" alt="Python 3.10+">
      </a>
      <a href="https://github.com/schettino72/rut"
         data-g4d="cta_click" data-g4d-target="badge-github">
        <img src="https://img.shields.io/github/stars/schettino72/rut?style=social" alt="GitHub stars">
      </a>
      <a href="https://github.com/schettino72/rut/blob/main/LICENSE">
        <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
      </a>
      <a href="https://github.com/schettino72/rut#readme">
        <img src="https://img.shields.io/badge/docs-readme-blue" alt="Documentation">
      </a>
    </div>
    <ul>
      <li>Test runner for Python's <code>unittest</code></li>
      <li>Orders tests by dependencies — foundational modules first</li>
      <li>Skips tests unaffected by your changes</li>
    </ul>
    <pre><code class="language-bash">pip install rut
rut              # all tests, smart order
rut --changed    # only affected tests</code></pre>
    <a href="{{ '/articles/usage' | relative_url }}" class="cta-button cta-button-sm"
       data-g4d="cta_click" data-g4d-target="hero-usage">Full usage guide →</a>
  </div>
</div>


<p class="section-header">How it works</p>

<div class="feature-list">
  <a href="{{ '/articles/dependency-ordering' | relative_url }}" class="feature-card feature-card-link"
     data-g4d="click" data-g4d-target="feature-dependency-ordering">
    <div class="feature-callout">
      <div class="feature-callout-text">
        <div class="feature-header">
          <span class="feature-icon"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="16" y="16" width="6" height="6" rx="1"/><rect x="2" y="16" width="6" height="6" rx="1"/><rect x="9" y="2" width="6" height="6" rx="1"/><path d="M5 16v-3a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v3"/><path d="M12 12V8"/></svg></span>
          <h3 class="feature-title">Order tests by dependencies</h3>
        </div>
        <p class="feature-desc">Foundational modules run first, so when something breaks you see the root cause immediately — not 300 cascading failures.</p>
        <span class="feature-link">Read more →</span>
      </div>
      <div class="feature-callout-image">
        <img src="{{ '/assets/images/cover-dependency-order.png' | relative_url }}" alt="Comparison of alphabetical vs dependency order - showing much earlier failure detection">
      </div>
    </div>
  </a>

  <a href="{{ '/articles/incremental-testing' | relative_url }}" class="feature-card feature-card-link"
     data-g4d="click" data-g4d-target="feature-incremental-testing">
    <div class="feature-callout">
      <div class="feature-callout-text">
        <div class="feature-header">
          <span class="feature-icon"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 4 15 12 5 20 5 4"/><line x1="19" y1="5" x2="19" y2="19"/></svg></span>
          <h3 class="feature-title">Skip tests unaffected by your changes</h3>
        </div>
        <p class="feature-desc"><code>rut --changed</code> runs only affected tests — tests that depend on files you modified. Test impact analysis that typically cuts test time by 50–80%.</p>
        <span class="feature-link">Read more →</span>
      </div>
      <div class="feature-callout-image">
        <img src="{{ '/assets/images/cover-incremental-testing.png' | relative_url }}" alt="DAG showing only affected tests run after a change">
      </div>
    </div>
  </a>
</div>


<p class="section-header">Core Features</p>

<div class="feature-grid grid-2x2">
  <div class="feature-card">
    <div class="feature-header">
      <span class="feature-icon"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/></svg></span>
      <h3 class="feature-title">Async Support</h3>
    </div>
    <p class="feature-desc">Built-in support for async test methods. No plugins needed.</p>
  </div>

  <div class="feature-card">
    <div class="feature-header">
      <span class="feature-icon"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg></span>
      <h3 class="feature-title">Keyword Filtering</h3>
    </div>
    <p class="feature-desc">Filter tests by name with <code>-k</code>. Run exactly what you need.</p>
  </div>

  <div class="feature-card">
    <div class="feature-header">
      <span class="feature-icon"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/></svg></span>
      <h3 class="feature-title">Fail Fast</h3>
    </div>
    <p class="feature-desc">Exit on the first failure with <code>-x</code>. Pairs well with dependency ordering.</p>
  </div>

  <div class="feature-card">
    <div class="feature-header">
      <span class="feature-icon"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg></span>
      <h3 class="feature-title">Coverage</h3>
    </div>
    <p class="feature-desc">Code coverage with <code>--cov</code>. No extra configuration.</p>
  </div>
</div>


<p class="section-header">Comparison</p>

<div class="feature-list">
  <div class="feature-card">
    <div class="feature-header">
      <h3 class="feature-title">vs python -m unittest</h3>
    </div>
    <p class="feature-desc">No smart ordering, no way to skip unaffected tests, no <code>-k</code>, no coverage. <span class="rut">rut</span> adds what's missing.</p>
  </div>

  <div class="feature-card">
    <div class="feature-header">
      <h3 class="feature-title">vs pytest</h3>
    </div>
    <p class="feature-desc">Great ecosystem and plugin support. <span class="rut">rut</span> takes a different approach — instead of replacing the test framework, it focuses on making the runner itself smarter (dependency ordering, affected-only runs) while staying on stdlib unittest.</p>
  </div>
</div>


<p class="section-header">Articles</p>

<div class="article-grid">
  <a href="{{ '/articles/import-graph' | relative_url }}" class="article-card"
     data-g4d="click" data-g4d-target="article-import-graph">
    <span class="card-tag">internals</span>
    <h3 class="card-title">How rut Builds the Import Dependency Graph</h3>
    <p class="card-summary">Static import analysis at the module level. How rut understands your codebase structure to order tests and skip unaffected ones.</p>
    <div class="card-arrow">Read article →</div>
  </a>

  <a href="{{ '/articles/migrate-from-pytest' | relative_url }}" class="article-card"
     data-g4d="click" data-g4d-target="article-migrate-from-pytest">
    <span class="card-tag">how-to</span>
    <h3 class="card-title">Migrating from pytest to rut</h3>
    <p class="card-summary">A practical guide for converting a pytest test suite to rut. Includes AI-agent-friendly instructions.</p>
    <div class="card-arrow">Read article →</div>
  </a>
</div>


<div class="cta-bottom">
  <a href="{{ '/articles/usage' | relative_url }}" class="cta-button"
     data-g4d="cta_click" data-g4d-target="bottom-usage">Get started with rut →</a>
</div>
