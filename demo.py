"""RedMiner SDK Demo - Interactive walkthrough of all features."""

from reddipy import Reddit
from reddipy.exporters import JSONExporter, CSVExporter, ConsoleExporter
import os

DIVIDER = "=" * 60


def wait():
    input("\n  Press Enter to continue...")
    print()


def header(title):
    print(f"\n{DIVIDER}")
    print(f"  {title}")
    print(DIVIDER)


def main():
    print(DIVIDER)
    print("  RedMiner SDK Demo")
    print("  Interactive walkthrough of all features")
    print(DIVIDER)

    # ----------------------------------------------------------------
    # 1. Configuration
    # ----------------------------------------------------------------
    header("1. Authentication Setup")

    print("  Checking stored config...")
    configured = Reddit.is_configured()
    print(f"  Already configured: {configured}")

    if not configured:
        print("\n  No cookie found. You need to configure first.")
        cookie = input("  Paste your reddit_session cookie: ").strip()
        if not cookie:
            print("  No cookie provided. Exiting.")
            return
        Reddit.configure(cookie=cookie)
        print("  Cookie saved to ~/.reddipy/config.json")
    else:
        print("  Using stored cookie from ~/.reddipy/config.json")

    reddit = Reddit(delay=1.0)
    print("\n  Reddit client initialized (1s delay between requests)")

    wait()

    # ----------------------------------------------------------------
    # 2. Search
    # ----------------------------------------------------------------
    header("2. Search Reddit")

    query = "python"
    print(f'  Searching for "{query}" (5 results)...\n')
    posts = reddit.search(query, limit=5)

    for i, p in enumerate(posts, 1):
        print(f"  {i}. [{p.score:>5} pts] {p.title[:65]}")
        print(f"     r/{p.subreddit} by {p.author} | {p.num_comments} comments")
        print()

    wait()

    # ----------------------------------------------------------------
    # 3. Scoped Search
    # ----------------------------------------------------------------
    header("3. Scoped Search (within a subreddit)")

    print('  Searching "async" in r/python, sorted by top, past year...\n')
    results = reddit.search("async", subreddit="python", sort="top",
                            time_filter="year", limit=5)

    for i, p in enumerate(results, 1):
        print(f"  {i}. [{p.score:>5} pts] {p.title[:65]}")
        print()

    wait()

    # ----------------------------------------------------------------
    # 4. Subreddit Scraping
    # ----------------------------------------------------------------
    header("4. Subreddit Scraping")

    print("  Fetching top 5 posts from r/technology this week...\n")
    posts = reddit.subreddit("technology", sort="top", time_filter="week", limit=5)

    for i, p in enumerate(posts, 1):
        print(f"  {i}. [{p.score:>6} pts] {p.title[:60]}")
        print(f"     {p.num_comments} comments | ratio: {p.upvote_ratio}")
        print()

    wait()

    # ----------------------------------------------------------------
    # 5. Post + Comments
    # ----------------------------------------------------------------
    header("5. Scrape a Post with Comments")

    url = f"https://www.reddit.com{posts[0].permalink}"
    print(f"  Scraping: {posts[0].title[:55]}...\n")
    post, comments = reddit.post(url)

    print(f"  Title:    {post.title}")
    print(f"  Author:   {post.author}")
    print(f"  Score:    {post.score}")
    print(f"  Comments: {post.num_comments}")
    print(f"  Flair:    {post.flair or 'None'}")

    body_preview = post.selftext.replace("\n", " ")[:100] if post.selftext else "(no body)"
    print(f"  Body:     {body_preview}...")

    print(f"\n  Top 5 comments (of {len(comments)} loaded):\n")
    for c in comments[:5]:
        body = c.body.replace("\n", " ")[:55]
        print(f"    [{c.score:>4}] {c.author}: {body}")

    wait()

    # ----------------------------------------------------------------
    # 6. User Activity
    # ----------------------------------------------------------------
    header("6. User Activity")

    username = "spez"
    print(f"  Fetching activity for u/{username}...\n")
    activity = reddit.user(username, limit=5)

    for item in activity:
        content = (item.title or item.body or "").replace("\n", " ")[:55]
        print(f"  [{item.type:>7}] [{item.score:>5}] r/{item.subreddit}")
        print(f"           {content}")
        print()

    wait()

    # ----------------------------------------------------------------
    # 7. User Activity Filtered
    # ----------------------------------------------------------------
    header("7. Filtered User Activity (posts only)")

    print(f"  Fetching only posts from u/{username}...\n")
    user_posts = reddit.user(username, limit=5, activity_type="posts")

    for item in user_posts:
        print(f"  [{item.score:>5}] {item.title[:65]}")
        print(f"         r/{item.subreddit}")
        print()

    wait()

    # ----------------------------------------------------------------
    # 8. Console Table Export
    # ----------------------------------------------------------------
    header("8. Console Table Export (rich)")

    print("  Displaying search results as a rich table:\n")
    table_data = reddit.search("machine learning", limit=5)
    ConsoleExporter().export(table_data)

    wait()

    # ----------------------------------------------------------------
    # 9. JSON Export
    # ----------------------------------------------------------------
    header("9. JSON Export")

    json_path = os.path.join(os.path.dirname(__file__), "demo_output.json")
    print(f"  Exporting 3 posts to {json_path}...\n")
    export_data = reddit.search("artificial intelligence", limit=3)
    JSONExporter().export(export_data, json_path)

    import json
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    print(f"  Saved {len(data)} posts. Preview:\n")
    print(json.dumps(data[0], indent=2)[:300])
    print("  ...")

    os.remove(json_path)
    print(f"\n  (cleaned up {json_path})")

    wait()

    # ----------------------------------------------------------------
    # 10. CSV Export
    # ----------------------------------------------------------------
    header("10. CSV Export")

    csv_path = os.path.join(os.path.dirname(__file__), "demo_output.csv")
    print(f"  Exporting 3 posts to {csv_path}...\n")
    CSVExporter().export(export_data, csv_path)

    import csv
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"  Saved {len(rows)} rows")
    print(f"  Columns: {', '.join(list(rows[0].keys())[:6])}...")
    print(f"\n  First row preview:")
    print(f"    Title: {rows[0]['title'][:60]}")
    print(f"    Score: {rows[0]['score']}")
    print(f"    Author: {rows[0]['author']}")

    os.remove(csv_path)
    print(f"\n  (cleaned up {csv_path})")

    wait()

    # ----------------------------------------------------------------
    # 11. Data Models
    # ----------------------------------------------------------------
    header("11. Data Models & to_dict()")

    print("  Post fields:")
    p = export_data[0]
    d = p.to_dict()
    for key, val in d.items():
        val_str = str(val)[:50]
        print(f"    {key:>15}: {val_str}")

    wait()

    # ----------------------------------------------------------------
    # 12. Auth Lifecycle
    # ----------------------------------------------------------------
    header("12. Auth Lifecycle")

    print(f"  is_configured(): {Reddit.is_configured()}")
    print("  Calling Reddit.logout()...")
    Reddit.logout()
    print(f"  is_configured(): {Reddit.is_configured()}")
    print("  Re-configuring with stored cookie...")

    config_path = os.path.join(os.path.expanduser("~"), ".reddipy", "config.json")
    print(f"  Config location: {config_path}")

    # Re-configure so user doesn't lose their cookie
    Reddit.configure(cookie=reddit._client._cookies.get("reddit_session", ""))
    print(f"  is_configured(): {Reddit.is_configured()}")

    # ----------------------------------------------------------------
    # Done
    # ----------------------------------------------------------------
    print(f"\n{DIVIDER}")
    print("  Demo Complete!")
    print(f"{DIVIDER}")
    print()
    print("  All 12 features tested successfully.")
    print()
    print("  SDK usage summary:")
    print("    from reddipy import Reddit")
    print("    reddit = Reddit()")
    print("    reddit.search(query, limit, sort, time_filter, subreddit)")
    print("    reddit.post(url)")
    print("    reddit.subreddit(name, sort, time_filter, limit)")
    print("    reddit.user(username, limit, sort, activity_type)")
    print()


if __name__ == "__main__":
    main()
