"""
Social media scraping tools using httpx + BeautifulSoup.
Compatible with Python 3.12+
"""

import asyncio
import json
import re
from urllib.parse import urljoin, urlparse, quote
from bs4 import BeautifulSoup
import httpx
from ai_query import tool, Field

# HTTP client with browser-like headers
scraper_client = httpx.AsyncClient(
    timeout=30.0,
    follow_redirects=True,
    headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
)


# =============================================================================
# TWITTER/X SCRAPING
# =============================================================================

@tool(description="Scrape a Twitter/X user's profile using Nitter (public Twitter frontend). Returns bio, stats, and recent tweets with links.")
async def scrape_twitter_profile(
    username: str = Field(description="Twitter/X username (without @)"),
    max_tweets: int = Field(description="Maximum number of tweets to fetch (1-50)", default=20)
) -> str:
    """
    Scrapes a Twitter/X profile via Nitter instances (privacy-respecting Twitter frontend).
    """
    username = username.lstrip("@").strip()

    # List of Nitter instances to try
    nitter_instances = [
        "https://nitter.poast.org",
        "https://nitter.privacydev.net",
        "https://nitter.woodland.cafe",
        "https://nitter.esmailelbob.xyz",
    ]

    for instance in nitter_instances:
        try:
            url = f"{instance}/{username}"
            response = await scraper_client.get(url)

            if response.status_code == 404:
                return f"Twitter user @{username} not found."

            if response.status_code != 200:
                continue  # Try next instance

            soup = BeautifulSoup(response.text, "lxml")

            # Check if profile exists
            error = soup.select_one(".error-panel")
            if error:
                return f"Twitter user @{username} not found or account is suspended."

            result = f"**🐦 Twitter Profile: @{username}**\n"
            result += f"🔗 Profile: [x.com/{username}](https://x.com/{username})\n\n"

            # Extract profile info
            profile = soup.select_one(".profile-card")
            if profile:
                # Display name
                name = profile.select_one(".profile-card-fullname")
                if name:
                    result += f"**Name:** {name.get_text(strip=True)}\n"

                # Bio
                bio = profile.select_one(".profile-bio")
                if bio:
                    result += f"**Bio:** {bio.get_text(strip=True)}\n"

                # Location
                location = profile.select_one(".profile-location")
                if location:
                    result += f"**Location:** {location.get_text(strip=True)}\n"

                # Website
                website = profile.select_one(".profile-website a")
                if website:
                    href = website.get("href", "")
                    result += f"**Website:** [{href}]({href})\n"

                # Stats
                stats = profile.select(".profile-stat-num")
                stat_labels = profile.select(".profile-stat-header")
                if stats and stat_labels:
                    result += "\n**Stats:**\n"
                    for stat, label in zip(stats, stat_labels):
                        result += f"  - {label.get_text(strip=True)}: {stat.get_text(strip=True)}\n"

            result += "\n"

            # Extract tweets
            tweets = soup.select(".timeline-item")[:max_tweets]
            if tweets:
                result += f"**Recent Tweets ({len(tweets)} found):**\n\n"

                for i, tweet in enumerate(tweets, 1):
                    # Tweet content
                    content_elem = tweet.select_one(".tweet-content")
                    if not content_elem:
                        continue

                    content = content_elem.get_text(strip=True)[:300]

                    # Tweet link
                    tweet_link = tweet.select_one(".tweet-link")
                    tweet_url = ""
                    if tweet_link:
                        tweet_path = tweet_link.get("href", "")
                        tweet_url = f"https://x.com{tweet_path}"

                    result += f"**{i}.** {content}\n"
                    if tweet_url:
                        result += f"   🔗 [{tweet_url}]({tweet_url})\n"

                    # Stats
                    stats_elem = tweet.select_one(".tweet-stats")
                    if stats_elem:
                        comments = stats_elem.select_one(".icon-comment + span")
                        retweets = stats_elem.select_one(".icon-retweet + span")
                        likes = stats_elem.select_one(".icon-heart + span")

                        stat_parts = []
                        if comments:
                            stat_parts.append(f"💬 {comments.get_text(strip=True)}")
                        if retweets:
                            stat_parts.append(f"🔄 {retweets.get_text(strip=True)}")
                        if likes:
                            stat_parts.append(f"❤️ {likes.get_text(strip=True)}")

                        if stat_parts:
                            result += f"   {' | '.join(stat_parts)}\n"

                    # Date
                    date_elem = tweet.select_one(".tweet-date a")
                    if date_elem:
                        result += f"   📅 {date_elem.get_text(strip=True)}\n"

                    # Extract links from tweet
                    links = content_elem.select("a")
                    for link in links[:3]:
                        href = link.get("href", "")
                        if href.startswith("http") and "nitter" not in href:
                            result += f"   📎 [{href}]({href})\n"

                    result += "\n"

            return result

        except Exception as e:
            continue  # Try next instance

    return f"Error: Could not scrape @{username}. All Nitter instances unavailable. Try using search_social_profile instead."


@tool(description="Search Twitter/X for tweets about a topic or person using Nitter.")
async def scrape_twitter_search(
    query: str = Field(description="Search query"),
    max_tweets: int = Field(description="Maximum number of tweets to fetch (1-30)", default=20)
) -> str:
    """
    Searches Twitter via Nitter instances.
    """
    nitter_instances = [
        "https://nitter.poast.org",
        "https://nitter.privacydev.net",
        "https://nitter.woodland.cafe",
    ]

    encoded_query = quote(query)

    for instance in nitter_instances:
        try:
            url = f"{instance}/search?f=tweets&q={encoded_query}"
            response = await scraper_client.get(url)

            if response.status_code != 200:
                continue

            soup = BeautifulSoup(response.text, "lxml")

            result = f"**🔍 Twitter Search: '{query}'**\n\n"

            tweets = soup.select(".timeline-item")[:max_tweets]

            if not tweets:
                return f"No tweets found for query: '{query}'"

            result += f"**Found {len(tweets)} tweets:**\n\n"

            for i, tweet in enumerate(tweets, 1):
                # Username
                username_elem = tweet.select_one(".username")
                username = username_elem.get_text(strip=True) if username_elem else "unknown"

                # Content
                content_elem = tweet.select_one(".tweet-content")
                if not content_elem:
                    continue
                content = content_elem.get_text(strip=True)[:250]

                # Tweet URL
                tweet_link = tweet.select_one(".tweet-link")
                tweet_url = ""
                if tweet_link:
                    tweet_path = tweet_link.get("href", "")
                    tweet_url = f"https://x.com{tweet_path}"

                result += f"**{i}. {username}:** {content}\n"
                if tweet_url:
                    result += f"   🔗 [{tweet_url}]({tweet_url})\n"

                # Date
                date_elem = tweet.select_one(".tweet-date a")
                if date_elem:
                    result += f"   📅 {date_elem.get_text(strip=True)}\n"

                result += "\n"

            return result

        except Exception:
            continue

    return f"Error: Could not search Twitter. All Nitter instances unavailable."


# =============================================================================
# REDDIT SCRAPING
# =============================================================================

@tool(description="Scrape a Reddit user's profile for posts and comments with links.")
async def scrape_reddit_user(
    username: str = Field(description="Reddit username (without u/)"),
    max_items: int = Field(description="Maximum number of posts/comments to fetch (1-50)", default=20)
) -> str:
    """
    Scrapes a Reddit user's profile using old.reddit.com.
    """
    username = username.lstrip("u/").strip()

    try:
        # Use old Reddit which is easier to scrape
        url = f"https://old.reddit.com/user/{username}"
        response = await scraper_client.get(url)

        if response.status_code == 404:
            return f"Reddit user u/{username} not found."

        if response.status_code != 200:
            return f"Error fetching Reddit profile: HTTP {response.status_code}"

        soup = BeautifulSoup(response.text, "lxml")

        result = f"**👽 Reddit Profile: u/{username}**\n"
        result += f"🔗 Profile: [reddit.com/user/{username}](https://reddit.com/user/{username})\n\n"

        # Get karma from sidebar
        karma_elem = soup.select_one(".karma")
        if karma_elem:
            result += f"**Karma:** {karma_elem.get_text(strip=True)}\n\n"

        # Get posts/comments
        items = soup.select(".thing")[:max_items]

        if not items:
            result += "No recent activity found.\n"
            return result

        result += f"**Recent Activity ({len(items)} items):**\n\n"

        for i, item in enumerate(items, 1):
            # Determine if post or comment
            is_comment = "comment" in item.get("class", [])

            # Title/content
            if is_comment:
                content_elem = item.select_one(".md")
                content = content_elem.get_text(strip=True)[:200] if content_elem else ""
                result += f"**{i}. [COMMENT]** {content}...\n"
            else:
                title_elem = item.select_one("a.title")
                title = title_elem.get_text(strip=True)[:200] if title_elem else "No title"
                result += f"**{i}. [POST]** {title}\n"

            # Subreddit
            subreddit_elem = item.select_one(".subreddit")
            if subreddit_elem:
                sub = subreddit_elem.get_text(strip=True)
                result += f"   📍 {sub}\n"

            # Link to item
            permalink = item.get("data-permalink", "")
            if permalink:
                full_url = f"https://reddit.com{permalink}"
                result += f"   🔗 [{full_url}]({full_url})\n"

            # Score
            score_elem = item.select_one(".score.unvoted")
            if score_elem:
                score = score_elem.get("title", score_elem.get_text(strip=True))
                result += f"   ⬆️ {score} points\n"

            # Time
            time_elem = item.select_one("time")
            if time_elem:
                result += f"   📅 {time_elem.get('title', time_elem.get_text(strip=True))}\n"

            result += "\n"

        return result

    except Exception as e:
        return f"Error scraping u/{username}: {str(e)}"


@tool(description="Search Reddit for posts matching a query. Returns posts with links.")
async def scrape_reddit_search(
    query: str = Field(description="Search query"),
    subreddit: str = Field(description="Limit to specific subreddit (optional, without r/)", default=""),
    max_posts: int = Field(description="Maximum number of posts to fetch (1-30)", default=20)
) -> str:
    """
    Searches Reddit using old.reddit.com.
    """
    try:
        encoded_query = quote(query)

        if subreddit:
            subreddit = subreddit.lstrip("r/")
            url = f"https://old.reddit.com/r/{subreddit}/search?q={encoded_query}&restrict_sr=on"
        else:
            url = f"https://old.reddit.com/search?q={encoded_query}"

        response = await scraper_client.get(url)

        if response.status_code != 200:
            return f"Error searching Reddit: HTTP {response.status_code}"

        soup = BeautifulSoup(response.text, "lxml")

        result = f"**🔍 Reddit Search: '{query}'**"
        if subreddit:
            result += f" in [r/{subreddit}](https://reddit.com/r/{subreddit})"
        result += "\n\n"

        posts = soup.select(".search-result, .thing")[:max_posts]

        if not posts:
            return f"No posts found for query: '{query}'"

        result += f"**Found {len(posts)} posts:**\n\n"

        for i, post in enumerate(posts, 1):
            # Title
            title_elem = post.select_one("a.search-title, a.title")
            title = title_elem.get_text(strip=True)[:200] if title_elem else "No title"

            result += f"**{i}.** {title}\n"

            # Subreddit
            sub_elem = post.select_one(".search-subreddit-link, .subreddit")
            if sub_elem:
                result += f"   📍 {sub_elem.get_text(strip=True)}\n"

            # Link
            if title_elem:
                href = title_elem.get("href", "")
                if href.startswith("/"):
                    href = f"https://reddit.com{href}"
                result += f"   🔗 [{href}]({href})\n"

            # Score and comments
            score_elem = post.select_one(".search-score, .score")
            if score_elem:
                result += f"   ⬆️ {score_elem.get_text(strip=True)}\n"

            comments_elem = post.select_one(".search-comments, .comments")
            if comments_elem:
                result += f"   💬 {comments_elem.get_text(strip=True)}\n"

            # Author
            author_elem = post.select_one(".search-author a, .author")
            if author_elem:
                result += f"   👤 u/{author_elem.get_text(strip=True)}\n"

            result += "\n"

        return result

    except Exception as e:
        return f"Error searching Reddit: {str(e)}"


# =============================================================================
# GITHUB SCRAPING
# =============================================================================

@tool(description="Scrape a GitHub user's profile for repos, contributions, and links.")
async def scrape_github_profile(
    username: str = Field(description="GitHub username"),
    max_repos: int = Field(description="Maximum number of repos to fetch (1-30)", default=10)
) -> str:
    """
    Scrapes a GitHub user's profile page.
    """
    username = username.strip()

    try:
        url = f"https://github.com/{username}"
        response = await scraper_client.get(url)

        if response.status_code == 404:
            return f"GitHub user {username} not found."

        if response.status_code != 200:
            return f"Error fetching GitHub profile: HTTP {response.status_code}"

        soup = BeautifulSoup(response.text, "lxml")

        result = f"**🐙 GitHub Profile: {username}**\n"
        result += f"🔗 Profile: [github.com/{username}](https://github.com/{username})\n\n"

        # Name
        name_elem = soup.select_one(".p-name, .vcard-fullname")
        if name_elem:
            result += f"**Name:** {name_elem.get_text(strip=True)}\n"

        # Bio
        bio_elem = soup.select_one(".p-note, .user-profile-bio")
        if bio_elem:
            result += f"**Bio:** {bio_elem.get_text(strip=True)}\n"

        # Location
        location_elem = soup.select_one("[itemprop='homeLocation']")
        if location_elem:
            result += f"**Location:** {location_elem.get_text(strip=True)}\n"

        # Company
        company_elem = soup.select_one("[itemprop='worksFor']")
        if company_elem:
            result += f"**Company:** {company_elem.get_text(strip=True)}\n"

        # Website
        website_elem = soup.select_one("[itemprop='url'] a, .Link--primary[href^='http']")
        if website_elem:
            href = website_elem.get("href", "")
            if href and not "github.com" in href:
                result += f"**Website:** [{href}]({href})\n"

        # Social links
        social_links = soup.select(".vcard-details a[href*='twitter'], .vcard-details a[href*='linkedin']")
        for link in social_links:
            href = link.get("href", "")
            text = link.get_text(strip=True)
            result += f"**Social:** [{text}]({href})\n"

        # Stats (followers, following, repos)
        stats = soup.select(".js-profile-editable-area a span.text-bold, .flex-order-1 span")
        stat_labels = ["Followers", "Following", "Repos"]
        for stat, label in zip(stats[:3], stat_labels):
            result += f"**{label}:** {stat.get_text(strip=True)}\n"

        result += "\n"

        # Pinned repos
        pinned = soup.select(".pinned-item-list-item")[:max_repos]
        if pinned:
            result += f"**Pinned Repositories ({len(pinned)}):**\n\n"
            for i, repo in enumerate(pinned, 1):
                name_elem = repo.select_one(".repo")
                if name_elem:
                    repo_name = name_elem.get_text(strip=True)
                    repo_url = f"https://github.com/{username}/{repo_name}"
                    result += f"{i}. **[{repo_name}]({repo_url})**\n"

                    desc_elem = repo.select_one(".pinned-item-desc")
                    if desc_elem:
                        result += f"   {desc_elem.get_text(strip=True)[:150]}\n"

                    lang_elem = repo.select_one("[itemprop='programmingLanguage']")
                    if lang_elem:
                        result += f"   💻 {lang_elem.get_text(strip=True)}\n"

                    stars_elem = repo.select_one("a[href*='stargazers']")
                    if stars_elem:
                        result += f"   ⭐ {stars_elem.get_text(strip=True)}\n"

                    result += "\n"

        # Recent repos if no pinned
        if not pinned:
            repos_url = f"https://github.com/{username}?tab=repositories"
            repos_response = await scraper_client.get(repos_url)
            if repos_response.status_code == 200:
                repos_soup = BeautifulSoup(repos_response.text, "lxml")
                repos = repos_soup.select("#user-repositories-list li")[:max_repos]

                if repos:
                    result += f"**Repositories ({len(repos)}):**\n\n"
                    for i, repo in enumerate(repos, 1):
                        name_elem = repo.select_one("a[itemprop='name codeRepository']")
                        if name_elem:
                            repo_name = name_elem.get_text(strip=True)
                            repo_url = f"https://github.com{name_elem.get('href', '')}"
                            result += f"{i}. **[{repo_name}]({repo_url})**\n"

                            desc_elem = repo.select_one("[itemprop='description']")
                            if desc_elem:
                                result += f"   {desc_elem.get_text(strip=True)[:150]}\n"

                            result += "\n"

        return result

    except Exception as e:
        return f"Error scraping GitHub profile: {str(e)}"


# =============================================================================
# LINKEDIN SCRAPING (Public profiles only)
# =============================================================================

@tool(description="Attempt to scrape a LinkedIn public profile. Limited due to LinkedIn restrictions.")
async def scrape_linkedin_profile(
    profile_url: str = Field(description="Full LinkedIn profile URL (e.g., https://linkedin.com/in/username)")
) -> str:
    """
    Attempts to scrape a LinkedIn public profile.
    Note: LinkedIn heavily restricts scraping, so results may be limited.
    """
    try:
        if "linkedin.com/in/" not in profile_url:
            return "Invalid LinkedIn URL. Please provide a full profile URL like https://linkedin.com/in/username"

        response = await scraper_client.get(profile_url)

        if response.status_code == 999:
            return f"LinkedIn blocked the request. Use search_social_profile to find LinkedIn profiles via web search instead.\n\n🔗 Profile URL: [{profile_url}]({profile_url})"

        if response.status_code != 200:
            return f"Could not access LinkedIn profile (HTTP {response.status_code}). LinkedIn may require login.\n\n🔗 Profile URL: [{profile_url}]({profile_url})"

        soup = BeautifulSoup(response.text, "lxml")

        result = f"**💼 LinkedIn Profile**\n"
        result += f"🔗 Profile: [{profile_url}]({profile_url})\n\n"

        # Try to extract basic info from meta tags
        og_title = soup.select_one('meta[property="og:title"]')
        if og_title:
            result += f"**Name:** {og_title.get('content', '')}\n"

        og_desc = soup.select_one('meta[property="og:description"]')
        if og_desc:
            result += f"**Headline:** {og_desc.get('content', '')}\n"

        # Try to get any visible text
        main_content = soup.select_one(".core-section-container, .pv-top-card")
        if main_content:
            text = main_content.get_text(strip=True)[:500]
            result += f"\n**Profile Content:**\n{text}\n"

        result += "\n**Note:** LinkedIn restricts scraping. For full profile data, use search_social_profile or visit the link directly."

        return result

    except Exception as e:
        return f"Error accessing LinkedIn: {str(e)}\n\n🔗 Profile URL: [{profile_url}]({profile_url})"


# =============================================================================
# YOUTUBE SCRAPING
# =============================================================================

@tool(description="Scrape a YouTube channel for info and recent videos with links.")
async def scrape_youtube_channel(
    channel_url: str = Field(description="YouTube channel URL (e.g., https://youtube.com/@username or https://youtube.com/c/channelname)"),
    max_videos: int = Field(description="Maximum number of videos to fetch (1-20)", default=10)
) -> str:
    """
    Scrapes a YouTube channel page for info and videos.
    """
    try:
        # Ensure we're hitting the videos tab
        if "/videos" not in channel_url:
            if channel_url.endswith("/"):
                channel_url = channel_url + "videos"
            else:
                channel_url = channel_url + "/videos"

        response = await scraper_client.get(channel_url)

        if response.status_code != 200:
            return f"Error fetching YouTube channel: HTTP {response.status_code}"

        soup = BeautifulSoup(response.text, "lxml")

        result = f"**📺 YouTube Channel**\n"
        result += f"🔗 Channel: [{channel_url}]({channel_url})\n\n"

        # Try to extract channel name from meta
        og_title = soup.select_one('meta[property="og:title"]')
        if og_title:
            result += f"**Channel:** {og_title.get('content', '')}\n"

        og_desc = soup.select_one('meta[property="og:description"]')
        if og_desc:
            result += f"**Description:** {og_desc.get('content', '')[:300]}\n"

        # Try to find subscriber count
        sub_text = soup.find(string=re.compile(r'\d+\.?\d*[KMB]?\s*subscribers', re.I))
        if sub_text:
            result += f"**Subscribers:** {sub_text.strip()}\n"

        result += "\n"

        # YouTube uses heavy JavaScript, so direct scraping is limited
        # We can try to extract video IDs from the page source
        video_ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', response.text)
        unique_ids = list(dict.fromkeys(video_ids))[:max_videos]  # Remove duplicates, keep order

        if unique_ids:
            result += f"**Recent Videos ({len(unique_ids)} found):**\n\n"
            for i, vid_id in enumerate(unique_ids, 1):
                video_url = f"https://youtube.com/watch?v={vid_id}"
                result += f"{i}. 🔗 [{video_url}]({video_url})\n"
        else:
            result += "**Note:** Could not extract video list. YouTube requires JavaScript for full rendering.\n"

        return result

    except Exception as e:
        return f"Error scraping YouTube channel: {str(e)}"


# =============================================================================
# MEDIUM/SUBSTACK SCRAPING
# =============================================================================

@tool(description="Scrape a Medium author profile for articles with links.")
async def scrape_medium_profile(
    username: str = Field(description="Medium username (e.g., @username or just username)"),
    max_articles: int = Field(description="Maximum number of articles to fetch (1-20)", default=10)
) -> str:
    """
    Scrapes a Medium author's profile for articles.
    """
    username = username.lstrip("@").strip()

    try:
        url = f"https://medium.com/@{username}"
        response = await scraper_client.get(url)

        if response.status_code == 404:
            return f"Medium user @{username} not found."

        if response.status_code != 200:
            return f"Error fetching Medium profile: HTTP {response.status_code}"

        soup = BeautifulSoup(response.text, "lxml")

        result = f"**📝 Medium Profile: @{username}**\n"
        result += f"🔗 Profile: [medium.com/@{username}](https://medium.com/@{username})\n\n"

        # Extract name from meta
        og_title = soup.select_one('meta[property="og:title"]')
        if og_title:
            result += f"**Name:** {og_title.get('content', '').replace(' – Medium', '')}\n"

        og_desc = soup.select_one('meta[property="og:description"]')
        if og_desc:
            result += f"**Bio:** {og_desc.get('content', '')[:200]}\n"

        result += "\n"

        # Try to find articles
        articles = soup.select("article")[:max_articles]

        if articles:
            result += f"**Recent Articles ({len(articles)}):**\n\n"
            for i, article in enumerate(articles, 1):
                title_elem = article.select_one("h2, h3")
                link_elem = article.select_one("a[href*='/@'], a[href*='/p/']")

                title = title_elem.get_text(strip=True) if title_elem else "Untitled"

                if link_elem:
                    href = link_elem.get("href", "")
                    if href.startswith("/"):
                        href = f"https://medium.com{href}"
                    result += f"{i}. **[{title}]({href})**\n\n"
                else:
                    result += f"{i}. **{title}**\n\n"
        else:
            result += "Could not extract articles. Medium uses heavy JavaScript.\n"

        return result

    except Exception as e:
        return f"Error scraping Medium profile: {str(e)}"


# =============================================================================
# HACKER NEWS SCRAPING
# =============================================================================

@tool(description="Scrape a Hacker News user profile for submissions and comments.")
async def scrape_hackernews_user(
    username: str = Field(description="Hacker News username"),
    max_items: int = Field(description="Maximum items to fetch (1-30)", default=15)
) -> str:
    """
    Scrapes a Hacker News user profile.
    """
    try:
        # Get user info
        user_url = f"https://news.ycombinator.com/user?id={username}"
        response = await scraper_client.get(user_url)

        if response.status_code != 200:
            return f"Hacker News user {username} not found."

        soup = BeautifulSoup(response.text, "lxml")

        result = f"**🟧 Hacker News Profile: {username}**\n"
        result += f"🔗 Profile: [news.ycombinator.com/user?id={username}](https://news.ycombinator.com/user?id={username})\n\n"

        # Extract user info from table
        info_table = soup.select_one("table table")
        if info_table:
            rows = info_table.select("tr")
            for row in rows:
                label = row.select_one("td:first-child")
                value = row.select_one("td:last-child")
                if label and value:
                    label_text = label.get_text(strip=True).rstrip(":")
                    value_text = value.get_text(strip=True)
                    if label_text and value_text and label_text != value_text:
                        result += f"**{label_text}:** {value_text}\n"

        result += "\n"

        # Get submissions
        submissions_url = f"https://news.ycombinator.com/submitted?id={username}"
        submissions_response = await scraper_client.get(submissions_url)

        if submissions_response.status_code == 200:
            submissions_soup = BeautifulSoup(submissions_response.text, "lxml")
            items = submissions_soup.select(".athing")[:max_items]

            if items:
                result += f"**Recent Submissions ({len(items)}):**\n\n"
                for i, item in enumerate(items, 1):
                    title_elem = item.select_one(".titleline a")
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        href = title_elem.get("href", "")
                        if not href.startswith("http"):
                            href = f"https://news.ycombinator.com/{href}"

                        # Get HN discussion link
                        item_id = item.get("id", "")
                        hn_link = f"https://news.ycombinator.com/item?id={item_id}"

                        result += f"{i}. **[{title}]({href})**\n"
                        result += f"   💬 [HN Discussion]({hn_link})\n\n"

        return result

    except Exception as e:
        return f"Error scraping Hacker News user: {str(e)}"
