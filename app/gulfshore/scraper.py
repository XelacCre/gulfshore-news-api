from fastapi import APIRouter, Query
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta 
import re

router = APIRouter()

#  Config: Multi-source support
NEWS_SOURCES = [
    {
        "name": "Gulfshore Business – CRE",
        "url": "https://www.gulfshorebusiness.com/category/commercial-real-estate/",
        "selector": "article.jeg_post div.jeg_postblock_content h3.jeg_post_title a"
    },
    {
        "name": "Gulfshore Business – Construction & Development",
        "url": "https://www.gulfshorebusiness.com/category/construction-development/",
        "selector": "article.jeg_post div.jeg_postblock_content h3.jeg_post_title a"
    },
    {
        "name": "Gulfshore Business – Residential Real Estate",
        "url": "https://www.gulfshorebusiness.com/category/residential-real-estate/",
        "selector": "article.jeg_post div.jeg_postblock_content h3.jeg_post_title a"
    },
    {
        "name": "Gulfshore Business – Home",
        "url": "https://www.gulfshorebusiness.com/",
        "selector": "article.elementor-post h3 a"
    }
]

#  HTTP request headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}

#  Date format regex
DATE_PATTERN = re.compile(r"^(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}$")


#  Extract date from individual article page
def fetch_article_date(article_url: str) -> str:
    try:
        resp = requests.get(article_url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        candidates = soup.select("span.elementor-icon-list-text, span.jeg_meta_date")
        for tag in candidates:
            text = tag.get_text(strip=True)
            if DATE_PATTERN.match(text):
                return text
        return "Date not found"
    except requests.RequestException:
        return "Date fetch failed"


#  Check if date is within the last N days
def is_within_days(date_str: str, days: int) -> bool:
    try:
        pub_dt = datetime.strptime(date_str, "%B %d, %Y")
        return pub_dt >= datetime.utcnow() - timedelta(days=days)
    except Exception as e:
        print(f"⚠️ Date parse failed for '{date_str}': {e}")
        return False


#  Main scraping logic
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
        articles = soup.select(source["selector"])

        if not articles:
            print(f"⚠️ No articles found for {source['name']}")
            continue

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(fetch_article_date, a['href']): a for a in articles}

            for future in futures:
                article = futures[future]
                headline = article.get_text(strip=True)
                link = article['href']

                # ✅ NEW: Detect sponsored content
                is_sponsored = "/sponsored_content/" in link

                pub_date = future.result()

                # ✅ NEW: Label sponsored articles with fallback if no date
                if is_sponsored and (pub_date == "Date not found" or pub_date == "Date fetch failed"):
                    pub_date = "Sponsored Content"

                 #Filter by days if provided
                if days > 0 and not is_within_days(pub_date, days):
                    continue

                # ✅ NEW: Include sponsored flag in each article
                news_item = {
                    "source": source["name"],
                    "title": headline,
                    "url": link,
                    "date": pub_date,
                    "sponsored": is_sponsored
                }

                print(f"[{pub_date}] {headline}")
                print(f" → {link}\n")

                news_list.append(news_item)

    return {
        "news": news_list,
        "fetched_at": datetime.now().astimezone().isoformat()

    }


#  FastAPI route with optional ?days=N query
@router.get("/news")
def get_news(days: int = Query(0, description="Limit results to articles published in the last N days")):
    return scrape_news(days)


#  Local testing support
if __name__ == "__main__":
    print("Scraping Gulfshore Business (All Sources)...\n")
    result = scrape_news(days=0)
    print(result)

# Export this router so main.py can use it
__all__ = ["router"]    