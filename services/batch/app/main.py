from fastapi import FastAPI
from .api import router
from .logging import configure_logging; configure_logging("INFO")

app = FastAPI(title="Batch Service", version="1.0.0")
app.include_router(router)
