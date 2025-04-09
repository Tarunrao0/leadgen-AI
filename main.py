from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from scrape import scrape_multiple
from parse import parse_with_ollama
from outreach import generate_outreach, TEMPLATES
import uvicorn
import time
import re

# Initialize FastAPI with enhanced CORS settings
app = FastAPI(title="LeadGen AI API")

# Configure CORS middleware
origins = [
    "https://docs.google.com",      # Google Sheets
    "https://script.google.com",    # Google Apps Script
    "https://*.googleusercontent.com",  # Google preview domains
    "https://*.ngrok-free.app",     # All ngrok domains
    "http://localhost",             # Local development
    "http://localhost:3000",        # Common dev server port
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600  # Cache preflight requests for 10 minutes
)

# Middleware to handle preflight OPTIONS requests
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    response = await call_next(request)
    if request.method == "OPTIONS":
        response.headers["Access-Control-Allow-Origin"] = request.headers.get("origin", "*")
        response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Max-Age"] = "600"
    return response

# Data models
class ExtractionRequest(BaseModel):
    urls: List[str]
    fields: List[str]
    
class OutreachRequest(BaseModel):
    url: str
    template_key: str
    product: str
    company_data: Dict[str, str]
    custom_hook: Optional[str] = None

# API endpoints
@app.post("/extract")
async def extract_data(request: ExtractionRequest):
    """Endpoint for extracting data from URLs"""
    try:
        start_time = time.time()
        
        # Input validation
        if not request.urls or not request.fields:
            raise HTTPException(status_code=400, detail="Missing required fields")
            
        if len(request.urls) > 50:
            raise HTTPException(status_code=400, detail="Maximum 50 URLs per request")

        # Scrape and process data
        scraped_data = scrape_multiple(request.urls)
        parse_prompt = ", ".join(request.fields)
        results = []
        
        for data in scraped_data:
            if 'error' in data:
                results.append({'url': data['url'], 'error': data['error']})
                continue
                
            try:
                llm_output = parse_with_ollama(
                    dom_chunks=[data['cleaned_content']],
                    parse_description=parse_prompt
                )
                
                result = {'url': data['url']}
                
                for line in llm_output.split('\n'):
                    if '::' in line:
                        key, val = line.split('::', 1)
                        key = re.sub(r'[^\w\s]', '', key).strip().lower()
                        result[key] = val.strip()
                
                results.append(result)
                
            except Exception as e:
                results.append({'url': data['url'], 'error': str(e)})
                
        return {'data': results, 'time_elapsed': time.time() - start_time}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/generate-outreach")
async def generate_outreach_message(request: OutreachRequest):
    """Endpoint for generating outreach messages"""
    try:
        start_time = time.time()
        
        # Prepare company data with custom hook if provided
        company_data = request.company_data
        if request.custom_hook:
            company_data['custom_hook'] = request.custom_hook
            
        message = generate_outreach(
            template_key=request.template_key,
            company_data=company_data,
            product=request.product
        )
        
        return {
            "message": message,
            "time_elapsed": time.time() - start_time,
            "template_used": request.template_key
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/template-options")
async def get_template_options():
    """Endpoint to get available outreach templates"""
    try:
        return list(TEMPLATES.keys())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "LeadGen AI API",
        "version": "1.1.0",
        "features": {
            "extraction": True,
            "outreach": True,
            "template_options": True
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        timeout_keep_alive=30
    )