# Reel Refractions — Site Audit

**Conducted:** February 2026
**Site:** https://reel-refractions.com/
**Stack:** Hugo + PaperMod (custom) · Vercel · TARDIS blue dark theme

---

## Core Themes & Tone

**Themes:** Feeling-first film criticism. Anti-algorithm, anti-star-rating in principle — but still delivers structured verdicts. Coverage skews toward new mainstream releases (crime, sci-fi, action) but the About signals broader aspirations.

**Tone:** Conversational, direct, occasionally profane in a considered way. Erwin commits to verdicts, uses specific scene and dialogue references, and writes *with* the reader — not at them. The voice is the site's clearest asset and should be protected at all costs when making structural changes.

---

## Structural Strengths

1. Three-column layout is distinctive — immediately reads as editorial, not another Substack
2. Performance fundamentals are excellent: self-hosted fonts, WebP srcset, preloads, cookie-free analytics
3. Accessibility basics are in place: skip link, ARIA labels, semantic HTML, keyboard-friendly nav
4. The Vault (screenplay-formatted archive) is the most original design idea on the site
5. AI-assisted content workflow (Python + Claude API) enables a sustainable publishing cadence
6. Robots.txt actively blocks AI scrapers — a principled stance aligned with the blog's ethos
7. Letterboxd integration threads the blog into an existing film community

---

## Structural Weaknesses

1. **Thin content library** — 3 posts is not enough to establish a reading habit, demonstrate range, or rank for anything
2. **Flat single category ("Film Reviews")** — no editorial differentiation between new releases, revisits, deep dives
3. **Search is invisible** — `/search/` is fully built with Fuse.js but not linked in the nav menu
4. **Newsletter is dead infrastructure** — `buttondownURL: ""` means the signup block renders nothing
5. **No related posts** — readers finishing a review have nowhere obvious to go next
6. **Tags include noise** — "Review" appears on every post; "CGI Criticism" on one; the taxonomy doesn't guide discovery

---

## SEO Issues

1. **No JSON-LD Review schema** — Google can't generate rich results (star ratings in SERPs) from these reviews
2. **`images: []` is empty** — no default Open Graph image; social shares for non-post pages render blank
3. **Summary duplicates description exactly** on all 3 posts — Hugo uses each field differently; they should differ
4. **About page meta description is weak** — "About Reel Refractions — a film blog by Erwin Bernard." tells crawlers nothing
5. **No internal linking between posts** — crawlers and readers can't traverse the content graph
6. **Taxonomy pages have no descriptive text** — `/categories/` and tag pages are thin stubs
7. **Keywords are generic** — `[Blog, Film, Cinema, Reviews]` — no long-tail specificity

---

## UX/Styling Issues

1. **No rating on post cards** — the verdict (2/5, 3.5/5) is the most scannable signal for a film blog and is invisible in list view
2. **Spoiler status embedded in the title string** — "— Spoiler Review" pollutes the `<title>` tag; a visual badge is cleaner
3. **Inline links are invisible** — `a { color: var(--text-color) }` makes body links indistinguishable from prose without hover
4. **Audio narration is unexplained** — the Web Speech API player appears without introduction; new visitors won't know what it does
5. **Right sidebar "Trending Tags" shows counts of 1 everywhere** — meaningless at 3 posts; should hide counts or the section entirely
6. **Muybridge animation is a raw GIF** — not a `<video>` element; larger file, worse rendering performance
7. **Breadcrumbs are redundant** — "Home > Film Reviews > Post Title" adds no value when there's only one category

---

## 5 High-Impact Content Improvements

1. **Add retrospective reviews of canonical films** — *Heat*, *Alien*, *Parasite* etc. generate evergreen traffic and demonstrate range beyond new releases
2. **Vary review format by type** — short-form "Quick Takes" (350 words, emotional) vs. long-form analysis (800–1,200 words, craft-focused); signals editorial intent
3. **Expand the About page** — add how Erwin watches films, what he won't cover, a direct invitation to disagree; currently 4 short paragraphs, should feel like a manifesto
4. **Add monthly revisits** — a film 5+ years old re-evaluated in current context creates natural internal links and demonstrates intellectual range
5. **Add author micro-bio to post footers** — one sentence humanises the writing and builds recognition across posts

---

## 5 Structural Improvements

1. **Add Search to the nav menu** — it's fully built; one line in `hugo.yaml`
2. **Implement JSON-LD Review schema** — `@type: Review` with `reviewRating`, `itemReviewed` (Film), `author`; enables rich results in Google
3. **Configure Buttondown newsletter** — commit to a URL and activate it; even 50 subscribers creates a channel independent of search
4. **Create differentiated post categories** — "New Releases" / "Revisits" / "Quick Takes" / "Retrospectives" instead of flat "Film Reviews"
5. **Add "More like this"** — Hugo's built-in `related` content surfaces 2–3 posts by shared tags; one template change, significant improvement to pages-per-session

---

## 5 Design Improvements

1. **Show film rating on post cards** — a verdict badge (e.g. `★★ 2/5`) in the cover image corner is the single most scannable signal for a film blog
2. **Replace spoiler status in title with a visual chip** — a `SPOILERS` badge on card and post header is cleaner than embedding it in the `<title>` string
3. **Make inline links visually distinct** — `text-decoration: underline` + a subtle tint (`#7ab8d4`) within `.post-content`
4. **Convert Muybridge GIF to `<video>`** — WebM + MP4 fallback with `autoplay loop muted playsinline`; meaningfully smaller, no GIF jank
5. **Add a "Just Watched" widget to the right sidebar** — a manually updated data file rendered in the sidebar adds personality and freshness signal between posts

---

## 3 Ways to Make the Blog More Distinctive

### 1. "The Refraction" Pull-Quote
After each post, manually select the single sentence that best captures the take. Display it as a large italic pull-quote beneath the post header — before the body, after the metadata. This creates a signature reading experience and a highly shareable format. The pull-quote also surfaces on the post card in list view.

### 2. Genre Lineage Box
A small "In Context" box per review shows 2–3 films that preceded or influenced the film being reviewed, each with a one-line annotation. For example, on *Caught Stealing*:

```
→ Uncut Gems (2019) — same kinetic dread
→ Sicario (2015) — violence with weight
→ The Wrestler (2008) — washed-up protagonist as mirror
```

This turns individual reviews into navigable film education. Nothing else in the indie film blog space does this consistently.

### 3. "Just Watched" Sidebar Widget
A sidebar section showing the last 3–5 films Erwin watched (with rating), drawn from a manually maintained data file. Films not yet reviewed show a "review pending" indicator. This bridges the gap between the blog and his active Letterboxd presence, gives the sidebar live personality between posts, and creates anticipation: readers see he watched something before the full review arrives.

---

## Implementation Notes

Changes were implemented on branch `claude/website-audit-drkmO`. Three dummy articles were created to demonstrate the editorial vision:

- **Heat (1995)** — Retrospective format, testing the genre lineage box and refraction quote at scale
- **Tron: Legacy (2010)** — Revisit format, demonstrating internal linking back to the Tron: Ares review
- **Nosferatu (2024)** — Quick Take format, short-form emotional review without section headings

All existing posts were refactored with new front matter fields (`rating`, `spoiler`, `refraction_quote`, `genre_lineage`, `review_type`) and moved to differentiated categories.
