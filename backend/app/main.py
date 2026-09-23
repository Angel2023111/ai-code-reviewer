from fastapi import FastAPI

from app.api.routes.reviews import router as review_router
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="AI Code Review System",
    description="LLM-powered automated code review platform",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(review_router)


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }