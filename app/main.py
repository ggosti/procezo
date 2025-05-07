from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.core.state import data_container
from dash_app.app import dash_app

from starlette.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse
from fastapi.middleware.wsgi import WSGIMiddleware

# Define the FastAPI server
app = FastAPI(title="procezo-api", version="0.0.1", description="Procezo API for Dash App")

# Mount Dash at /dashboard
app.mount("/dashboard", WSGIMiddleware(dash_app.server))

# Allow local frontend access, Enable CORS (optional but common for Dash/JS frontends)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

steps = ['raw','proc']

@app.on_event("startup")
def load_data():
    print('dataContainer',data_container)
    print('dataContainer projects',data_container.projects)
    for step in steps: 
        print('load step',step)
        data_container.load_all(step)
        print('dataContainer projects',[p.name for p in data_container.projects])
        print('dataContainer groups',[(g.id, g.name, g.project.name,g.step,g.version) for g in data_container.groups])

@app.get("/")
def read_root():
    return RedirectResponse(url="/dashboard")

@app.get("/api/projects")
def list_projects():
    return [(p.name,p.step) for p in data_container.projects]#.keys())
