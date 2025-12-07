"""Aplicação FastAPI principal."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers.v1 import (
    staff, stores, departments, access_requests, invitations,
    product_frames, product_lenses, customers,
    cash_sessions, cash_movements, service_orders, products,
    sales, lab, receivable_accounts, kardex
)


app = FastAPI(
    title="Otica API",
    description="API de Gestão de Óticas - Sistema SaaS Multi-tenant",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
# Se não houver origens configuradas, usar lista padrão
cors_origins = settings.cors_origins_list if settings.cors_origins_list else [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8080",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8080",
    "http://192.168.0.100:3000",  # IP local da rede
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Routers
app.include_router(staff.router, prefix="/api/v1")
app.include_router(stores.router, prefix="/api/v1")
app.include_router(departments.router, prefix="/api/v1")
app.include_router(access_requests.router, prefix="/api/v1")
app.include_router(invitations.router, prefix="/api/v1")
app.include_router(product_frames.router, prefix="/api/v1")
app.include_router(product_lenses.router, prefix="/api/v1")
app.include_router(customers.router, prefix="/api/v1")
# Fase 2 - Ciclo de Venda
app.include_router(cash_sessions.router, prefix="/api/v1")
app.include_router(cash_movements.router, prefix="/api/v1")
app.include_router(service_orders.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(sales.router, prefix="/api/v1")
app.include_router(lab.router, prefix="/api/v1")
app.include_router(receivable_accounts.router, prefix="/api/v1")
app.include_router(kardex.router, prefix="/api/v1")


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

