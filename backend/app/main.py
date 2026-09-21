from fastapi import FastAPI

from app.api.routes.reviews import router as review_router


app = FastAPI(
    title="AI Code Review System",
    description="LLM-powered automated code review platform",
    version="0.1.0"
)

app.include_router(review_router)


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }