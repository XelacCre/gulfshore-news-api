from fastapi import FastAPI
from app.gulfshore.scraper import router as gulfshore_router
from app.naples.scraper import router as naples_router
from app.newspress.scraper import router as newspress_router
from app.jacksonville.scraper import router as jax_router
from app.heraldtribune.scraper import router as herald_router

app = FastAPI(title="News Scraper API")

# Mount routes
app.include_router(gulfshore_router, prefix="/gulfshore", tags=["Gulfshore Business"])
app.include_router(naples_router, prefix="/naples", tags=["Naples Daily News"])
app.include_router(newspress_router, prefix="/news-press", tags=["News-Press"])
app.include_router(jax_router, prefix="/jax", tags=["Jacksonville Daily Record"])
app.include_router(herald_router, prefix="/herald-tribune", tags=["Herald Tribune"])