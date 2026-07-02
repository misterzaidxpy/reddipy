# RedMiner

A Python tool for scraping Reddit data. Works as both a **Python SDK** and a **CLI tool**.

Extracts posts, comments, and user activity from Reddit's public JSON endpoints. Exports to JSON, CSV, or formatted console tables.

## Installation

```bash
pip install .
```

Or for development:

```bash
pip install -e ".[dev]"
```

## Quick Start

### 1. Get Your Reddit Session Cookie

RedMiner requires a `reddit_session` cookie from your browser:

1. Open Reddit in your browser and log in
2. Open DevTools (F12) > Application > Cookies > `reddit.com`
3. Find the `reddit_session` cookie and copy its value

### 2. Configure (One-Time Setup)

**SDK:**

```python
from redminer import Reddit

Reddit.configure(cookie="paste_your_reddit_session_value_here")
```

**CLI:**

```bash
redminer configure "paste_your_reddit_session_value_here"
```

This saves the cookie to `~/.redminer/config.json`. You only need to do this once.

## Python SDK

```python
from redminer import Reddit

reddit = Reddit()
```

### Search

```python
posts = reddit.search("machine learning", limit=10)
for post in posts:
    print(f"[{post.score}] {post.title} - r/{post.subreddit}")
```

Search within a specific subreddit:

```python
posts = reddit.search("async", subreddit="python", sort="top", time_filter="month", limit=20)
```

**Parameters:** `query`, `sort` (relevance/hot/new/top/comments), `time_filter` (day/week/month/year/all), `limit`, `subreddit`

### Scrape a Post

```python
post, comments = reddit.post("https://www.reddit.com/r/python/comments/abc123/title/")

print(post.title)
print(post.score)
print(f"{len(comments)} comments")

for comment in comments:
    print(f"  [{comment.score}] {comment.author}: {comment.body[:80]}")
```

### Subreddit Posts

```python
posts = reddit.subreddit("python", sort="top", time_filter="week", limit=50)
for post in posts:
    print(f"{post.title} ({post.num_comments} comments)")
```

**Parameters:** `name`, `sort` (hot/new/top/rising/controversial), `time_filter`, `limit`

### User Activity

```python
activity = reddit.user("spez", limit=10, activity_type="posts")
for item in activity:
    print(f"[{item.type}] {item.title or item.body[:50]}")
```

**Parameters:** `username`, `limit`, `sort` (new/hot/top), `activity_type` (posts/comments/all)

### Export Data

```python
from redminer.exporters import JSONExporter, CSVExporter

posts = reddit.search("python", limit=20)

# Save to JSON
JSONExporter().export(posts, "results.json")

# Save to CSV
CSVExporter().export(posts, "results.csv")
```

### Configuration Options

```python
reddit = Reddit(
    cookie="override_session_cookie",   # Override stored cookie
    delay=1.0,                          # Seconds between requests (default: 2.0)
    proxy="http://1.2.3.4:8080",        # Single proxy
    proxy_file="proxies.txt",           # Proxy list (one per line, random rotation)
    verbose=True,                       # Print progress to stderr
)
```

### Data Models

Every scraped item is returned as a clean dataclass:

**Post:** `id`, `title`, `author`, `subreddit`, `score`, `upvote_ratio`, `num_comments`, `created_utc`, `selftext`, `url`, `permalink`, `flair`

**Comment:** `id`, `author`, `body`, `score`, `created_utc`, `parent_id`, `depth`, `is_submitter`, `replies`

**UserActivity:** `type`, `id`, `author`, `subreddit`, `score`, `created_utc`, `title`, `body`, `permalink`

All models have `.to_dict()` for serialization.

### Auth Management

```python
Reddit.configure(cookie="your_cookie")  # Save cookie
Reddit.is_configured()                  # Check if cookie exists
Reddit.logout()                         # Remove stored cookie
```

## CLI Usage

### Configure

```bash
redminer configure "your_reddit_session_cookie"
redminer logout
```

### Search

```bash
redminer search "python async" --limit 20 --sort top --time week
redminer search "flask" --subreddit python --limit 10
```

### Scrape a Post

```bash
redminer post "https://www.reddit.com/r/python/comments/abc123/title/"
```

### Subreddit

```bash
redminer subreddit python --sort hot --limit 50
redminer subreddit datascience --sort top --time month
```

### User Activity

```bash
redminer user spez --limit 10 --type posts
redminer user spez --type comments --sort top
```

### Export

```bash
# JSON
redminer search "python" --export json -o results.json

# CSV
redminer subreddit python --export csv -o posts.csv

# Console (default)
redminer search "python" --limit 5
```

When `--export json` or `--export csv` is used without `-o`, a file is auto-generated (e.g., `redminer_search_20260703_143000.json`).

### Proxy Support

```bash
# Single proxy
redminer search "python" --proxy http://1.2.3.4:8080

# Multiple proxies with random rotation
redminer search "python" --proxy-file proxies.txt
```

`proxies.txt` format (one per line):

```
http://1.2.3.4:8080
http://5.6.7.8:3128
socks5://9.10.11.12:1080
```

SOCKS5 proxies require: `pip install "redminer[socks]"`

### All CLI Flags

| Flag | Description | Default |
|------|-------------|---------|
| `--limit` | Max results | 25 |
| `--sort` | Sort order | varies |
| `--time` / `-t` | Time filter (day/week/month/year/all) | all |
| `--export` | Output format (json/csv/console) | console |
| `--output` / `-o` | Output file path | auto |
| `--cookie` | Reddit session cookie | stored config |
| `--cookie-file` | JSON file with cookies | - |
| `--proxy` | Single proxy URL | - |
| `--proxy-file` | Proxy list file | - |
| `--delay` | Seconds between requests | 2.0 |
| `--user-agent` | Custom User-Agent | Chrome UA |
| `--verbose` / `-v` | Show progress | false |

## Rate Limiting

RedMiner has built-in rate limiting:

- **Request delay:** 2-second gap between requests (configurable with `--delay`)
- **Cooldown on 429:** Automatic exponential backoff (2s, 4s, 8s) when rate-limited
- **Max retries:** 3 attempts before raising an error
- **Proxy rotation:** Dead proxies are skipped for 60 seconds before retry

## Project Structure

```
redminer/
    __init__.py       # Package init, exports Reddit class
    sdk.py            # Python SDK (Reddit class)
    cli.py            # CLI entry point
    client.py         # HTTP client (rate limiting, pagination, proxies)
    config.py         # Persistent config (~/.redminer/config.json)
    models.py         # Post, Comment, UserActivity dataclasses
    exceptions.py     # Custom exceptions
    utils.py          # URL parsing, helpers
    scrapers/         # Search, Post, Subreddit, User scrapers
    exporters/        # JSON, CSV, Console exporters
```

## License

MIT
