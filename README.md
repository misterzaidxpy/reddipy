<h1 align="center">RedMiner</h1>

<p align="center">
  <strong>Scrape Reddit posts, comments, and user activity. Python SDK + CLI.</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/reddit-miner/"><img src="https://img.shields.io/pypi/v/reddit-miner.svg?style=flat-square&color=blue" alt="PyPI version"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12%20|%203.13-blue.svg?style=flat-square" alt="Python versions"></a>
  <a href="https://github.com/zaidkx37/redminer/actions"><img src="https://img.shields.io/github/actions/workflow/status/zaidkx37/redminer/ci.yml?style=flat-square&label=CI" alt="CI"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/license-MIT-green.svg?style=flat-square" alt="License: MIT"></a>
  <a href="https://pypi.org/project/reddit-miner/"><img src="https://img.shields.io/pypi/dm/reddit-miner?style=flat-square&color=orange&label=downloads" alt="Downloads"></a>
</p>

<p align="center">
  Built on Reddit's public JSON endpoints. Two interfaces: <b>Python SDK</b> and <b>CLI</b>.
</p>

---

## Features

- **Search** Reddit by keyword with sort, time, and subreddit filters
- **Scrape posts** with full comment trees, scores, and metadata
- **Subreddit browsing** with hot, new, top, rising, and controversial sorting
- **User profiles** with post/comment activity filtering
- **Export** to JSON, CSV, or rich console tables
- **Auto-pagination** to collect beyond the 100-per-request limit
- **Proxy rotation** with single proxy, proxy file, and dead proxy cooldown
- **Rate limiting** with configurable delay and exponential backoff
- **Realistic headers** matching a real Chrome browser fingerprint
- **Lightweight** with only `requests` and `rich` as dependencies

---

## Installation

Recommended to **[install using pip](https://pypi.org/project/reddit-miner/)**

```bash
pip install reddit-miner
```

For SOCKS5 proxy support:

```bash
pip install "redminer[socks]"
```

**Requirements:** Python 3.10+

## Authentication

RedMiner requires a `reddit_session` cookie from your browser. This is the only cookie needed.

### Step 1: Get the Cookie

1. Open [reddit.com](https://www.reddit.com) in your browser and log in
2. Open DevTools (`F12`) > **Application** tab > **Cookies** > `https://www.reddit.com`
3. Find the cookie named `reddit_session`
4. Copy its **Value** (a long JWT string starting with `eyJ...`)

### Step 2: Configure (One-Time)

**SDK:**

```python
from redminer import Reddit

Reddit.configure(cookie="eyJhbGciOiJS...")
```

**CLI:**

```bash
redminer configure "eyJhbGciOiJS..."
```

The cookie is saved to `~/.redminer/config.json`. You only need to do this once. All future SDK and CLI calls will use it automatically.

### Auth Management

```python
Reddit.configure(cookie="...")   # save cookie
Reddit.is_configured()           # check if cookie exists (returns True/False)
Reddit.logout()                  # remove stored cookie
```

```bash
redminer configure "cookie"      # save
redminer logout                  # remove
```

### Override Stored Cookie

If you need to use a different cookie for a single session:

```python
reddit = Reddit(cookie="different_cookie_here")
```

```bash
redminer search "python" --cookie "different_cookie_here"
```

---

## Python SDK

### Initialize

```python
from redminer import Reddit

reddit = Reddit()
```

All methods below assume you have already configured authentication.

### Search

Search Reddit for posts matching a keyword.

```python
# Basic search
posts = reddit.search("machine learning", limit=10)
for post in posts:
    print(f"[{post.score}] {post.title}")
    print(f"  r/{post.subreddit} by {post.author}")
```

**Search within a specific subreddit:**

```python
posts = reddit.search("async", subreddit="python", limit=10)
```

**All parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | str | required | Search keywords |
| `limit` | int | 25 | Max results (up to ~1000) |
| `sort` | str | "relevance" | relevance, hot, new, top, comments |
| `time_filter` | str | "all" | day, week, month, year, all |
| `subreddit` | str | None | Scope search to a subreddit |

**Returns:** `list[Post]`

### Scrape a Post

Extract a single post with its full comment tree.

```python
post, comments = reddit.post("https://www.reddit.com/r/python/comments/abc123/title/")

# Post data
print(post.title)
print(post.author)
print(post.score)
print(post.selftext)       # post body
print(post.flair)           # post flair (or None)
print(post.num_comments)
print(post.upvote_ratio)

# Comments
print(f"{len(comments)} top-level comments loaded")

for comment in comments[:5]:
    print(f"[{comment.score}] {comment.author}: {comment.body[:80]}")
    print(f"  depth: {comment.depth}, is_submitter: {comment.is_submitter}")
```

Accepts any Reddit post URL format:

```python
# All of these work
reddit.post("https://www.reddit.com/r/python/comments/abc123/title/")
reddit.post("https://old.reddit.com/r/python/comments/abc123/")
reddit.post("https://reddit.com/r/python/comments/abc123/title")
reddit.post("/r/python/comments/abc123/title/")   # bare permalink
```

**Returns:** `tuple[Post, list[Comment]]`

### Subreddit Posts

Fetch posts from a subreddit with sort and time filters.

```python
# Hot posts (default)
posts = reddit.subreddit("python")

# Top posts this week
posts = reddit.subreddit("python", sort="top", time_filter="week", limit=50)

# New posts
posts = reddit.subreddit("datascience", sort="new", limit=20)

# Rising posts
posts = reddit.subreddit("technology", sort="rising", limit=10)

for post in posts:
    print(f"[{post.score:>5}] {post.title}")
    print(f"        {post.num_comments} comments | r/{post.subreddit}")
```

**All parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | required | Subreddit name (without `r/`) |
| `sort` | str | "hot" | hot, new, top, rising, controversial |
| `time_filter` | str | "all" | day, week, month, year, all (for top/controversial) |
| `limit` | int | 25 | Max posts |

**Returns:** `list[Post]`

### User Activity

Fetch a Reddit user's recent posts and comments.

```python
# All activity
activity = reddit.user("spez", limit=10)

for item in activity:
    print(f"[{item.type}] r/{item.subreddit} ({item.score} pts)")
    if item.type == "post":
        print(f"  {item.title}")
    else:
        print(f"  {item.body[:80]}")
```

**Filter by activity type:**

```python
# Posts only
posts = reddit.user("spez", limit=10, activity_type="posts")

# Comments only
comments = reddit.user("spez", limit=10, activity_type="comments")

# Both (default)
all_activity = reddit.user("spez", limit=10, activity_type="all")
```

**All parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `username` | str | required | Reddit username (without `u/`) |
| `limit` | int | 25 | Max items |
| `sort` | str | "new" | new, hot, top |
| `activity_type` | str | "all" | posts, comments, all |

**Returns:** `list[UserActivity]`

### Export Data

Save scraped data to JSON, CSV, or display as a formatted table.

**JSON:**

```python
from redminer.exporters import JSONExporter

posts = reddit.search("python", limit=20)
JSONExporter().export(posts, "results.json")

# Or print to stdout (no file path)
JSONExporter().export(posts)
```

**CSV:**

```python
from redminer.exporters import CSVExporter

posts = reddit.subreddit("python", sort="top", limit=50)
CSVExporter().export(posts, "posts.csv")
```

**Console table (rich formatted):**

```python
from redminer.exporters import ConsoleExporter

posts = reddit.search("python", limit=10)
ConsoleExporter().export(posts)
```

**Exporting comments:**

```python
post, comments = reddit.post("https://reddit.com/r/python/comments/abc123/title/")

# Comments to JSON (includes post and comment data)
import json
combined = {
    "post": post.to_dict(),
    "comments": [c.to_dict() for c in comments]
}
with open("post_data.json", "w") as f:
    json.dump(combined, f, indent=2)

# Comments to CSV (flattened, with depth/parent_id columns)
CSVExporter().export(comments, "comments.csv")
```

### Proxy Support (SDK)

Route requests through proxies to distribute load or bypass IP restrictions.

**Single proxy:**

```python
reddit = Reddit(proxy="http://1.2.3.4:8080")
```

**Multiple proxies with random rotation:**

```python
reddit = Reddit(proxy_file="proxies.txt")
```

Each request picks a random proxy from the file. Failed proxies are automatically skipped for 60 seconds.

**proxies.txt format:**

```
http://1.2.3.4:8080
http://5.6.7.8:3128
socks5://9.10.11.12:1080
```

SOCKS5 requires: `pip install "redminer[socks]"`

### Data Models

Every scraped item is a Python dataclass with typed fields. All models have a `.to_dict()` method for serialization.

**Post**

| Field | Type | Description |
|-------|------|-------------|
| `id` | str | Reddit post ID |
| `title` | str | Post title |
| `author` | str | Author username |
| `subreddit` | str | Subreddit name |
| `score` | int | Net upvotes |
| `upvote_ratio` | float | Upvote percentage (0.0 - 1.0) |
| `num_comments` | int | Total comment count |
| `created_utc` | datetime | Post creation time (UTC) |
| `selftext` | str | Post body text (empty for link posts) |
| `url` | str | Post URL or linked URL |
| `permalink` | str | Reddit permalink |
| `flair` | str or None | Post flair text |

**Comment**

| Field | Type | Description |
|-------|------|-------------|
| `id` | str | Comment ID |
| `author` | str | Author username |
| `body` | str | Comment text |
| `score` | int | Net upvotes |
| `created_utc` | datetime | Comment creation time (UTC) |
| `parent_id` | str | Parent post/comment ID |
| `depth` | int | Nesting depth (0 = top-level) |
| `is_submitter` | bool | True if comment author is the post author |
| `replies` | list[Comment] | Nested reply comments |

**UserActivity**

| Field | Type | Description |
|-------|------|-------------|
| `type` | str | "post" or "comment" |
| `id` | str | Item ID |
| `author` | str | Username |
| `subreddit` | str | Subreddit name |
| `score` | int | Net upvotes |
| `created_utc` | datetime | Creation time (UTC) |
| `title` | str or None | Post title (None for comments) |
| `body` | str or None | Comment body (None for posts) |
| `permalink` | str | Reddit permalink |

**Serialization:**

```python
post_dict = post.to_dict()
# {"id": "abc123", "title": "...", "created_utc": "2026-07-03T12:00:00+00:00", ...}

# datetime fields become ISO 8601 strings in to_dict()
# Nested comment replies are recursively serialized
```

### Error Handling

RedMiner raises specific exceptions you can catch:

```python
from redminer.exceptions import (
    RedMinerError,           # base exception (catch-all)
    SubredditNotFoundError,  # subreddit is private, banned, or doesn't exist
    PostNotFoundError,       # post URL is invalid or deleted
    UserNotFoundError,       # user is suspended or doesn't exist
    RateLimitError,          # rate limited after 3 retries with backoff
    NetworkError,            # connection failure or timeout
    ProxyError,              # all proxies are dead
)

try:
    posts = reddit.subreddit("nonexistent_sub_12345")
except SubredditNotFoundError:
    print("Subreddit doesn't exist")
except RateLimitError:
    print("Rate limited, try again later or reduce --delay")
except NetworkError:
    print("Connection failed")
```

### Advanced Configuration

```python
reddit = Reddit(
    cookie="override_cookie",          # override stored cookie
    delay=1.0,                         # seconds between requests (default: 2.0)
    proxy="http://1.2.3.4:8080",       # single proxy
    proxy_file="proxies.txt",          # proxy list with random rotation
    user_agent="Custom Agent/1.0",     # custom User-Agent string
    verbose=True,                      # print progress to stderr
)
```

---

## CLI Usage

All CLI commands use stored authentication by default. Run `redminer configure` first.

### Search (CLI)

```bash
# Basic search
redminer search "python"

# With filters
redminer search "machine learning" --limit 20 --sort top --time week

# Search within a subreddit
redminer search "flask" --subreddit python --limit 10
redminer search "hooks" -s react --sort new
```

### Post (CLI)

```bash
# Scrape a post with all comments
redminer post "https://www.reddit.com/r/python/comments/abc123/title/"

# Export to JSON
redminer post "https://reddit.com/r/python/comments/abc123/title/" --export json -o post.json
```

### Subreddit (CLI)

```bash
# Hot posts (default)
redminer subreddit python

# Top posts this month
redminer subreddit datascience --sort top --time month --limit 50

# New posts
redminer subreddit technology --sort new --limit 20

# Rising
redminer subreddit programming --sort rising
```

### User (CLI)

```bash
# All activity
redminer user spez --limit 10

# Posts only
redminer user spez --type posts --limit 20

# Comments only, sorted by top
redminer user spez --type comments --sort top
```

### Export (CLI)

```bash
# JSON file
redminer search "python" --export json -o results.json

# CSV file
redminer subreddit python --export csv -o posts.csv

# Console table (default, no flag needed)
redminer search "python" --limit 5

# Auto-generated filename (omit -o)
redminer search "python" --export json
# Creates: redminer_search_20260703_143000.json
```

### Proxy Support (CLI)

```bash
# Single proxy
redminer search "python" --proxy http://1.2.3.4:8080

# Multiple proxies with random rotation
redminer search "python" --proxy-file proxies.txt
```

**proxies.txt** (one proxy per line):

```
http://1.2.3.4:8080
http://5.6.7.8:3128
socks5://9.10.11.12:1080
```

SOCKS5 requires: `pip install "redminer[socks]"`

### All CLI Flags

**Common flags (available on all commands):**

| Flag | Description | Default |
|------|-------------|---------|
| `--limit` | Max number of results | 25 |
| `--sort` | Sort order | varies by command |
| `--time` / `-t` | Time filter (day/week/month/year/all) | all |
| `--export` | Output format (json/csv/console) | console |
| `--output` / `-o` | Output file path | auto-generated |
| `--cookie` | Override stored reddit_session cookie | stored config |
| `--cookie-file` | Path to JSON file with cookies | - |
| `--proxy` | Single proxy URL | - |
| `--proxy-file` | Path to proxy list file | - |
| `--delay` | Seconds between requests | 2.0 |
| `--user-agent` | Custom User-Agent header | Chrome 149 |
| `--verbose` / `-v` | Show progress and retry info | false |

**Command-specific flags:**

| Command | Flag | Description | Default |
|---------|------|-------------|---------|
| `search` | `--subreddit` / `-s` | Scope search to a subreddit | all of Reddit |
| `user` | `--type` | Filter activity (posts/comments/all) | all |

**Exit codes:**

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error (invalid args, unexpected failure) |
| 2 | Network error (connection failed, rate limited, proxies dead) |
| 3 | Not found (subreddit/post/user doesn't exist) |

---

## Rate Limiting

RedMiner has built-in protections to avoid getting blocked:

- **Request delay:** 2-second gap between requests (configurable with `--delay` or `delay=` parameter)
- **Cooldown on 429:** Automatic exponential backoff (2s, 4s, 8s) when rate-limited by Reddit
- **Max retries:** 3 attempts with increasing wait times before raising an error
- **Dead proxy cooldown:** Failed proxies are skipped for 60 seconds before being retried
- **Realistic headers:** All requests include 14 browser-standard headers (Accept, Sec-CH-UA, Sec-Fetch-*, etc.) matching a real Chrome browser fingerprint

**Tips for staying safe:**

- Keep `delay` at 2.0 or higher for normal use
- Use `--verbose` to see when retries and cooldowns happen
- For large scrapes (500+ items), use proxies to distribute load
- Don't run multiple instances on the same account simultaneously

## Project Structure

```
redminer/
    __init__.py       # Package exports: Reddit, Post, Comment, UserActivity
    sdk.py            # Python SDK (Reddit class)
    cli.py            # CLI entry point (argparse subcommands)
    client.py         # HTTP client (headers, rate limiting, pagination, proxies)
    config.py         # Persistent auth (~/.redminer/config.json)
    models.py         # Post, Comment, UserActivity dataclasses
    exceptions.py     # RedMinerError, SubredditNotFoundError, etc.
    utils.py          # URL parsing, timestamp conversion, filename generation
    scrapers/
        base.py       # BaseScraper abstract class
        search.py     # SearchScraper
        post.py       # PostScraper
        subreddit.py  # SubredditScraper
        user.py       # UserScraper
    exporters/
        base.py       # BaseExporter abstract class
        json_exporter.py
        csv_exporter.py
        console.py    # Rich formatted tables
```

## License

MIT
