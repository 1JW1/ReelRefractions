#!/usr/bin/env python3
"""
new_post.py — Content workflow script for Reel Refractions
===========================================================

Automates new post creation by generating front matter using the Anthropic
Claude API and formatting the post body as Markdown.

Usage:
    python scripts/new_post.py <body.txt|google-docs-url> <cover_image> [secondary_image ...]

Requirements:
    - pip install -r scripts/requirements.txt
    - Set the ANTHROPIC_API_KEY environment variable
    - For Google Docs URLs: place credentials.json in the project root
      (see README for Google Cloud setup instructions)

The script:
    1. Reads the plain text body from the provided file or Google Docs URL
    2. Calls the Claude API to infer front matter (title, slug, description,
       summary, tags, review_type, rating, spoiler, refraction_quote, genre_lineage)
    3. Prints the inferred front matter for interactive review
    4. On confirmation, writes the final .md file to staging/<date>-<slug>/
    5. Copies images into the same directory
    6. User manually moves to content/posts/ when satisfied

The staging/ directory is gitignored and never committed directly.
"""

import argparse
import json
import os
import shutil
import sys
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("Error: 'anthropic' package not installed.")
    print("Run: pip install -r scripts/requirements.txt")
    sys.exit(1)


FRONT_MATTER_PROMPT = """You are a metadata generator for a film review blog called "Reel Refractions".
Given the blog post text below, generate Hugo-compatible front matter in JSON format with these fields:

- title: The post title (include film name and year if mentioned)
- slug: URL-friendly slug derived from the title (lowercase, hyphens)
- description: One punchy sentence for SEO/OpenGraph — reads like a trailer line, not a plot summary (max 160 characters)
- summary: One analytical sentence that differs from description — where description is feeling, summary is argument
- tags: Array of relevant tags (film title, genre, director full name, lead actor name — 4 to 8 tags; no generic tags like "Review")
- cover_alt: Vivid, descriptive alt text for the cover image (describe a likely movie poster or promotional still — include character poses, colours, mood, and setting in one detailed sentence)
- review_type: One of "new-release", "revisit", "retrospective", or "quick-take" — infer from writing style and context
- refraction_quote: The single best sentence from the post that captures the feeling, not the plot — must work as a standalone pull quote or social share
- genre_lineage: Array of exactly 2–3 objects, each with "title" (film name + year, e.g. "Heat (1995)") and "note" (one clause: what connects it AND how it differs).
  STRICT EDITORIAL RULES — all must be satisfied:
  1. AVOID THE OBVIOUS: Never pick the franchise predecessor or the single most famous film in the genre as a lineage entry. If reviewing a Tron film, TRON (1982) is off-limits. If reviewing a sci-fi film, do not default to Blade Runner, The Matrix, or Alien.
  2. MIX ERAS: Never choose two films from the same year. Aim for at least one decade of separation between any two entries.
  3. ILLUMINATE, DON'T JUST MATCH GENRE: Choose films that reveal something about the reviewed film's theme, tone, craft, or emotional register — not just films with a similar plot or genre tag. A film from a completely different genre can qualify if the connection is genuinely illuminating.
  4. EACH NOTE must contain two clauses: what connects them AND how they differ or what makes the comparison surprising.
{tmdb_context}- rating: The reviewer's score as a string in "X / 5" format (e.g. "3.5 / 5") — find the verdict or score in the text
- spoiler: Boolean — true if the post references specific plot events, endings, deaths, or twists; false if analysis is thematic or stylistic only

Return ONLY valid JSON, no markdown fences, no explanation.

Post text:
{body}"""


def get_api_key() -> str:
    """Read API key from environment variable."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        print("Error: ANTHROPIC_API_KEY environment variable is not set.")
        print("Export it before running: export ANTHROPIC_API_KEY='sk-ant-...'")
        sys.exit(1)
    return key


def is_google_docs_url(arg: str) -> bool:
    """Return True if arg looks like a Google Docs URL."""
    return arg.startswith("https://docs.google.com/document/")


def extract_doc_id(url: str) -> str:
    """Extract the document ID from a Google Docs URL.

    Handles the standard form:
        https://docs.google.com/document/d/<DOC_ID>/edit
    """
    parsed = urllib.parse.urlparse(url)
    parts = parsed.path.split("/")
    try:
        d_index = parts.index("d")
        return parts[d_index + 1]
    except (ValueError, IndexError):
        print(f"Error: Could not extract document ID from URL: {url}")
        sys.exit(1)


def _extract_text_from_doc(doc: dict) -> str:
    """Extract plain text from a Google Docs API response, preserving paragraphs."""
    paragraphs = []
    for element in doc.get("body", {}).get("content", []):
        paragraph = element.get("paragraph")
        if not paragraph:
            continue
        parts = []
        for run in paragraph.get("elements", []):
            text_run = run.get("textRun")
            if text_run:
                parts.append(text_run.get("content", "").rstrip("\n"))
        text = "".join(parts).strip()
        if text:
            paragraphs.append(text)
    return "\n\n".join(paragraphs)


def fetch_google_doc(url: str) -> str:
    """Fetch a Google Doc's content as plain text via the Docs API.

    Requires credentials.json in the working directory (project root).
    Caches the OAuth token to token.json after first authorisation.
    """
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError:
        print("Error: Google API packages not installed.")
        print("Run: pip install -r scripts/requirements.txt")
        sys.exit(1)

    SCOPES = ["https://www.googleapis.com/auth/documents.readonly"]
    creds_file = Path("credentials.json")
    token_file = Path("token.json")

    if not creds_file.exists():
        print("Error: credentials.json not found in the project root.")
        print("See README for Google Cloud setup instructions.")
        sys.exit(1)

    creds = None
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_file), SCOPES)
            creds = flow.run_local_server(port=0)
        token_file.write_text(creds.to_json())

    doc_id = extract_doc_id(url)
    service = build("docs", "v1", credentials=creds)

    try:
        doc = service.documents().get(documentId=doc_id).execute()
    except Exception as e:
        print(f"Error fetching Google Doc: {e}")
        print("If you see a 403, delete token.json and re-run to re-authorise.")
        sys.exit(1)

    return _extract_text_from_doc(doc)


def get_tmdb_api_key() -> str | None:
    """Return TMDB API key from environment, or None if not set."""
    return os.environ.get("TMDB_API_KEY")


def search_tmdb(title: str, year: str, api_key: str) -> int | None:
    """Search TMDB for a film by title (+ optional year). Returns movie_id or None."""
    params = urllib.parse.urlencode({
        "api_key": api_key,
        "query": title,
        "language": "en-US",
        "page": "1",
        **({"year": year} if year else {}),
    })
    url = f"https://api.themoviedb.org/3/search/movie?{params}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
        results = data.get("results", [])
        if results:
            return results[0]["id"]
    except Exception as e:
        print(f"  TMDB search failed: {e}")
    return None


def fetch_similar_movies(movie_id: int, api_key: str) -> list[dict]:
    """Return up to 6 similar movies from TMDB for the given movie_id."""
    params = urllib.parse.urlencode({"api_key": api_key, "language": "en-US", "page": "1"})
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/similar?{params}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
        results = data.get("results", [])[:6]
        return [
            {
                "title": r["title"],
                "year": r.get("release_date", "")[:4],
            }
            for r in results
            if r.get("title") and r.get("release_date")
        ]
    except Exception as e:
        print(f"  TMDB similar-movies fetch failed: {e}")
    return []


def build_tmdb_context(similar_movies: list[dict]) -> str:
    """Format the TMDB similar-movies list into a prompt context block."""
    if not similar_movies:
        return ""
    films = "\n  ".join(
        f"- {m['title']} ({m['year']})" for m in similar_movies
    )
    return (
        "  The following real films are catalogued as 'similar' by The Movie Database (TMDB). "
        "You MAY use 1–2 of these if they genuinely illuminate the reviewed film via themes, "
        "tone, or craft — not just shared genre. Replace the remainder with more revealing "
        "choices from any era:\n  " + films + "\n"
    )


def generate_front_matter(body: str, api_key: str, tmdb_context: str = "") -> dict:
    """Call Claude API to generate front matter from post body."""
    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1536,
        messages=[
            {
                "role": "user",
                "content": FRONT_MATTER_PROMPT.format(
                    body=body[:8000],
                    tmdb_context=tmdb_context,
                ),
            }
        ],
    )

    response_text = message.content[0].text.strip()

    # Strip markdown fences if present
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        response_text = "\n".join(lines[1:-1])

    return json.loads(response_text)


_REVIEW_TYPE_TO_CATEGORY = {
    "new-release": "New Releases",
    "revisit": "Revisits",
    "retrospective": "Retrospectives",
    "quick-take": "Quick Takes",
}


def format_front_matter(meta: dict, cover_image: str, today: str, single_image: str = "", letterboxd_url: str = "") -> str:
    """Format metadata dict into Hugo YAML front matter."""
    tags = "\n".join(f'  - "{t}"' for t in meta.get("tags", []))
    review_type = meta.get("review_type", "new-release")
    category = _REVIEW_TYPE_TO_CATEGORY.get(review_type, "New Releases")
    cover_alt = meta.get("cover_alt", "")
    spoiler_val = "true" if meta.get("spoiler", False) else "false"
    refraction_quote = meta.get("refraction_quote", "").replace('"', '\\"')
    summary = meta.get("summary", meta["description"]).replace('"', '\\"')

    single_image_lines = ""
    if single_image:
        single_image_lines = f'\n  singleImage: "{single_image}"\n  singleAlt: ""'

    if meta.get("genre_lineage"):
        gl_lines = []
        for entry in meta["genre_lineage"]:
            t = entry.get("title", "").replace('"', '\\"')
            n = entry.get("note", "").replace('"', '\\"')
            gl_lines.append(f'  - title: "{t}"\n    note: "{n}"')
        genre_lineage_block = "genre_lineage:\n" + "\n".join(gl_lines)
    else:
        genre_lineage_block = "genre_lineage: []"

    return f"""---
title: "{meta['title']}"
date: {today}T12:00:00Z
draft: false
slug: "{meta['slug']}"
author: "Erwin Bernard"
description: "{meta['description']}"
tags:
{tags}
categories:
  - "{category}"
showToc: false
cover:
  image: "{cover_image}"
  alt: "{cover_alt}"
  caption: ""{single_image_lines}
  relative: true
letterboxd_url: "{letterboxd_url}"
summary: "{summary}"
rating: "{meta.get('rating', '')}"
spoiler: {spoiler_val}
review_type: "{review_type}"
refraction_quote: "{refraction_quote}"
{genre_lineage_block}
---"""


def format_body(body: str, secondary_images: list[str]) -> str:
    """Format plain text body as Markdown, inserting secondary images."""
    paragraphs = [p.strip() for p in body.strip().split("\n\n") if p.strip()]

    if not secondary_images:
        return "\n\n".join(paragraphs)

    # Distribute secondary images evenly through the post
    total = len(paragraphs)
    result = []
    image_positions = []

    if total > 1 and secondary_images:
        step = max(1, total // (len(secondary_images) + 1))
        for i, img in enumerate(secondary_images):
            pos = step * (i + 1)
            if pos < total:
                image_positions.append((pos, img))

    img_idx = 0
    for i, para in enumerate(paragraphs):
        result.append(para)
        if img_idx < len(image_positions) and i == image_positions[img_idx][0] - 1:
            img_name = image_positions[img_idx][1]
            result.append(f'{{{{< figure src="{img_name}" alt="" caption="" >}}}}')
            img_idx += 1

    return "\n\n".join(result)


def main():
    parser = argparse.ArgumentParser(
        description="Create a new Reel Refractions blog post with AI-generated front matter."
    )
    parser.add_argument(
        "body",
        help="Path to plain text file OR a Google Docs URL (https://docs.google.com/document/d/...)",
    )
    parser.add_argument("cover", help="Path to cover/hero image")
    parser.add_argument("images", nargs="*", help="Paths to secondary inline images")
    parser.add_argument("--letterboxd", default="", help="Letterboxd URL for this film")
    parser.add_argument(
        "--tmdb-id",
        type=int,
        default=None,
        metavar="ID",
        help="TMDB movie ID — skips the title search step. "
             "Find it at themoviedb.org (e.g. 533533 for Tron: Ares). "
             "Requires TMDB_API_KEY env var.",
    )
    args = parser.parse_args()

    # Validate inputs
    cover_path = Path(args.cover)

    if not cover_path.is_file():
        print(f"Error: Cover image not found: {cover_path}")
        sys.exit(1)

    secondary_paths = []
    for img in args.images:
        p = Path(img)
        if not p.is_file():
            print(f"Error: Secondary image not found: {p}")
            sys.exit(1)
        secondary_paths.append(p)

    # Fetch body from Google Docs URL or read from local file
    if is_google_docs_url(args.body):
        print("Fetching document from Google Docs...")
        body = fetch_google_doc(args.body)
    else:
        body_path = Path(args.body)
        if not body_path.is_file():
            print(f"Error: Body file not found: {body_path}")
            sys.exit(1)
        body = body_path.read_text(encoding="utf-8")

    api_key = get_api_key()

    # Optionally enrich genre_lineage with real TMDB similar-movies data
    tmdb_context = ""
    tmdb_api_key = get_tmdb_api_key()
    if tmdb_api_key:
        movie_id = args.tmdb_id
        if movie_id is None:
            # Extract a rough title guess from the first line of the body for search
            first_line = body.strip().split("\n")[0][:80]
            print(f"\nSearching TMDB for: {first_line!r}...")
            movie_id = search_tmdb(first_line, "", tmdb_api_key)
        if movie_id:
            print(f"  Fetching similar movies for TMDB ID {movie_id}...")
            similar = fetch_similar_movies(movie_id, tmdb_api_key)
            if similar:
                tmdb_context = build_tmdb_context(similar)
                print(f"  Found {len(similar)} similar films from TMDB.")
            else:
                print("  No similar movies found on TMDB.")
        else:
            print("  Could not find film on TMDB — proceeding without TMDB context.")
    else:
        print("\n(TMDB_API_KEY not set — genre_lineage will be generated from post text alone.)")

    # Generate front matter via Claude
    print("\nGenerating front matter via Claude API...")
    try:
        meta = generate_front_matter(body, api_key, tmdb_context=tmdb_context)
    except (json.JSONDecodeError, anthropic.APIError) as e:
        print(f"Error generating front matter: {e}")
        sys.exit(1)

    today = date.today().isoformat()
    cover_name = cover_path.name

    # First secondary image becomes the article-page hero; rest go inline
    article_cover_path = None
    article_cover_name = ""
    if secondary_paths:
        article_cover_path = secondary_paths[0]
        article_cover_name = article_cover_path.name
        secondary_paths = secondary_paths[1:]

    secondary_names = [p.name for p in secondary_paths]

    front_matter = format_front_matter(meta, cover_name, today, single_image=article_cover_name, letterboxd_url=args.letterboxd)

    # Display for review
    print("\n" + "=" * 60)
    print("GENERATED FRONT MATTER")
    print("=" * 60)
    print(front_matter)
    print("=" * 60)

    # Interactive confirmation
    while True:
        choice = input("\n[C]onfirm, [E]dit fields, or [Q]uit? ").strip().lower()
        if choice == "c":
            break
        elif choice == "e":
            new_title = input(f"  Title [{meta['title']}]: ").strip()
            if new_title:
                meta["title"] = new_title
            new_desc = input(f"  Description [{meta['description']}]: ").strip()
            if new_desc:
                meta["description"] = new_desc
            new_slug = input(f"  Slug [{meta['slug']}]: ").strip()
            if new_slug:
                meta["slug"] = new_slug
            new_alt = input(f"  Cover alt [{meta.get('cover_alt', '')}]: ").strip()
            if new_alt:
                meta["cover_alt"] = new_alt
            print("  Review type options: new-release, revisit, retrospective, quick-take")
            new_type = input(f"  Review type [{meta.get('review_type', 'new-release')}]: ").strip()
            if new_type in ("new-release", "revisit", "retrospective", "quick-take"):
                meta["review_type"] = new_type
            elif new_type:
                print(f"  Invalid review type '{new_type}' — keeping current value.")
            new_rating = input(f"  Rating (e.g. 3.5 / 5) [{meta.get('rating', '')}]: ").strip()
            if new_rating:
                meta["rating"] = new_rating
            current_quote = meta.get("refraction_quote", "")
            preview = (current_quote[:60] + "...") if len(current_quote) > 60 else current_quote
            new_quote = input(f"  Refraction quote [{preview}]: ").strip()
            if new_quote:
                meta["refraction_quote"] = new_quote
            front_matter = format_front_matter(meta, cover_name, today, single_image=article_cover_name, letterboxd_url=args.letterboxd)
            print("\nUpdated front matter:")
            print(front_matter)
        elif choice == "q":
            print("Cancelled.")
            sys.exit(0)

    # Build post content
    formatted_body = format_body(body, secondary_names)
    full_content = front_matter + "\n\n" + formatted_body + "\n"

    # Write to staging directory
    slug = meta["slug"]
    staging_dir = Path("staging") / f"{today}-{slug}"
    staging_dir.mkdir(parents=True, exist_ok=True)

    post_file = staging_dir / "index.md"
    post_file.write_text(full_content, encoding="utf-8")

    # Copy images
    shutil.copy2(cover_path, staging_dir / cover_name)
    if article_cover_path:
        shutil.copy2(article_cover_path, staging_dir / article_cover_name)
    for p in secondary_paths:
        shutil.copy2(p, staging_dir / p.name)

    print(f"\nPost created at: {staging_dir}/")
    print(f"  - {post_file}")
    print(f"  - {cover_name} (listing cover)")
    if article_cover_name:
        print(f"  - {article_cover_name} (article hero)")
    for name in secondary_names:
        print(f"  - {name} (inline)")
    print(f"\nTo publish, move the directory to content/posts/:")
    print(f"  mv {staging_dir} content/posts/{today}-{slug}")


if __name__ == "__main__":
    main()
