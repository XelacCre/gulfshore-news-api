from fastapi import APIRouter, Query
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import re
import calendar

router = APIRouter()

NEWS_SOURCES = [
    {
        "name": "Jacksonville Daily Record – Front Page",
        "url": "https://www.jaxdailyrecord.com/",
        "selector": "div.card__post__title > h6 > a"
    },
    {   "name": "Jacksonville Daily Record - Government",
        "url": "https://www.jaxdailyrecord.com/news/government",
        "selector": "div.card__post__title > h6 > a"
    }
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}

# 📅 Attempt to extract date from URL
def extract_date_from_url(url: str) -> str:
    match = re.search(r"/news/(\d{4})/([a-z]{3})/(\d{2})", url)
    if match:
        year, month_abbr, day = match.groups()
        try:
            month_num = list(calendar.month_abbr).index(month_abbr.capitalize())
            full_date = datetime(int(year), month_num, int (day))
            return full_date.strftime("%B %d, %Y")
        except Exception as e:
            print(f"⚠️ Failed to parse date from URL: {e}")
    return "Date not found"

def is_within_days(date_str: str, days: int) -> bool:
    try:
        pub_dt = datetime.strptime(date_str, "%B %d, %Y")
        return pub_dt >= datetime.utcnow() - timedelta(days=days)
    except:
        return False

def scrape_news(days: int = 0):
    news_list = []

    for source in NEWS_SOURCES:
        print(f"\n🔍 Scraping: {source['name']}")
        try:
            resp = requests.get(source["url"], headers=HEADERS, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            print(f"⚠️ Error fetching {source['name']}: {e}")
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        articles = soup.select(source["selector"])

        if not articles:
            print(f"⚠️ No articles found for {source['name']}")
            continue

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {}
            for a in articles:
                if a.has_attr("href"):
                    raw_link = a["href"]
                    full_link = "https://www.jaxdailyrecord.com" + raw_link if raw_link.startswith("/") else raw_link
                    futures[executor.submit(extract_date_from_url, full_link)] = a
            

            for future in futures:
                article = futures[future]
                headline = article.get_text(strip=True)
                link = article["href"]

                # Fix relative links
                if link.startswith("/"):
                    link = "https://www.jaxdailyrecord.com" + link

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

@router.get("/news")
def get_jax_news(days: int = Query(0, description="Limit results to articles published in the last N days")):
    return scrape_news(days)

# Local test
if __name__ == "__main__":
    print("Scraping Jacksonville Daily Record...\n")
    result = scrape_news(days=0)
    print(result)
