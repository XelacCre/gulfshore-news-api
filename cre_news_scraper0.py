from fastapi import FastAPI
import requests
from bs4 import BeautifulSoup

app = FastAPI()

URL = "https://www.gulfshorebusiness.com/category/commercial-real-estate/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                  "AppleWebKit/537.36 (KHTML, like Gecko)"
                  "Chrome/123.0.0.0 Safari/537.36"
}

def scrape_news():
    try:
        response = requests.get(URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        return {"error": f"Failed to fetch news: {str(e)}"}

    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract headlines & URLs
    articles = soup.select('article.jeg_post div.jeg_postblock_content h3.jeg_post_title a')
    if not articles:
        return {"error": "No articles found. Check your selectors."}

    news_list = []
    for article in articles:
        headline = article.get_text(strip=True)
        link = article['href']
        news_list.append({"title": headline, "url": link})

    return {"news": news_list}

@app.get("/news")
def get_news():
    return scrape_news()
