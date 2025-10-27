from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from .routes import events, auth
from datetime import datetime

app = FastAPI()

timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events.router)
app.include_router(auth.router)


@app.get("/")
def welcome():
    """Server's up and running"""
    return {
        "message": "Cloudboard Server is running!",
        "version": "1.0.0",
        "started_at": timestamp,
    }


@app.get("/tracker.js", response_class=FileResponse)
async def get_tracker():
    """Serve the tracker file"""
    headers = {"Cache-Control": "public, max-age=86400"}
    return FileResponse(
        "src/static/tracker.js", media_type="application/javascript", headers=headers
    )
