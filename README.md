# dan.rio# Markdown Blog with Seamless Transitions



Personal blog built with minimal dependencies and seamless View Transitions.A minimal, elegant blog built with Markdown that features seamless page transitions using the View Transitions API.



## Stack## ✨ Features



- Python build script (Markdown → HTML)- 📝 **Write in Markdown** - Blog posts are simple `.md` files with frontmatter

- CSS-first animations with View Transitions API- 🎨 **Seamless Transitions** - Fluid card-to-page animations using View Transitions API

- Dark/light theme with localStorage persistence- 🌓 **Dark/Light Mode** - Toggle with preference persistence

- No framework, no Node.js- ⚡ **Fast & Minimal** - Pre-compiled HTML, no runtime processing

- ♿ **Accessible** - WCAG 2.1 AA compliant with screen reader support

## Development- 📱 **Responsive** - Works beautifully on all devices

- 🐍 **Simple Build** - Just Python, no Node.js required

```bash

# Install dependencies## 🚀 Quick Start

pip install -r requirements.txt

### 1. Install Dependencies

# Write posts in blog-posts/*.md

# Run build to generate HTML```bash

python build.pypip install -r requirements.txt

```

# Serve locally

python -m http.server 8080### 2. Write Your First Post

```

Create a new Markdown file in the `blog-posts/` folder:

## Deployment

```markdown

GitHub Pages serves from root. The `.nojekyll` file ensures all assets load correctly.---

title: My First Blog Post

1. Write/edit posts in `blog-posts/`date: 2025-10-23

2. Run `python build.py`excerpt: A brief description of your post that appears on the card.

3. Commit and push generated HTMLslug: my-first-post

4. GitHub Pages auto-deploysorder: 1

---

## Browser Support

## Your Content Here

CSS animations and View Transitions work in Chrome/Edge 111+. Other browsers get graceful fallbacks.

Write your blog post content using Markdown...
```

### 3. Build the Site

```bash
python build.py
```

This will:
- Convert all `.md` files to HTML blog posts
- Generate the index page with all posts
- Preserve all transitions and styling

### 4. Serve Locally

```bash
python -m http.server 8080
```

Then open `http://localhost:8080`

## 📝 Writing Posts

### Frontmatter Fields

Every post should start with YAML frontmatter:

```yaml
---
title: Your Post Title          # Required - appears in cards and page
date: 2025-10-23               # Required - used for sorting
excerpt: Brief description...   # Required - shown on card
slug: url-friendly-name        # Optional - defaults to filename
order: 1                       # Optional - for manual sorting (higher = first)
---
```

### Markdown Support

Full Markdown support including:
- Headers (`#`, `##`, `###`)
- **Bold** and *italic* text
- Lists (ordered and unordered)
- Links and images
- Code blocks with syntax highlighting
- Blockquotes
- Tables

### Adding a New Post

1. Create `blog-posts/your-new-post.md`
2. Add frontmatter and content
3. Run `python build.py`
4. Done! Your post appears on the site

**That's it!** The HTML is pre-compiled and ready to serve instantly.

## 🎯 File Structure

```
blog/
├── blog-posts/              # 📝 Your Markdown files (write here!)
│   ├── modern-web-development.md
│   └── css-animations-guide.md
├── blog/                    # 🏗️ Generated HTML files (auto-created)
│   ├── modern-web-development.html
│   └── css-animations-guide.html
├── styles.css              # 🎨 Main stylesheet
├── post.css                # 📄 Post-specific styles
├── theme.js                # 🌓 Dark mode toggle
├── transitions.js          # ✨ View transitions magic
├── build.py                # 🔨 Build script (run this!)
├── requirements.txt        # 📦 Python dependencies
└── index.html              # 🏠 Generated homepage (auto-created)
```

## 🎨 Customization

### Change Colors

Edit the CSS variables in `styles.css`:

```css
:root {
    --color-bg: #ffffff;
    --color-text: #000000;
    --color-border: #e5e5e5;
    /* ... */
}
```

### Change Site Name

Update "YOUR NAME" in the templates within `build.py`

### Modify Post Template

Edit the `generate_post_html()` function in `build.py`

## 🔄 Development Workflow

### Manual Build (Recommended)

```bash
python build.py
```

Run this whenever you add/edit a post. Fast and simple!

### Auto-rebuild on Save (Optional)

Use a file watcher like `watchdog`:

```bash
pip install watchdog
watchmedo shell-command --patterns="*.md" --recursive --command="python build.py" blog-posts/
```

## 🌐 Browser Support

- ✅ Chrome/Edge 111+ (full transitions)
- ✅ Firefox (graceful fallback)
- ✅ Safari (graceful fallback)

The site works in all browsers, but seamless transitions require View Transitions API support (Chrome 111+).

## 📚 How It Works

1. **Markdown Files** → Parsed with `python-frontmatter` and `markdown`
2. **Build Script** → Pre-compiles HTML for each post with matching `view-transition-name` attributes
3. **Static HTML** → No runtime processing, instant loading
4. **View Transitions** → Browser natively morphs matching elements during navigation
5. **SPA Navigation** → `transitions.js` intercepts clicks for seamless transitions

## 🎓 Adding Features

### Syntax Highlighting

Install `pygments`:

```bash
pip install pygments
```

Update `build.py` to use `markdown` with `codehilite` extension.

### RSS Feed

Add RSS generation to `build.py` using the parsed posts array.

### Tags/Categories

Add `tags: [web, css]` to frontmatter and filter in build script.

## 📖 Example Post

See `blog-posts/modern-web-development.md` for a complete example.

## 🤝 Credits

Built with:
- [python-markdown](https://python-markdown.github.io/) - Markdown parser
- [python-frontmatter](https://github.com/eyeseast/python-frontmatter) - Frontmatter parser
- View Transitions API - Native browser transitions

## ⚡ Why Pre-compile?

**Runtime conversion** (Markdown → HTML on page load):
- ❌ Slower page loads
- ❌ Requires JavaScript libraries in browser
- ❌ Processing overhead for every visitor

**Pre-compilation** (Markdown → HTML once, at build time):
- ✅ Instant page loads (just static HTML)
- ✅ No client-side dependencies
- ✅ Better SEO (pre-rendered content)
- ✅ Works without JavaScript
- ✅ You only run the build when writing posts

## 📄 License

MIT - Feel free to use for your own blog!

---

**Happy blogging!** ✍️
