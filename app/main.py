from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import wallets

app = FastAPI(
    title="Wallet API",
    description="API for managing wallets and transactions",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(wallets.router, prefix="/api/v1", tags=["wallets"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
