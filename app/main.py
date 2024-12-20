from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import wallets

app = FastAPI(
    title="Wallet API",
    description="API for managing wallets and transactions",
    version="1.0.0",
    redirect_slashes=False
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    wallets.router,
    prefix="/api/v1/wallets",
    tags=["wallets"]
)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
