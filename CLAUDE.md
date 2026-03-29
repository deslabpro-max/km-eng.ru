# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Static landing page for **KM-ENGINEERING** (КМ-ИНЖИНИРИНГ) — a Russian B2B distributor of security systems (fire suppression, CCTV, access control) for the energy/industrial sector. Hosted on GitHub Pages at **km-eng.ru**.

## Architecture

Single-page static site (no build tools, no bundler, no framework):

- **index.html** — main landing page with sections: hero slider, advantages, about, partners/logos, contact form
- **thanks.html** — post-form-submission redirect page (noindex)
- **styles.css** — all styles; uses CSS custom properties (design tokens in `:root`), BEM-like naming, responsive breakpoints
- **script.js** — all interactivity: hero slider with autoplay, scroll-reveal via IntersectionObserver, sticky header, smooth scroll, mobile menu, touch/swipe support
- **scraper.py** — one-time utility that scraped the original Tilda site into `scraped_data/`; not part of the live site
- **scraped_data/** — archived content from the original site scrape (HTML, images, JSON); reference only

## Running Locally

No build step. Serve the root directory:

```bash
npx serve .
# or
python -m http.server 8000
```

## Deployment

GitHub Pages from `main` branch. CNAME points to `km-eng.ru`. Push to `main` triggers deploy automatically.

## Key Details

- **Language**: all user-facing content is in Russian
- **Form**: contact form submits to formsubmit.co, redirects to thanks.html on success
- **SEO**: meta tags, Open Graph, sitemap.xml, robots.txt are configured
- **Font**: Open Sans via Google Fonts
- **Design tokens**: colors, spacing, typography scales defined as CSS custom properties in `:root` (styles.css)
- **Cache busting**: stylesheet link uses `?v=11` query parameter — increment when changing styles
