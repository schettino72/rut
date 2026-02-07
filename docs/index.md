---
layout: default
title: rut - Run Unit Tests
---
<!-- Icons: Lucide (ISC License) https://lucide.dev -->

<div class="hero">
  <div class="hero-logo">
    <img src="{{ '/assets/images/logo.png' | relative_url }}" alt="rut logo">
  </div>
  <div class="hero-content">
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
    <ul>
      <li><strong>Fast</strong> — dependency-aware ordering, runs only what changed</li>
      <li><strong>Optimized for AI coding agents</strong> — tight feedback loops matter</li>
    </ul>
    <pre><code class="language-bash">pip install rut</code></pre>
  </div>
</div>

<p class="section-header">Core Features</p>

<div class="feature-grid grid-2x2">
  <div class="feature-card">
    <div class="feature-header">
      <span class="feature-icon"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/></svg></span>
      <h3 class="feature-title">3 Characters</h3>
    </div>
    <p class="feature-desc">The fastest test command you'll ever type. Just <span class="rut">rut</span>.</p>
  </div>

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
    <p class="feature-desc">Filter tests by name patterns. Run exactly what you need.</p>
  </div>

  <div class="feature-card">
    <div class="feature-header">
      <span class="feature-icon"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg></span>
      <h3 class="feature-title">Coverage</h3>
    </div>
    <p class="feature-desc">Code coverage support without extra configuration.</p>
  </div>
</div>

<p class="section-header">What makes <span class="rut">rut</span> different</p>

<div class="feature-list">
  <a href="{{ '/articles/dependency-ordering' | relative_url }}" class="feature-card feature-card-link">
    <div class="feature-header">
      <span class="feature-icon"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><path d="M6 21V9a9 9 0 0 0 9 9"/></svg></span>
      <h3 class="feature-title">Dependency Ordering</h3>
    </div>
    <p class="feature-desc">Topological test ordering by import graph. Tests for broken modules fail first.</p>
    <span class="feature-link">Read more →</span>
  </a>

  <a href="{{ '/articles/incremental-testing' | relative_url }}" class="feature-card feature-card-link">
    <div class="feature-header">
      <span class="feature-icon"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 4 15 12 5 20 5 4"/><line x1="19" y1="5" x2="19" y2="19"/></svg></span>
      <h3 class="feature-title">Incremental Testing</h3>
    </div>
    <p class="feature-desc">Only run tests affected by your changes. Skip the rest.</p>
    <span class="feature-link">Read more →</span>
  </a>
</div>

<!-- Articles section - uncomment when ready
<p class="section-header">Articles</p>

<div class="article-grid">
  <a href="{{ '/articles/rut-guardrails-for-ai-agents' | relative_url }}" class="article-card">
    <span class="card-tag">rut</span>
    <h3 class="card-title">Unit Tests Are the Guardrails for AI Coding Agents</h3>
    <p class="card-summary">Test runner time dominates the AI coding loop. rut cuts it by 50-80% by running only affected tests. Built on 15+ years of dependency tracking tools.</p>
    <div class="card-arrow">Read article →</div>
  </a>

  <a href="{{ '/articles/why-tests-matter-for-ai-coding' | relative_url }}" class="article-card">
    <span class="card-tag">AI + Testing</span>
    <h3 class="card-title">Why Unit Tests Matter More for AI Coding Than for Humans</h3>
    <p class="card-summary">An AI agent doesn't remember what it broke three iterations ago. Your test suite does. Understanding the agent loop and why fast tests are essential.</p>
    <div class="card-arrow">Read article →</div>
  </a>
</div>
-->
