from fastapi import FastAPI

# Disable generated documentation routes (and their CDN assets).
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
