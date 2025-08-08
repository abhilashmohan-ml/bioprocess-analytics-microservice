from fastapi import FastAPI
from .api import router
from .logging import configure_logging; configure_logging("INFO")

app = FastAPI(
    title="Auth Service",
    version="1.0.0",
    description="Authentication microservice for user registration, login, and token issuance."
)

# Attach the API router containing all auth endpoints
app.include_router(router)