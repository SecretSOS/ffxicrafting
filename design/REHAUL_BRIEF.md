# ffxicrafting.com — page redesign brief for Claude Code

## Context

The current site (repo at `C:\Users\MEE87\Documents\ffxicrafting`, hosted on Vercel) is plain server-rendered HTML with three JS files total (search, table helpers, Vercel Analytics) — no framework. It's not slow because of the stack; it's hard to use because of specific, fixable interaction and layout patterns repeated across the content-heavy pages.

Two confirmed root causes, found by inspecting the live site directly:

1. **The section "tabs" on zone pages and craft/guild pages are not tabs.** They're `<a href="#anchor">` links. Every section's full content renders on the page at once, stacked end to end — a zone page with 375 data rows is one continuous scroll with jump-links pretending to be tabs.
2. **List pages have no filtering, grouping, or pagination.** `/zone/` is a flat two-column alphabetical list of 163 zones with no search box, even though the item search in the header already proves the pattern works elsewhere.

One page already does it right: the Crafting Calculator (`/calculator`) uses real collapsible accordion sections. That's the pattern to generalize, not invent from scratch.

## Goal

Rebuild the page templates — not the data pipeline — so the site reads like a proper wiki/magazine hybrid: real tab/accordion components, card-based sourcing instead of raw tables where it aids scanning, a consistent infobox + editorial rail layout, and filtering on every long list page.

## Stack recommendation

**Do not build this as a client-rendered React SPA.** This is a content site where most traffic lands directly on item/zone/recipe pages from search — it needs fast first paint and crawlable HTML per page. Use a framework that outputs static HTML per page but gives real component reuse:

- **Astro** (preferred) — static output by default, islands architecture for the bits that need interactivity (tabs, filters, the calculator), works well with a large generated dataset like this one.
- **Next.js with static export** is the fallback if Astro doesn't fit the existing data pipeline.

Either way: a "card," "infobox," "data table," and "tab group" should each be one component, used everywhere, not re-implemented per page template.

## Reference mockups (attached alongside this brief)

- `reference-zone-page.html` — North Gustaberg, working example. Open it in a browser: the five section buttons are real tabs (vanilla JS, `classList.toggle`), not anchors. Infobox top-right (wiki convention), editorial rail alongside the data panel.
- `reference-item-page.html` — Chunk of Copper Ore. Card-grid sourcing ("Where to get it" / "Used in") instead of a flat vendor table, with an "at a glance" infobox rail.

These are plain HTML/CSS/JS, not final code — they exist to pin down layout, type hierarchy (Fraunces serif display / Public Sans body / JetBrains Mono for numbers), and the tab/card interaction pattern. Treat the visual direction as a strong starting point, not a pixel-locked spec — reuse the project's own existing brand colors if there's a preference to keep them close to what's live now.

## Suggested build order

1. Scaffold the new framework project reading from the existing data source (don't touch the data/parsing layer yet).
2. Build the shared components first: `TabGroup`, `InfoboxCard`, `DataCard`, `SourceCard`, `StatRail`. Get these right once.
3. Migrate the **zone page** template first (highest page count, worst current problem).
4. Migrate the **craft/guild page** template (same fake-tab problem: Hours/Shop/GP Turn-ins/GP Rewards/Vendor/Recipes).
5. Migrate the **item page** template.
6. Add a filter/search box to `/zone/` and any other flat list page (crafts index, gathering index) reusing the header search pattern.
7. Preserve every existing URL — this is an SEO-relevant data site, don't break inbound links during the migration.

## Known data-layer issue (separate from the redesign, worth a ticket)

The Chocobo Digging "weight" column shows `0` for every item on every zone page currently — looks like a rounding/display bug in the data pipeline, not a real rate. Not a layout problem; flag it but don't try to fix it as part of this visual rehaul.
