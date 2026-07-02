from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .app.api import router
from .app.config import settings

app = FastAPI(title="PickPilot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"status": "PickPilot API is operational"}
