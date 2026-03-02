import argparse
import os

from insighthub.site_builder import build_site


def _default_site_url() -> str:
    repo = os.getenv("GITHUB_REPOSITORY", "")
    if "/" in repo:
        owner, name = repo.split("/", 1)
        return f"https://{owner}.github.io/{name}"
    return "https://example.github.io/insighthub"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build static site from InsightHub markdown manifest.")
    parser.add_argument("--manifest", default="output/manifest/index.json")
    parser.add_argument("--content-root", default="output")
    parser.add_argument("--output-dir", default="site")
    parser.add_argument("--site-url", default=_default_site_url())
    parser.add_argument("--site-title", default="InsightHub Daily")
    parser.add_argument("--posts-per-page", type=int, default=20)
    args = parser.parse_args()

    result = build_site(
        manifest_path=args.manifest,
        content_root=args.content_root,
        output_dir=args.output_dir,
        site_url=args.site_url,
        site_title=args.site_title,
        posts_per_page=args.posts_per_page,
    )
    print(
        f"Built site: {result['output_dir']} (posts={result['posts_count']}, pages={result['index_pages']})"
    )


if __name__ == "__main__":
    main()

