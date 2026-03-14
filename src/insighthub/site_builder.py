import json
import math
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup

try:
    import markdown as md  # type: ignore
except ImportError:  # pragma: no cover - fallback path
    md = None


FORBIDDEN_TAGS = {"script", "iframe", "object", "embed", "style", "link", "meta"}
SAFE_PROTOCOLS = {"http", "https", "mailto"}


def build_site(
    *,
    manifest_path: str,
    content_root: str,
    output_dir: str,
    site_url: str,
    site_title: str = "每日趋势观察",
    posts_per_page: int = 20,
) -> Dict[str, Any]:
    manifest = _load_manifest(manifest_path)
    posts = manifest.get("posts", [])
    site_url = site_url.rstrip("/")
    base_path = urlparse(site_url).path.rstrip("/")

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "posts").mkdir(parents=True, exist_ok=True)
    (out / "assets").mkdir(parents=True, exist_ok=True)
    _write_assets(out)

    rendered_posts: List[Dict[str, Any]] = []
    for post in posts:
        markdown_rel = str(post.get("markdown_path", "")).strip()
        markdown_path = _resolve_safe_path(Path(content_root), Path(content_root) / markdown_rel)
        raw_md = markdown_path.read_text(encoding="utf-8") if markdown_path and markdown_path.exists() else ""
        html = _render_markdown(raw_md)
        safe_html = _sanitize_html(html)
        slug = str(post.get("slug", "")).strip()
        post_dir = _resolve_safe_path(out / "posts", out / "posts" / slug)
        if not post_dir:
            continue
        rel_path = f"posts/{slug}/index.html"
        abs_path = post_dir / "index.html"
        abs_path.parent.mkdir(parents=True, exist_ok=True)

        canonical_url = f"{site_url}/{rel_path.replace('index.html', '')}"
        abs_path.write_text(
            _render_post_page(
                site_title=site_title,
                post=post,
                safe_content=safe_html,
                canonical_url=canonical_url,
                base_path=base_path,
            ),
            encoding="utf-8",
        )

        rendered_posts.append(
            {
                **post,
                "canonical_url": canonical_url,
                "html_path": rel_path,
            }
        )

    _render_index_pages(
        out=out,
        site_title=site_title,
        posts=rendered_posts,
        site_url=site_url,
        base_path=base_path,
        posts_per_page=posts_per_page,
    )
    _write_search_index(out, rendered_posts, base_path=base_path)
    _write_rss(out, rendered_posts, site_title=site_title, site_url=site_url)
    _write_sitemap(out, rendered_posts, site_url=site_url)

    return {
        "posts_count": len(rendered_posts),
        "output_dir": str(out),
        "index_pages": max(1, math.ceil(max(1, len(rendered_posts)) / posts_per_page)),
    }


def _load_manifest(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        return {"posts": []}
    data.setdefault("posts", [])
    return data


def _resolve_safe_path(base: Path, target: Path) -> Optional[Path]:
    try:
        base_resolved = base.resolve()
        target_resolved = target.resolve()
        target_resolved.relative_to(base_resolved)
        return target_resolved
    except Exception:
        return None


def _render_markdown(content: str) -> str:
    if md is not None:
        return md.markdown(content, extensions=["extra", "sane_lists"])
    return _render_markdown_fallback(content)


def _render_markdown_fallback(content: str) -> str:
    lines = content.splitlines()
    blocks: List[str] = []
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line.startswith("### "):
            blocks.append(f"<h3>{_render_inline(line[4:])}</h3>")
        elif line.startswith("## "):
            blocks.append(f"<h2>{_render_inline(line[3:])}</h2>")
        elif line.startswith("# "):
            blocks.append(f"<h1>{_render_inline(line[2:])}</h1>")
        else:
            blocks.append(f"<p>{_render_inline(line)}</p>")
    return "\n".join(blocks)


def _render_inline(text: str) -> str:
    parts: List[str] = []
    cursor = 0
    for match in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", text):
        start, end = match.span()
        if start > cursor:
            parts.append(escape(text[cursor:start]))
        label = escape(match.group(1))
        href = escape(match.group(2), quote=True)
        parts.append(f'<a href="{href}">{label}</a>')
        cursor = end
    if cursor < len(text):
        parts.append(escape(text[cursor:]))
    return "".join(parts)


def _sanitize_html(content: str) -> str:
    soup = BeautifulSoup(content, "lxml")
    for tag_name in FORBIDDEN_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    for tag in soup.find_all(True):
        attrs = list(tag.attrs.keys())
        for attr in attrs:
            attr_l = attr.lower()
            if attr_l.startswith("on"):
                del tag.attrs[attr]
                continue
            if attr_l in {"src", "href"}:
                value = str(tag.attrs.get(attr, "")).strip()
                if not _is_safe_url(value):
                    del tag.attrs[attr]

        if tag.name == "a":
            href = tag.attrs.get("href")
            if href:
                parsed = urlparse(href)
                if parsed.scheme in {"http", "https"}:
                    tag.attrs["target"] = "_blank"
                    tag.attrs["rel"] = "noopener noreferrer nofollow"
    return str(soup.body.decode_contents() if soup.body else soup)


def _is_safe_url(url: str) -> bool:
    if not url:
        return False
    parsed = urlparse(url)
    if not parsed.scheme:
        return True
    return parsed.scheme.lower() in SAFE_PROTOCOLS


def _render_post_page(
    *,
    site_title: str,
    post: Dict[str, Any],
    safe_content: str,
    canonical_url: str,
    base_path: str,
) -> str:
    title = escape(post.get("title", "Untitled"))
    date = escape(post.get("date", ""))
    tags = post.get("tags", [])
    tag_html = "".join(f'<span class="tag">{escape(tag)}</span>' for tag in tags)
    summary = escape(post.get("summary", ""))
    item_count = int(post.get("item_count", 0))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} | {escape(site_title)}</title>
  <meta name="description" content="{summary}">
  <meta name="theme-color" content="#1263cc">
  <link rel="canonical" href="{escape(canonical_url)}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;500;600;700&family=Poppins:wght@500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{escape(base_path)}/assets/site.css">
</head>
<body class="page-post">
  <main class="container shell">
    <header class="post-header panel">
      <a class="back-link" href="{escape(base_path)}/">Back to Home</a>
      <p class="kicker">Daily Technical Trend Briefing</p>
      <h1>{title}</h1>
      <p class="meta">{date} · {item_count} items</p>
      <div class="tags">{tag_html}</div>
    </header>
    <article class="content panel prose">{safe_content}</article>
  </main>
</body>
</html>
"""


def _render_index_pages(
    *,
    out: Path,
    site_title: str,
    posts: List[Dict[str, Any]],
    site_url: str,
    base_path: str,
    posts_per_page: int,
) -> None:
    pages = max(1, math.ceil(max(1, len(posts)) / posts_per_page))
    all_tags = sorted({tag for post in posts for tag in post.get("tags", [])})
    for i in range(1, pages + 1):
        start = (i - 1) * posts_per_page
        end = start + posts_per_page
        page_posts = posts[start:end]
        html = _render_index_page(
            site_title=site_title,
            posts=page_posts,
            page=i,
            total_pages=pages,
            site_url=site_url,
            base_path=base_path,
            all_tags=all_tags,
        )
        if i == 1:
            (out / "index.html").write_text(html, encoding="utf-8")
        else:
            page_dir = out / "page" / str(i)
            page_dir.mkdir(parents=True, exist_ok=True)
            (page_dir / "index.html").write_text(html, encoding="utf-8")


def _render_index_page(
    *,
    site_title: str,
    posts: List[Dict[str, Any]],
    page: int,
    total_pages: int,
    site_url: str,
    base_path: str,
    all_tags: List[str],
) -> str:
    visible_posts = len(posts)
    cards = []
    for p in posts:
        link = f"{base_path}/" + p["html_path"].replace("index.html", "")
        tags = " ".join(p.get("tags", []))
        chip_html = "".join(f'<span class="tag">{escape(t)}</span>' for t in p.get("tags", []))
        cards.append(
            f"""
<article class="card panel" data-tags="{escape(tags)}">
  <p class="meta">{escape(p.get("date", ""))} · {int(p.get("item_count", 0))} items</p>
  <h2><a href="{escape(link)}">{escape(p.get("title", "Untitled"))}</a></h2>
  <p class="excerpt">{escape(p.get("summary", ""))}</p>
  <div class="tags">{chip_html}</div>
</article>"""
        )

    page_nav = []
    if page > 1:
        prev_link = f"{base_path}/" if page - 1 == 1 else f"{base_path}/page/{page-1}/"
        page_nav.append(f'<a class="btn" href="{prev_link}">Previous</a>')
    page_nav.append(f"<span class=\"page-indicator\">Page {page} / {total_pages}</span>")
    if page < total_pages:
        page_nav.append(f'<a class="btn" href="{base_path}/page/{page+1}/">Next</a>')

    canonical = f"{site_url}/" if page == 1 else f"{site_url}/page/{page}/"
    tag_options = ['<option value="">All tags</option>'] + [
        f'<option value="{escape(tag)}">{escape(tag)}</option>' for tag in all_tags
    ]
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(site_title)} - Page {page}</title>
  <meta name="theme-color" content="#1263cc">
  <link rel="canonical" href="{escape(canonical)}">
  <link rel="alternate" type="application/rss+xml" title="{escape(site_title)} RSS" href="{escape(base_path)}/rss.xml">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;500;600;700&family=Poppins:wght@500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{escape(base_path)}/assets/site.css">
</head>
<body class="page-index">
  <main class="container shell">
    <header class="site-header panel">
      <p class="kicker">Automated Intelligence Briefing</p>
      <h1>{escape(site_title)}</h1>
      <p class="meta">Daily generated summaries, deployed as static pages.</p>
      <div class="stats">
        <span class="stat"><strong>{total_pages}</strong> pages</span>
        <span class="stat"><strong>{len(all_tags)}</strong> tags</span>
        <span class="stat"><strong>{visible_posts}</strong> posts on this page</span>
      </div>
      <div class="tool-row">
        <input id="searchInput" placeholder="Search title, summary, or tag">
        <select id="tagFilter">
          {''.join(tag_options)}
        </select>
      </div>
    </header>
    <section id="postList" class="grid">
      {''.join(cards) if cards else '<p class="empty">No posts yet.</p>'}
    </section>
    <nav id="pagination" class="pagination">{' '.join(page_nav)}</nav>
  </main>
  <script>window.__INSIGHTHUB_BASE_PATH__ = "{escape(base_path)}";</script>
  <script src="{escape(base_path)}/assets/search.js"></script>
</body>
</html>
"""


def _write_search_index(out: Path, posts: List[Dict[str, Any]], *, base_path: str) -> None:
    search_index = []
    for p in posts:
        search_index.append(
            {
                "title": p.get("title", ""),
                "summary": p.get("summary", ""),
                "tags": p.get("tags", []),
                "date": p.get("date", ""),
                "url": f"{base_path}/" + p["html_path"].replace("index.html", ""),
            }
        )
    (out / "search-index.json").write_text(json.dumps(search_index, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_rss(out: Path, posts: List[Dict[str, Any]], *, site_title: str, site_url: str) -> None:
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = site_title
    ET.SubElement(channel, "link").text = site_url + "/"
    ET.SubElement(channel, "description").text = f"{site_title} feed"
    ET.SubElement(channel, "lastBuildDate").text = _rfc2822(datetime.now(timezone.utc))

    for p in posts[:50]:
        item = ET.SubElement(channel, "item")
        link = p.get("canonical_url") or f"{site_url}/" + p["html_path"].replace("index.html", "")
        ET.SubElement(item, "title").text = p.get("title", "")
        ET.SubElement(item, "link").text = link
        ET.SubElement(item, "guid").text = p.get("id", link)
        ET.SubElement(item, "description").text = p.get("summary", "")
        created = _parse_iso(p.get("created_at"))
        ET.SubElement(item, "pubDate").text = _rfc2822(created)

    ET.ElementTree(rss).write(out / "rss.xml", encoding="utf-8", xml_declaration=True)


def _write_sitemap(out: Path, posts: List[Dict[str, Any]], *, site_url: str) -> None:
    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    _add_sitemap_url(urlset, f"{site_url}/")
    for p in posts:
        _add_sitemap_url(urlset, p.get("canonical_url") or f"{site_url}/" + p["html_path"].replace("index.html", ""))
    ET.ElementTree(urlset).write(out / "sitemap.xml", encoding="utf-8", xml_declaration=True)


def _add_sitemap_url(root: ET.Element, loc: str) -> None:
    url = ET.SubElement(root, "url")
    ET.SubElement(url, "loc").text = loc


def _rfc2822(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")


def _parse_iso(value: Optional[str]) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        return datetime.now(timezone.utc)


def _write_assets(out: Path) -> None:
    css = """
:root{
  --bg:#F8FAFC;
  --fg:#020617;
  --muted:#334155;
  --card:#ffffffee;
  --line:#d4deeb;
  --accent:#0369A1;
  --accent-2:#18a07b;
  --radius:18px;
  --shadow:0 12px 40px rgba(16,36,68,.09);
}
*{box-sizing:border-box}
body{
  margin:0;
  color:var(--fg);
  background:
    radial-gradient(1200px 500px at 10% -15%, #d7e7ff 0%, transparent 60%),
    radial-gradient(900px 450px at 95% 0%, #d3f3e8 0%, transparent 55%),
    var(--bg);
  font-family:"Open Sans","Noto Sans SC","PingFang SC","Microsoft YaHei",sans-serif;
  line-height:1.65;
}
h1,h2,h3{font-family:"Poppins","Noto Sans SC",sans-serif;line-height:1.2;margin:0 0 .6rem}
a{color:var(--accent);text-decoration:none;cursor:pointer}
a:hover{text-decoration:underline}
.container{max-width:1120px;margin:0 auto;padding:26px 18px 44px}
.shell{display:grid;gap:18px}
.panel{
  background:var(--card);
  border:1px solid var(--line);
  border-radius:var(--radius);
  box-shadow:var(--shadow);
  backdrop-filter:blur(7px);
}
.site-header{padding:24px}
.kicker{
  margin:0 0 8px;
  color:var(--accent-2);
  font-size:.84rem;
  letter-spacing:.08em;
  text-transform:uppercase;
  font-weight:700;
}
.meta{margin:0;color:var(--muted);font-size:.94rem}
.stats{display:flex;gap:10px;flex-wrap:wrap;margin:14px 0}
.stat{
  display:inline-flex;
  gap:6px;
  align-items:center;
  padding:6px 10px;
  border-radius:999px;
  font-size:.82rem;
  color:#1d3c63;
  background:#eaf2ff;
}
.tool-row{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px}
.tool-row input,.tool-row select{
  border:1px solid #c6d4e6;
  border-radius:12px;
  padding:12px 13px;
  background:#ffffff;
  color:var(--fg);
  font-size:.95rem;
}
.tool-row input{flex:1;min-width:220px}
.tool-row select{min-width:160px}
.grid{display:grid;grid-template-columns:1fr;gap:12px}
.card{
  padding:18px;
  transform:translateY(0);
  transition:transform .22s ease, box-shadow .22s ease, border-color .22s ease;
}
.card:hover{
  transform:translateY(-2px);
  box-shadow:0 18px 40px rgba(14,35,61,.12);
  border-color:#b7cbe3;
}
.card h2{font-size:1.2rem;margin:0 0 .55rem}
.excerpt{margin:0 0 .75rem;color:#26354c}
.tags{display:flex;gap:7px;flex-wrap:wrap}
.tag{
  display:inline-flex;
  align-items:center;
  padding:3px 10px;
  border-radius:999px;
  font-size:.78rem;
  color:#1f4c86;
  background:#e7f0fe;
}
.pagination{
  display:flex;
  gap:12px;
  align-items:center;
  justify-content:center;
  margin-top:6px;
}
.btn{
  display:inline-flex;
  align-items:center;
  justify-content:center;
  padding:9px 14px;
  border-radius:10px;
  background:#0f59b4;
  color:#fff;
  font-weight:600;
  cursor:pointer;
}
.btn:hover{text-decoration:none;background:#0a4a97}
.page-indicator{color:var(--muted);font-size:.92rem}
.post-header{padding:24px}
.back-link{display:inline-flex;margin-bottom:8px;color:#32547e;font-weight:600}
.content{padding:22px 24px}
.prose p,.prose ul,.prose ol,.prose blockquote{margin:0 0 1rem}
.prose blockquote{
  margin:1rem 0;
  border-left:4px solid #c4d9f5;
  background:#f4f8ff;
  padding:10px 12px;
  color:#274567;
}
.prose pre{
  background:#0e1b2f;
  color:#d8e8ff;
  border-radius:12px;
  overflow:auto;
  padding:14px;
}
.prose code{
  font-family:"JetBrains Mono","Consolas",monospace;
  font-size:.92em;
}
.empty{
  margin:0;
  padding:18px;
  border-radius:14px;
  background:#fff;
  border:1px dashed #bfd0e6;
  color:#506078;
}
a:focus-visible,.btn:focus-visible,input:focus-visible,select:focus-visible{
  outline:none;
  box-shadow:0 0 0 3px rgba(3,105,161,.24);
  border-color:var(--accent);
}
@media (prefers-reduced-motion: reduce){
  *{
    animation:none !important;
    transition:none !important;
    scroll-behavior:auto !important;
  }
}
@media (min-width:860px){
  .grid{grid-template-columns:repeat(2,minmax(0,1fr))}
}
@media (max-width:640px){
  .container{padding:18px 12px 28px}
  .site-header,.post-header,.content{padding:16px}
  .tool-row{flex-direction:column}
  .tool-row input,.tool-row select{width:100%;min-width:0}
  .card h2{font-size:1.08rem}
  .pagination{justify-content:space-between}
}
"""
    js = """
(() => {
  const input = document.getElementById('searchInput');
  const tagFilter = document.getElementById('tagFilter');
  const list = document.getElementById('postList');
  const pagination = document.getElementById('pagination');
  if (!input || !tagFilter || !list) return;

  const defaultHtml = list.innerHTML;
  const defaultPagination = pagination ? pagination.style.display : '';
  let allPosts = [];

  function safe(text) {
    return String(text || '').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function card(post) {
    const safeTitle = safe(post.title);
    const safeDate = safe(post.date);
    const safeSummary = safe(post.summary);
    const safeUrl = post.url || '/';
    const tags = Array.isArray(post.tags)
      ? post.tags.map((t) => `<span class="tag">${safe(t)}</span>`).join('')
      : '';
    return `<article class="card panel"><p class="meta">${safeDate}</p><h2><a href="${safeUrl}">${safeTitle}</a></h2><p class="excerpt">${safeSummary}</p><div class="tags">${tags}</div></article>`;
  }

  function applyFilter() {
    const q = input.value.trim().toLowerCase();
    const tag = tagFilter.value.trim().toLowerCase();
    if (!q && !tag) {
      list.innerHTML = defaultHtml;
      if (pagination) pagination.style.display = defaultPagination;
      return;
    }

    const filtered = allPosts.filter((p) => {
      const hay = `${p.title || ''} ${p.summary || ''} ${(p.tags || []).join(' ')}`.toLowerCase();
      const tagHit = !tag || (p.tags || []).map((x) => String(x).toLowerCase()).includes(tag);
      return tagHit && (!q || hay.includes(q));
    });

    list.innerHTML = filtered.length ? filtered.map(card).join('') : '<p class="empty">No matching posts.</p>';
    if (pagination) pagination.style.display = 'none';
  }

  const basePath = window.__INSIGHTHUB_BASE_PATH__ || '';
  fetch(`${basePath}/search-index.json`)
    .then((r) => (r.ok ? r.json() : []))
    .then((data) => {
      allPosts = Array.isArray(data) ? data : [];
    })
    .catch(() => {
      allPosts = [];
    });

  input.addEventListener('input', applyFilter);
  tagFilter.addEventListener('change', applyFilter);
})();
"""

    (out / "assets" / "site.css").write_text(css.strip() + "\n", encoding="utf-8")
    (out / "assets" / "search.js").write_text(js.strip() + "\n", encoding="utf-8")
