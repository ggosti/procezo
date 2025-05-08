from fastapi import FastAPI
from contextlib import asynccontextmanager

from starlette.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse
from fastapi.middleware.wsgi import WSGIMiddleware


from app.core.state import data_container
from app.api.endpoints import router as api_router
from dash_app.app import dash_app

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Loading data...")
    steps = ['raw','proc']
    for step in steps: 
        print('load step',step)
        data_container.load_all(step)
    print("Data loaded.")
    yield
    print("App shutting down.")

# Define the FastAPI server
app = FastAPI(title="procezo-api", version="0.0.1", description="Procezo API for Dash App",lifespan=lifespan)

# Register api_ruter
app.include_router(api_router)

# Mount Dash at /dashboard
app.mount("/dashboard", WSGIMiddleware(dash_app.server))

# Allow local frontend access, Enable CORS (optional but common for Dash/JS frontends)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/")
def read_root():
    return RedirectResponse(url="/dashboard")


