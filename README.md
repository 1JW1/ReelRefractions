# Reel Refractions

A film blog for spontaneous reflections on cinema — emotional, instinctive, and sometimes messy, just like film itself.

**Live site:** [reel-refractions.com](https://reel-refractions.com)

## Tech Stack

- **Static site generator:** [Hugo](https://gohugo.io/) (v0.146.0)
- **Theme:** [PaperMod](https://github.com/adityatelange/hugo-PaperMod) (with extensive layout overrides)
- **Deployment:** [Vercel](https://vercel.com) (auto-deploys on push to `main`)
- **Comments:** [Remark42](https://remark42.com/) (self-hosted)
- **Newsletter:** [Buttondown](https://buttondown.com/)
- **Analytics:** Vercel Analytics (privacy-friendly, no cookies)

## Local Development

```bash
# Clone with submodules
git clone --recurse-submodules https://github.com/1JW1/ReelRefractions.git
cd ReelRefractions

# Install dependencies
npm install

# Start dev server (includes drafts)
npm run dev

# Production build
npm run build
```

The dev server runs at `http://localhost:1313` with live reload.

## Creating New Posts

Use the content workflow script to generate posts with AI-assisted front matter:

```bash
# Install Python dependencies
pip install -r scripts/requirements.txt

# Set your API key
export ANTHROPIC_API_KEY='sk-ant-...'

# Create a new post
python scripts/new_post.py path/to/body.txt path/to/cover.jpg [optional-inline-images...]

# Review the generated post in staging/, then move to content/posts/
mv staging/2025-01-15-film-title content/posts/2025-01-15-film-title
```

## Google Docs Integration

You can pass a Google Docs URL directly instead of a local `.txt` file:

```bash
python scripts/new_post.py "https://docs.google.com/document/d/YOUR_DOC_ID/edit" cover.jpg
```

### One-time setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/) and create a project (or select an existing one).
2. Enable the **Google Docs API**: `APIs & Services → Library → Google Docs API → Enable`.
3. Create OAuth 2.0 credentials: `APIs & Services → Credentials → Create Credentials → OAuth client ID`.
   - Application type: **Desktop app**
   - Give it any name (e.g. `ReelRefractions`)
4. Download the credentials JSON and save it as **`credentials.json`** in the project root (it is gitignored).
5. Install the updated Python dependencies:
   ```bash
   pip install -r scripts/requirements.txt
   ```
6. Run the script with a Google Docs URL. Your browser will open once for an OAuth consent screen. After authorising, a `token.json` file is saved to the project root (also gitignored) and subsequent runs skip the browser step.

> **Scope used:** `documents.readonly` — the script only reads your document, never modifies it.
>
> If you see a 403 error, delete `token.json` and re-run to re-authorise.

## Project Structure

```
layouts/          # Custom layout overrides (three-column design)
assets/css/       # Custom stylesheet
assets/icons/     # SVG icons (Letterboxd)
content/posts/    # Blog posts (page bundles)
content/vault/    # The Vault (archives page)
content/about/    # About page
scripts/          # Content workflow tools
themes/PaperMod/  # Theme (git submodule — do not modify)
```

## License

- **Code** (templates, scripts, configuration): [MIT License](LICENSE)
- **Content** (posts, images): [CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/)

See [LICENSE](LICENSE) for full details.
