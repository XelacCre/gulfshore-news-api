from fastapi import APIRouter, Query
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import re

router = APIRouter()

# 🔗 Only Herald Tribune News – Business
NEWS_SOURCES = [
    {
        "name": "Herald Tribune – Home",
        "url": "https://www.heraldtribune.com/",
        "selector": "a.gnt_m_lb_a"
    },
    {
        "name": "Herald Tribune – News",
        "url": "https://www.heraldtribune.com/news/",
        "selector": "a.gnt_m_flm_a"
    },
    {
        "name": "Herald Tribune - Local",
        "url": "https://www.heraldtribune.com/news/local/",
        "selector": "a.gnt_m_flm_a"
    },
    {   "name": "Herald Tribune - Sarasota",
        "url": "https://www.heraldtribune.com/news/sarasota/",
        "selector": [

            "a.gnt_m_flm_a",
            "a.gnt_m_he"
        ]    
    },
    {   "name": "Herald Tribune - Manatee",
        "url": "https://www.heraldtribune.com/news/manatee/",
        "selector": "a.gnt_m_flm_a"
    },
    {   "name": "Herald Tribune - Venice and North Port",
        "url": "https://www.heraldtribune.com/news/venice-and-north-port/",
        "selector": "a.gnt_m_flm_a"
    },
    {   "name": "Herald Tribune - State News",
        "url": "https://www.heraldtribune.com/news/state/",
        "selector": "a.gnt_m_flm_a"
    }
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}

# 🧠 Match "March 25, 2025"
DATE_PATTERN = re.compile(r"^(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}$")

# 🕵️ Extract article date
def fetch_article_date(article_url: str) -> str:
    try:
        if article_url.startswith("/"):
            article_url = "https://www.heraldtribune.com" + article_url

        resp = requests.get(article_url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Gannett-style meta tag
        meta_date = soup.find("meta", {"property": "article:published"})
        if meta_date and meta_date.get("content"):
            try:
                parsed_date = datetime.strptime(meta_date["content"], "%Y-%m-%dT%H:%M:%SZ")
                return parsed_date.strftime("%B %d, %Y")
            except Exception as e:
                print(f"⚠️ Meta date parse failed: {e}")

        # Fallback: Extract date from URL if present (e.g. /2025/02/25/)
        url_date_match = re.search(r"/(\d{4})/(\d{2})/(\d{2})/", article_url)
        if url_date_match:
            try:
                year, month, day = map(int, url_date_match.groups())
                parsed_date = datetime(year, month, day)
                return parsed_date.strftime("%B %d, %Y")
            except Exception as e:
                print(f"⚠️ URL date parse failed: {e}")
    

        return "Date not found"
    except requests.RequestException:
        return "Date fetch failed"

# 📅 Date range filtering
def is_within_days(date_str: str, days: int) -> bool:
    try:
        pub_dt = datetime.strptime(date_str, "%B %d, %Y")
        return pub_dt >= datetime.utcnow() - timedelta(days=days)
    except Exception as e:
        print(f"⚠️ Date parse failed for '{date_str}': {e}")
        return False

# 🔁 Main scraping
def scrape_news(days: int = 0):
    news_list = []

    for source in NEWS_SOURCES:
        print(f"\n🔍 Scraping: {source['name']}")
        try:
            resp = requests.get(source["url"], headers=HEADERS, timeout=10)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"⚠️ Error fetching {source['name']}: {str(e)}")
            continue

        soup = BeautifulSoup(resp.text, 'html.parser')
        selectors = source["selector"]
        if isinstance(selectors, str):
            selectors = [selectors]

        articles = []
        for sel in selectors:
            articles.extend(soup.select(sel))

        if not articles:
            print(f"⚠️ No articles found for {source['name']}")
            continue

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
    executor.submit(fetch_article_date, a['href']): a
    for a in articles if a.has_attr("href")
}


            for future in futures:
                article = futures[future]
                headline = article.get_text(strip=True)
                link = article['href']

                # Fix relative links
                if link.startswith("/"):
                    link = "https://www.heraldtribune.com" + link

                pub_date = future.result()

                if days > 0 and not is_within_days(pub_date, days):
                    continue

                news_item = {
                    "source": source["name"],
                    "title": headline,
                    "url": link,
                    "date": pub_date
                }

                print(f"[{pub_date}] {headline}")
                print(f" → {link}\n")

                news_list.append(news_item)

    return {
        "news": news_list,
        "fetched_at": datetime.now().astimezone().isoformat()
    }

# 🧠 API route
@router.get("/news")
def get_news(days: int = Query(0, description="Limit results to articles published in the last N days")):
    return scrape_news(days)

# 🧪 Local test
if __name__ == "__main__":
    print("Scraping Herald Tribune News – Business...\n")
    result = scrape_news(days=0)
    print(result)
