from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from app.api import (
    auth,
    properties,
    tenants,
    issues,
    payments,
    waitlist,
    messaging,
    ussd,
    dashboard
)

# Create FastAPI app
app = FastAPI(
    title="PropMS API",
    description="Rental property management platform API. Powers the landlord dashboard and integrates with Africa's Talking SMS and USSD APIs.",
    version="1.0.0",
    contact={
        "name": "PropMS Team"
    }
)

# CORS middleware (configure for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


# Health check endpoint
@app.get("/", tags=["health"])
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "PropMS API is running"}


# Register routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(properties.router, prefix="/properties", tags=["properties"])
app.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
app.include_router(issues.router, prefix="/issues", tags=["issues"])
app.include_router(payments.router, prefix="/payments", tags=["payments"])
app.include_router(waitlist.router, prefix="/waitlist", tags=["waitlist"])
app.include_router(messaging.router, prefix="/messaging", tags=["messaging"])
app.include_router(ussd.router, prefix="/ussd", tags=["ussd"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
