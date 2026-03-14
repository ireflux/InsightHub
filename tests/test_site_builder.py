import json
import os
import sys
import tempfile


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from insighthub.site_builder import build_site


def test_build_site_outputs_pages_and_feeds():
    with tempfile.TemporaryDirectory() as tmp:
        output_root = os.path.join(tmp, "output")
        posts_dir = os.path.join(output_root, "posts")
        manifest_dir = os.path.join(output_root, "manifest")
        os.makedirs(posts_dir, exist_ok=True)
        os.makedirs(manifest_dir, exist_ok=True)

        with open(os.path.join(posts_dir, "2026-03-02-run1.md"), "w", encoding="utf-8") as f:
            f.write("# Test Post\n\nHello <script>alert(1)</script> [ok](https://example.com)")

        manifest = {
            "site_timezone": "Asia/Shanghai",
            "generated_at": "2026-03-02T23:00:00+08:00",
            "posts": [
                {
                    "id": "2026-03-02-run1",
                    "run_id": "run1",
                    "date": "2026-03-02",
                    "title": "Test Post",
                    "slug": "2026-03-02-run1",
                    "markdown_path": "posts/2026-03-02-run1.md",
                    "summary": "Summary",
                    "tags": ["hacker_news"],
                    "sources": ["Hacker News"],
                    "item_count": 1,
                    "is_empty_update": False,
                    "created_at": "2026-03-02T23:00:00+08:00",
                }
            ],
        }
        manifest_path = os.path.join(manifest_dir, "index.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

        site_dir = os.path.join(tmp, "site")
        result = build_site(
            manifest_path=manifest_path,
            content_root=output_root,
            output_dir=site_dir,
            site_url="https://demo.github.io/InsightHub",
            site_title="InsightHub Daily",
            posts_per_page=10,
        )

        assert result["posts_count"] == 1
        assert os.path.exists(os.path.join(site_dir, "index.html"))
        assert os.path.exists(os.path.join(site_dir, "posts", "2026-03-02-run1", "index.html"))
        assert os.path.exists(os.path.join(site_dir, "search-index.json"))
        assert os.path.exists(os.path.join(site_dir, "rss.xml"))
        assert os.path.exists(os.path.join(site_dir, "sitemap.xml"))

        with open(os.path.join(site_dir, "posts", "2026-03-02-run1", "index.html"), "r", encoding="utf-8") as f:
            post_html = f.read()
        assert 'rel="noopener noreferrer nofollow"' in post_html
        assert "<script>" not in post_html
        assert '<link rel="canonical" href="https://demo.github.io/InsightHub/posts/2026-03-02-run1/"' in post_html


def test_build_site_ignores_markdown_path_traversal():
    with tempfile.TemporaryDirectory() as tmp:
        output_root = os.path.join(tmp, "output")
        posts_dir = os.path.join(output_root, "posts")
        manifest_dir = os.path.join(output_root, "manifest")
        os.makedirs(posts_dir, exist_ok=True)
        os.makedirs(manifest_dir, exist_ok=True)

        secret_path = os.path.join(tmp, "secret.txt")
        with open(secret_path, "w", encoding="utf-8") as f:
            f.write("SECRET_CONTENT")

        manifest = {
            "site_timezone": "Asia/Shanghai",
            "generated_at": "2026-03-02T23:00:00+08:00",
            "posts": [
                {
                    "id": "2026-03-02-run2",
                    "run_id": "run2",
                    "date": "2026-03-02",
                    "title": "Traversal",
                    "slug": "2026-03-02-run2",
                    "markdown_path": "../secret.txt",
                    "summary": "Summary",
                    "tags": [],
                    "sources": [],
                    "item_count": 0,
                    "is_empty_update": False,
                    "created_at": "2026-03-02T23:00:00+08:00",
                }
            ],
        }
        manifest_path = os.path.join(manifest_dir, "index.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

        site_dir = os.path.join(tmp, "site")
        build_site(
            manifest_path=manifest_path,
            content_root=output_root,
            output_dir=site_dir,
            site_url="https://demo.github.io/InsightHub",
            site_title="InsightHub Daily",
            posts_per_page=10,
        )

        post_path = os.path.join(site_dir, "posts", "2026-03-02-run2", "index.html")
        with open(post_path, "r", encoding="utf-8") as f:
            post_html = f.read()
        assert "SECRET_CONTENT" not in post_html
