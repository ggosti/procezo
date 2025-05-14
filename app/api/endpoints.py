from typing import Optional

from fastapi import APIRouter,Query
from fastapi.responses import JSONResponse
from app.core.state import data_container

import os
import pandas as pd
from typing import Dict, Any, List

router = APIRouter()

@router.get("/api/projects/{step}")
def list_projects(step: str):
    return [{"name":p.name, "step":p.step} for p in data_container.projects if step == p.step]#.keys())

@router.get("/api/groups/{step}/{project_name}")
def list_groups(step: str, project_name: str, ver: Optional[str] = Query(default=None)):
    #print('list_groups',step,project_name,ver)
    groups = data_container.get_groups_in_project(project_name, step, ver)
    #print('groups',groups)
    if len(groups) == 0:
        return JSONResponse(content={"error": f"Not found groups in {project_name} at step {step}"}, status_code=404)
    return [{"name":g.name, "step":g.step, "version":g.version} for g in groups]

@router.get("/api/group/proc/{project_name}/{group_name}/{ver}")
def get_group_data(project_name: str, group_name: str, ver: str):
    step = 'proc'
    #print('list_groups',step,project_name,ver)
    group = data_container.get_group(project_name, group_name, step, ver)
    print('groups',group.name,group.version,group.project.name,group.panoramic)
    if group is None:
        return JSONResponse(content={"error": f"Not found group {group_name} in {project_name} at step {step}"}, status_code=404)
    return {"name":group.name, "step":group.step, "version":group.version, "panoramic":group.panoramic}

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
    return JSONResponse(content={"rows": record.to_dict(),"timeKey": record.timeKey,"pars":record.pars}, status_code=200)

@router.get("/api/record/summary/{step}/{project_name}/{group_name}/{record_name}")
def get_record_data(step: str, project_name: str, group_name: str, record_name: str, ver: Optional[str] = Query(default=None)):
    record =  data_container.get_record(project_name,group_name,record_name,step,version=ver)
    #print('record',record,'pars',record.pars)
    if record is None:
        return JSONResponse(content={"error": f"Not found record {record_name} version {ver}: in {project_name}/{group_name}  at step {step}"}, status_code=404)
    return record.pars

@router.get("/api/record/children/{step}/{project_name}/{group_name}/{record_name}")
def get_record_data(step: str, project_name: str, group_name: str, record_name: str, ver: Optional[str] = Query(default=None)):
    record =  data_container.get_record(project_name,group_name,record_name,step,version=ver)
    #print('record',record)
    children = record.child_records
    if record is None:
        return JSONResponse(content={"error": f"Not found record {record_name} version {ver}: in {project_name}/{group_name}  at step {step}"}, status_code=404)
    return [{"name":r.name,"step":r.step,"ver":r.version} for r in children] #record.child_records

@router.post("/api/record/proc/{project_name}/{group_name}/{record_name}/preprocessed-VR-sessions")
def store_record_data(
    project_name: str, 
    group_name: str, 
    record_name: str, 
    #verion_name: str, 
    rows: List[Dict[str, Any]]
    ):

    # Convert JSON to Pandas DataFrame
    print('rows',rows)
    kDf = pd.DataFrame(rows)

    verion_name = 'preprocessed-VR-sessions' 

    rawRecord =  data_container.get_record(project_name,group_name,record_name,'raw')
    procGroup = data_container.get_group(project_name,group_name,'proc',version=verion_name)
    #print('record',record)
    if rawRecord is None:
        return JSONResponse(content={"error": f"Not found record {record_name} version {verion_name}: in {project_name}/{group_name}  at step proc"}, status_code=404)
    #print('record',record)
    fName = record_name+'-preprocessed'
    record_path = os.path.join(procGroup.path, 'preprocessed-VR-sessions',fName+'.csv')
    procRecord = data_container.add_record(rawRecord,procGroup,fName,record_path, kDf, version=verion_name)
    kDf.to_csv(procRecord.path,index=False,na_rep='NA') #(keeperPath+'/'+fname+'-preprocessed.csv',index=False,na_rep='NA')
    procRecord.data = kDf
    procRecord.putProcRecordInProcFile()
    return JSONResponse(content={"status": "ok"}, status_code=200)

@router.put("/api/record/proc/{project_name}/{group_name}/{record_name}/preprocessed-VR-sessions")
def update_record_data(
    project_name: str, 
    group_name: str, 
    record_name: str, 
    #verion_name: str, 
    rows: List[Dict[str, Any]]
    ):

    # Convert JSON to Pandas DataFrame
    kDf = pd.DataFrame(rows)

    verion_name = 'preprocessed-VR-sessions' 
    procRecord =  data_container.get_record(project_name,group_name,record_name,'proc',version=verion_name)
    if procRecord is None:
        return JSONResponse(content={"error": f"Not found record {record_name} version {verion_name}: in {project_name}/{group_name}  at step proc"}, status_code=404)

    kDf.to_csv(procRecord.path,index=False,na_rep='NA')
    procRecord.data = kDf
    procRecord.putProcRecordInProcFile()
    return JSONResponse(content={"status": "ok"}, status_code=200)