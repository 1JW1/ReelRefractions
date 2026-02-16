#!/usr/bin/env python3
"""
new_post.py — Content workflow script for Reel Refractions
===========================================================

Automates new post creation by generating front matter using the Anthropic
Claude API and formatting the post body as Markdown.

Usage:
    python scripts/new_post.py <body.txt> <cover_image> [secondary_image ...]

Requirements:
    - pip install anthropic  (or: pip install -r scripts/requirements.txt)
    - Set the ANTHROPIC_API_KEY environment variable

The script:
    1. Reads the plain text body from the provided file
    2. Calls the Claude API to infer front matter (title, slug, description,
       tags, categories, keywords, date)
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
- description: One concise sentence for SEO/OpenGraph (max 160 characters)
- tags: Array of relevant tags (film title, genre, actor names, themes — 4 to 10 tags)
- categories: Array with one category — either "Film Reviews" or "Film" (use "Film Reviews" for review posts, "Film" for general discussion)
- keywords: Array of SEO keywords (3 to 6 broad terms)

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


def generate_front_matter(body: str, api_key: str) -> dict:
    """Call Claude API to generate front matter from post body."""
    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": FRONT_MATTER_PROMPT.format(body=body[:8000]),
            }
        ],
    )

    response_text = message.content[0].text.strip()

    # Strip markdown fences if present
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        response_text = "\n".join(lines[1:-1])

    return json.loads(response_text)


def format_front_matter(meta: dict, cover_image: str, today: str) -> str:
    """Format metadata dict into Hugo YAML front matter."""
    tags = "\n".join(f'  - "{t}"' for t in meta.get("tags", []))
    categories = "\n".join(f'  - "{c}"' for c in meta.get("categories", ["Film Reviews"]))
    keywords = "\n".join(f'  - "{k}"' for k in meta.get("keywords", []))

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
{categories}
keywords:
{keywords}
showToc: false
cover:
  image: "{cover_image}"
  alt: ""
  caption: ""
  relative: true
summary: "{meta['description']}"
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
    parser.add_argument("body", help="Path to plain text file containing the post body")
    parser.add_argument("cover", help="Path to cover/hero image")
    parser.add_argument("images", nargs="*", help="Paths to secondary inline images")
    args = parser.parse_args()

    # Validate inputs
    body_path = Path(args.body)
    cover_path = Path(args.cover)

    if not body_path.is_file():
        print(f"Error: Body file not found: {body_path}")
        sys.exit(1)
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

    body = body_path.read_text(encoding="utf-8")
    api_key = get_api_key()

    # Generate front matter via Claude
    print("\nGenerating front matter via Claude API...")
    try:
        meta = generate_front_matter(body, api_key)
    except (json.JSONDecodeError, anthropic.APIError) as e:
        print(f"Error generating front matter: {e}")
        sys.exit(1)

    today = date.today().isoformat()
    cover_name = cover_path.name
    secondary_names = [p.name for p in secondary_paths]

    front_matter = format_front_matter(meta, cover_name, today)

    # Display for review
    print("\n" + "=" * 60)
    print("GENERATED FRONT MATTER")
    print("=" * 60)
    print(front_matter)
    print("=" * 60)

    # Interactive confirmation
    while True:
        choice = input("\n[C]onfirm, [E]dit title/description, or [Q]uit? ").strip().lower()
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
            front_matter = format_front_matter(meta, cover_name, today)
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
    for p in secondary_paths:
        shutil.copy2(p, staging_dir / p.name)

    print(f"\nPost created at: {staging_dir}/")
    print(f"  - {post_file}")
    print(f"  - {cover_name}")
    for name in secondary_names:
        print(f"  - {name}")
    print(f"\nTo publish, move the directory to content/posts/:")
    print(f"  mv {staging_dir} content/posts/{today}-{slug}")


if __name__ == "__main__":
    main()
