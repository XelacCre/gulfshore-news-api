from fastapi import FastAPI
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import re 

app = FastAPI()

URL = "https://www.gulfshorebusiness.com/category/commercial-real-estate/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                  "AppleWebKit/537.36 (KHTML, like Gecko)"
                  "Chrome/123.0.0.0 Safari/537.36"
}

# Fetch individual article date
def fetch_article_date(article_url):
    try:
        resp = requests.get(article_url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        article_soup = BeautifulSoup(resp.text, 'html.parser')

        # Check all common span locations where dates could appear
        candidates = article_soup.select("span.elementor-icon-list-text, span.jeg_meta_date")

        # Regex for date pattern like "March 21, 2025"
        date_pattern = re.compile(r"^(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}$")

        for tag in candidates:
            text = tag.get_text(strip=True)
            if date_pattern.match(text):
                return text

        return "Date not found"

    except requests.RequestException:
        return "Date fetch failed"cd 


# Main scraping function
def scrape_news():
    try:
        response = requests.get(URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching the news listing page: {str(e)}")
        return {"error": f"Failed to fetch news: {str(e)}"}

    soup = BeautifulSoup(response.text, 'html.parser')
    articles = soup.select('article.jeg_post div.jeg_postblock_content h3.jeg_post_title a')

    if not articles:
        print("No articles found. Check your selectors.")
        return {"error": "No articles found."}

    news_list = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_article_date, article['href']): article for article in articles}

        for future in futures:
            article = futures[future]
            headline = article.get_text(strip=True)
            link = article['href']
            pub_date = future.result()

            news_item = {
                "title": headline,
                "url": link,
                "date": pub_date
            }

            # Print to terminal
            #print(f"[{pub_date}] {headline}")
            #print(f" → {link}\n")

            news_list.append(news_item)

    return {"news": news_list, "fetched_at": datetime.utcnow().isoformat()}

@app.get("/news")
def get_news():
    return scrape_news()

# Run manually in script for testing outside API
if __name__ == "__main__":
    print("Scraping Gulfshore Business - Commercial Real Estate News...\n")
    result = scrape_news()