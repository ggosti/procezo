from typing import Optional

from fastapi import APIRouter,Query
from fastapi.responses import JSONResponse
from app.core.state import data_container

router = APIRouter()

@router.get("/api/projects/{step}")
def list_projects(step: str):
    return [(p.name,p.step) for p in data_container.projects if step == p.step]#.keys())

@router.get("/api/groups/{step}/{project_name}")
def list_groups(step: str, project_name: str, ver: Optional[str] = Query(default=None)):
    groups = data_container.get_groups_in_project(project_name, step, ver)
    print('groups',groups)
    if len(groups) == 0:
        return JSONResponse(content={"error": f"Not found groups in {project_name} at step {step}"}, status_code=404)
    return [[g.name,g.step,g.version] for g in groups]

@router.get("/api/records/{step}/{project_name}/{group_name}")
def list_records(step: str, project_name: str, group_name: str, ver: Optional[str] = Query(default=None)):
    records = data_container.get_recods_in_project_and_group(project_name, group_name, step,  ver)
    print('records',records)
    if len(records) == 0:
        return JSONResponse(content={"error": f"Not found records in {project_name}/{group_name} at step {step} ver {ver}"}, status_code=404)
    return [{"name":r.name,"step":r.step,"ver":r.version,"time_key":r.timeKey} for r in records]

@router.get("/api/record/{step}/{project_name}/{group_name}/{record_name}")
def get_record_data(step: str, project_name: str, group_name: str, record_name: str, ver: Optional[str] = Query(default=None)):
    record =  data_container.get_record(project_name,group_name,record_name,step,version=ver)
    if record is None:
        return JSONResponse(content={"error": f"Not found record {record_name} version {ver}: in {project_name}/{group_name}  at step {step}"}, status_code=404)
    return JSONResponse(content={"rows": record.to_dict()})
    

