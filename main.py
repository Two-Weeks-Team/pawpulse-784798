import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from .routes import api_router
from .models import Base, get_engine

load_dotenv()

app = FastAPI(title="PawPulse API", version="0.1.0")

# In a real deployment you would restrict origins. For demo we allow all.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup() -> None:
    """Create DB tables if they do not exist."""
    engine = get_engine()
    Base.metadata.create_all(engine)

# All routes are mounted under /api for clarity.
app.include_router(api_router, prefix="/api")
