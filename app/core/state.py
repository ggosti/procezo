from app.services.data_container import DataContainer
import json


with open('config.json') as f:
    d = json.load(f)

rawProjectsPath = d['rawProjectsPath']
procProjectsPath = d['procProjectsPath']
allowedProjects = d['allowedProjects']
processes = d['processes']

print('load projects insede state.py')    
data_container = DataContainer(rawProjectsPath, procProjectsPath, allowedProjects, processes)

