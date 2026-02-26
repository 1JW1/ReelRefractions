# Reel Refractions — Writing Guide

A practical reference to open alongside a blank `index.md`. Everything here
maps directly to a front matter field or a content decision you'll face each
time you sit down to write.

---

## Monthly Cadence (2–3 posts)

Aim for this mix each month:

| Slot | Type | Purpose |
|------|------|---------|
| 1–2× | `new-release` | Core of the blog — responsive, timely |
| 1× | `retrospective` or `revisit` | Evergreen SEO, demonstrates range |
| Optional | `quick-take` | When a film deserves a reaction, not an essay |

Don't force the retrospective/revisit if nothing calls for it — but don't skip
it two months in a row either.

---

## Review Type Guide

Set `review_type` to one of these four values. It controls the chip shown on
cards and the category the post is filed under.

### `new-release`
- **Length**: 500–800 words
- **Focus**: First-watch feeling + one craft observation
- **Structure**: Situation → what works → what doesn't → verdict
- **Avoid**: Padding with plot summary. Assume the reader has seen the trailer.

### `retrospective`
- **Length**: 800–1,200 words
- **Focus**: Why it still matters — context, legacy, what changed since release
- **Structure**: Why now → original reception → what holds up → what doesn't → re-rating
- **Avoid**: Retelling the plot of a film everyone has seen.

### `revisit`
- **Length**: 500–700 words
- **Focus**: What changed between watches — the "I was wrong" or "I was right" arc
- **Structure**: Original take → what prompted the revisit → what changed → updated verdict
- **The hook**: Lead with the gap between then and now. That tension *is* the piece.

### `quick-take`
- **Length**: 300–400 words
- **Focus**: Pure feeling, one paragraph of analysis max
- **Structure**: One strong opening line → two or three honest reactions → a single verdict sentence
- **Avoid**: Trying to cover everything. Pick one thing and commit to it.

---

## Front Matter Cheat Sheet

Every field that appears on cards or in the post template. Fill all of them —
leaving one blank breaks a component.

---

### `refraction_quote`

**The most important field.** One sentence that captures the *feeling*, not
the plot. It appears as a pull quote on the post page and as the hook on
listing cards.

**Rules:**
- Must work as a standalone sentence — a stranger should understand it without
  reading the post
- Captures mood, theme, or the reviewer's core reaction — never plot events
- Test it: would you screenshot this and post it? If not, rewrite it

**Weak:** *"Heat is a great film about cops and robbers in Los Angeles."*

**Strong:** *"Heat doesn't ask whether obsession destroys you. It simply shows
two men who've already decided it's worth it."*

Write the whole review first, then find this sentence. It's usually already
there — you just have to recognise it.

---

### `genre_lineage`

The "In Context" box on each post. List 2–3 films that *illuminate* this one,
not just films in the same genre.

```yaml
genre_lineage:
  - title: "Uncut Gems (2019)"
    note: "same kinetic, relentless dread"
  - title: "Sicario (2015)"
    note: "violence that carries real weight and consequence"
  - title: "The Wrestler (2008)"
    note: "washed-up protagonist as a mirror for self-destruction"
```

**Rules:**
- 2 films minimum, 3 maximum
- Mix eras where possible — not three films from the same decade
- Each `note` is one clause: what connects them *and* how they differ
- Avoid the obvious: don't put *Alien* in the lineage of every sci-fi film

---

### `rating`

Format: `"X / 5"` — always with spaces around the slash.

```yaml
rating: "3.5 / 5"
```

Half-points are fine. Be consistent — decide privately what 3 means vs 4 and
stick to it across posts.

| Score | Meaning |
|-------|---------|
| 5 / 5 | Essential. Watch it now. |
| 4 / 5 | Very good. Worth your evening. |
| 3 / 5 | Flawed but worth watching once. |
| 2 / 5 | Not recommended. Here's why it doesn't work. |
| 1 / 5 | Avoid. |

---

### `spoiler`

```yaml
spoiler: true   # or false
```

**`true`** when analysis depends on:
- Specific plot turns or reveals
- Endings or final acts
- Character deaths or betrayals

**`false`** when analysis is:
- Thematic or tonal
- About performance, craft, direction
- About the first act only

When in doubt, mark `true`. Readers will thank you.

---

### `description`

One punchy sentence for the card and `<meta>` tag. Reads like a trailer line,
not a summary. Max 160 characters.

- Write it **last**, after the review is done
- Should function as the film's elevator pitch as filtered through your verdict
- **Not** a plot summary, **not** a repeat of the title

**Weak:** *"A review of Caught Stealing, a 2024 crime thriller."*

**Strong:** *"Starts hot, ends cold. A stylish burst of brutality that loses
its soul and stumbles into a one-note finish."*

---

### `summary`

One analytical sentence — different from `description`. Where `description` is
feeling, `summary` is argument.

- `description` → what the film *is*
- `summary` → what is *wrong or right* about it

Both appear on cards: description as the hook, summary as the secondary line
for readers who want more before clicking.

---

### `tags`

Tags power the inline search on the homepage. Use these categories
consistently — don't invent single-use tags.

| Category | Format | Example |
|----------|--------|---------|
| Genre | Capitalised noun | `Crime`, `Thriller`, `Horror`, `Sci-Fi`, `Action`, `Drama` |
| Director | Full name | `Michael Mann`, `Robert Eggers`, `Denis Villeneuve` |
| Lead actor | Full name, first-billed only | `Austin Butler`, `Zoë Kravitz` |
| Franchise | Only if 2+ franchise films reviewed | `Tron`, `Predator` |
| Era | For retrospectives only | `Classic` (pre-1980), `Eighties`, `Nineties` |

**Avoid:** `Review` (redundant), single-use descriptors, vague terms like
`Atmospheric` or `Gritty`.

4–8 tags per post is the right range. More dilutes the taxonomy.

---

### `cover` and `cover.alt`

The `alt` field is used for accessibility and Open Graph image previews.

- Describe the image as if explaining it to someone who can't see it
- Include: subject, pose, colours, mood, setting
- One detailed sentence — not "movie poster"

**Weak:** *"Caught Stealing movie poster"*

**Strong:** *"Austin Butler as Hank in a yellow-tinted promotional still,
mid-stride in a blood-spattered white shirt, Manhattan fire escapes blurred
behind him"*

---

## Newsletter Threshold

Not every post needs a send. Rules:

| Post type | Send? |
|-----------|-------|
| `new-release` | **Always send** — timely, subscriber value |
| `retrospective` | **Send if strong** — must have a fresh argument, not just a rewatch |
| `revisit` | **Send if the gap is interesting** — the "I was wrong" angle usually is |
| `quick-take` | **Batch** — save 3+ quick takes for a monthly digest, don't send individually |

---

## Running `new_post.py`

The script handles front matter generation. Basic usage:

```bash
python scripts/new_post.py body.txt cover.jpg --letterboxd "https://letterboxd.com/..."
```

With an article-page hero image:

```bash
python scripts/new_post.py body.txt listing-cover.jpg hero.jpg --letterboxd "..."
```

The script will:
1. Call Claude to infer all front matter fields from your body text
2. Print the generated front matter for review
3. Offer an `[E]dit` step to correct `review_type`, `rating`, `refraction_quote`, title, slug, description, and cover alt
4. Write the final post to `staging/<date>-<slug>/`

Move the staging directory to `content/posts/` when satisfied:

```bash
mv staging/2026-02-26-film-title content/posts/
```

**Always review and correct `refraction_quote` manually** — Claude's suggestion
is a starting point, not the final word.
