from fastapi import FastAPI
from dash_app.app import dash_app
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse
from fastapi.middleware.wsgi import WSGIMiddleware

# Define the FastAPI server
app = FastAPI(title="procezo-api", version="0.0.1", description="Procezo API for Dash App")

# Mount Dash at /dashboard
app.mount("/dashboard", WSGIMiddleware(dash_app))

# Allow local frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return RedirectResponse(url="/dashboard")