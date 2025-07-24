import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from scraper import LinkedInJobScraper
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],  # Allow your Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class JobSearchRequest(BaseModel):
    query: str
    location: Optional[str] = None
    num_jobs: Optional[int] = 10

class Job(BaseModel):
    id: str
    title: str
    company: str
    location: str
    description: str
    postedDate: str
    url: str

class JobSearchResponse(BaseModel):
    jobs: List[Job]
    total_results: int
    search_time: float
    query: str
    location: Optional[str]

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up the FastAPI server...")
    try:
        # Test the scraper setup
        scraper = LinkedInJobScraper()
        scraper.setup_driver()
        logger.info("Selenium WebDriver setup successful")
    except Exception as e:
        logger.error(f"Failed to setup WebDriver: {str(e)}")
        raise

@app.post("/jobs/", response_model=JobSearchResponse)
async def search_jobs(request: JobSearchRequest):
    logger.info(f"Received job search request - Query: {request.query}, Location: {request.location}")
    
    try:
        start_time = datetime.now()
        scraper = LinkedInJobScraper()
        jobs = scraper.scrape_jobs(
            search_query=request.query,
            location=request.location,
            num_jobs=request.num_jobs
        )
        search_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"Successfully scraped {len(jobs)} jobs in {search_time:.2f} seconds")
        
        return JobSearchResponse(
            jobs=jobs,
            total_results=len(jobs),
            search_time=search_time,
            query=request.query,
            location=request.location
        )
    except Exception as e:
        logger.error(f"Error during job scraping: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch jobs: {str(e)}"
        )

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting the server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info") 