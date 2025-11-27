from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from typing import List, Optional
import os

from rag_engine import MilletRAGEngine
from recommendation_engine import MilletRecommender

app = FastAPI(
    title="Millet Health Advisor API",
    description="AI-powered millet recommendations based on health concerns",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (HTML, CSS, JS) from current directory
app.mount("/static", StaticFiles(directory="."), name="static")

# Request models
class HealthQuery(BaseModel):
    health_concerns: List[str]
    user_query: Optional[str] = ""

class RecommendationResponse(BaseModel):
    success: bool
    recommendations: List[dict]
    summary: str
    scientific_evidence: dict

# Initialize engines
rag_engine = MilletRAGEngine()
recommender = MilletRecommender()

@app.get("/")
async def read_root():
    return FileResponse('index.html')

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Millet Health Advisor API is running"}

@app.post("/api/recommend", response_model=RecommendationResponse)
async def get_recommendations(query: HealthQuery):
    try:
        if not query.health_concerns:
            raise HTTPException(status_code=400, detail="At least one health concern is required")
        
        # Get recommendations from CSV data
        recommendations = recommender.get_top_recommendations(query.health_concerns, top_n=3)
        
        # Get scientific evidence for each recommended millet
        # Get scientific evidence for each recommended millet
        scientific_evidence = {}
        
        # FIX: Combine selected tags AND user's typed text for the search
        search_context = ', '.join(query.health_concerns)
        if query.user_query:
            search_context += f". Specific focus: {query.user_query}"

        for rec in recommendations:
            millet_name = rec['name'].lower().replace(' millet', '')
            
            # Now we search the database for "Weight Loss AND Bone Strength"
            evidence = rag_engine.get_scientific_evidence(
                health_concern=search_context,
                millet_type=millet_name
            )
            scientific_evidence[rec['name']] = evidence
        
        # Generate comprehensive summary using LLM
        user_data = {
            'recommendations': recommendations,
            'health_concerns': query.health_concerns,
            'user_query': query.user_query
        }
        summary = rag_engine.get_combined_recommendation(query.health_concerns, user_data)
        
        # Enhance each recommendation with benefits summary
        for rec in recommendations:
            millet_name = rec['name'].lower().replace(' millet', '')
            evidence = scientific_evidence.get(rec['name'], [])
            benefits_summary = rag_engine.generate_benefits_summary(
                millet_name, query.health_concerns, evidence
            )
            rec['benefits_summary'] = benefits_summary
        
        return RecommendationResponse(
            success=True,
            recommendations=recommendations,
            summary=summary,
            scientific_evidence=scientific_evidence
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")

@app.get("/api/millets")
async def get_all_millets():
    try:
        millets = recommender.df['millet_type'].unique().tolist()
        return {"millets": [millet.title() for millet in millets]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)