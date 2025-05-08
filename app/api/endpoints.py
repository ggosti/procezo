from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.core.state import data_container

router = APIRouter()

@router.get("/api/projects")
def list_projects():
    return [(p.name,p.step) for p in data_container.projects]#.keys())

@router.get("/api/record/{step}/{project_name}/{group_name}/{record_name}/{version_name}")
def get_record_data(step: str, project_name: str, group_name: str, record_name: str, version_name: str):
    try:
        record =  data_container.get_record(project_name,group_name,record_name,step,version_name)
        return JSONResponse(content={"rows": record.to_dict()})
    except KeyError as e:
        return JSONResponse(content={"error": f"Not found: {e}"}, status_code=404)
    

