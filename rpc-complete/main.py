"""
RPC Verification System
Main entry point for the FastAPI application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="RPC Verification System",
    description="""
    Complete candidate verification system with:
    - Resume Module: PDF/DOCX text extraction, skill matching, NLP
    - Project Module: GitHub API analysis, plagiarism detection
    - Certificate Module: OCR extraction, QR code verification
    - Trust Score Engine: Weighted scoring combining all modules
    """,
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and register routes after app creation to ensure compatibility
from app.api.routes import router  # noqa: E402
app.include_router(router, prefix="/api/v1", tags=["verification"])


@app.get("/")
async def root():
    return {
        "name": "RPC Verification System",
        "version": "1.0.0",
        "endpoints": {
            "resume": "/api/v1/verify-resume",
            "project": "/api/v1/verify-project",
            "certificate": "/api/v1/verify-certificate",
            "full": "/api/v1/verify-full",
        },
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
