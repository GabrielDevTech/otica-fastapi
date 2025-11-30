"""Aplicação FastAPI principal."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers.v1 import staff, stores, departments, access_requests, invitations


app = FastAPI(
    title="Otica API",
    description="API de Gestão de Óticas - Sistema SaaS Multi-tenant",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(staff.router, prefix="/api/v1")
app.include_router(stores.router, prefix="/api/v1")
app.include_router(departments.router, prefix="/api/v1")
app.include_router(access_requests.router, prefix="/api/v1")
app.include_router(invitations.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Endpoint raiz."""
    return {
        "message": "Otica API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "ok"}

