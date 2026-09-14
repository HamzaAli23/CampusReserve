from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse

from .api import router
from .database import create_tables


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_tables()
    yield


app = FastAPI(
    title="CampusReserve API",
    description="Room and equipment reservation API for a student portfolio project.",
    version="0.2.1",
    lifespan=lifespan,
)
app.include_router(router)


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    return FileResponse(Path(__file__).parent / "static" / "index.html")


def run() -> None:
    uvicorn.run("campusreserve.main:app", host="127.0.0.1", port=8000, reload=False)
