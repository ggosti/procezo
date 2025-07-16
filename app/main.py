from fastapi import FastAPI
from contextlib import asynccontextmanager

from starlette.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.staticfiles import StaticFiles


from app.core.state import data_container
from app.api.endpoints import router as api_router
from dash_app.app import dash_app

from dash_app.vars_app import dash_app as vars
from dash_app.edit_group_app import dash_app as edit_group
from dash_app.edit_record_app import dash_app as edit_record


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Loading data...")
    steps = ['raw','proc']
    for step in steps: 
        print('load step',step)
        data_container.load_all(step)
    print('update put groups pars')
    data_container.update_put_groups_pars()
    data_container.update_put_records_pars()
    #print('load project lineage')
    #projects = link_projects(projects)
    #print('load group lineage')
    #groups = link_groups(groups)
    print('load record lineage')
    data_container.link_records()
    print("Data loaded.")
    yield
    print("App shutting down.")

# Define the FastAPI server
app = FastAPI(title="procezo-api", version="0.0.1", description="Procezo API for Dash App",lifespan=lifespan)

# Register api_ruter
app.include_router(api_router)

# Mount 'static' folder at "/"
app.mount("/app", StaticFiles(directory="app/static", html=True), name="static")

# Mount Dash at /dashboard
app.mount("/dashboard", WSGIMiddleware(dash_app.server))
app.mount("/vars", WSGIMiddleware(vars.server))
app.mount("/edit_group", WSGIMiddleware(edit_group.server))
app.mount("/edit_record", WSGIMiddleware(edit_record.server))

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


