from fastapi import FastAPI
from app.gulfshore.scraper import router as gulfshore_router
from app.naples.scraper import router as naples_router

app = FastAPI(title="News Scraper API")

# Mount routes
app.include_router(gulfshore_router, prefix="/gulfshore", tags=["Gulfshore Business"])
app.include_router(naples_router, prefix="/naples", tags=["Naples Daily News"])
