from fastapi import FastAPI

app = FastAPI(
    title="Equity Intelligence Platform API",
    version="0.1.0",
    description="A minimal backend foundation for research and decision support."
)


@app.get("/api/v1/health")
def health_check():
    return {"status": "healthy", "message": "Equity Intelligence API is running."}
