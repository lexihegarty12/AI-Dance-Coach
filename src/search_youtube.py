"""Search YouTube for dance videos and save metadata only.

This uses the official YouTube Data API v3. It does not download video or
audio files. Set YOUTUBE_API_KEY in the environment before running it.
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import ssl
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


API_URL = "https://www.googleapis.com/youtube/v3/search"


def _https_context() -> ssl.SSLContext:
    """Use the virtual environment's certifi bundle when available."""
    try:
        import certifi
    except ImportError:
        return ssl.create_default_context()
    return ssl.create_default_context(cafile=certifi.where())


def search_youtube(query: str, api_key: str, max_results: int = 10) -> list[dict]:
    """Return public YouTube video metadata for a search query."""
    params = urllib.parse.urlencode(
        {
            "key": api_key,
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": max(1, min(max_results, 50)),
            "safeSearch": "moderate",
        }
    )
    request = urllib.request.Request(
        f"{API_URL}?{params}",
        headers={"User-Agent": "AI-Dance-Coach/0.1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20, context=_https_context()) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"YouTube API request failed ({exc.code}): {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach YouTube API: {exc.reason}") from exc

    results = []
    for item in payload.get("items", []):
        video_id = item.get("id", {}).get("videoId")
        snippet = item.get("snippet", {})
        if not video_id:
            continue
        results.append(
            {
                "video_id": video_id,
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "title": snippet.get("title", ""),
                "description": snippet.get("description", ""),
                "channel": snippet.get("channelTitle", ""),
                "published_at": snippet.get("publishedAt", ""),
                "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                "source": "youtube",
                "discovered_at": datetime.now(timezone.utc).isoformat(),
            }
        )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Search phrase, e.g. 'beginner ballet tendu tutorial'")
    parser.add_argument("--max-results", type=int, default=10, help="Number of results, from 1 to 50")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("analysis_output/youtube_search.json"),
        help="JSON output path",
    )
    args = parser.parse_args()

    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        try:
            api_key = getpass.getpass("YouTube API key (input hidden): ")
        except (EOFError, KeyboardInterrupt):
            print("\nNo API key supplied.", file=sys.stderr)
            return 2
        if not api_key:
            print("No API key supplied.", file=sys.stderr)
            return 2

    try:
        results = search_youtube(args.query, api_key, args.max_results)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Saved {len(results)} metadata records to {args.output}")
    for index, result in enumerate(results, start=1):
        print(f"{index}. {result['title']} — {result['url']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
