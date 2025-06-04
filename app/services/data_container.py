# Define classes Project, Group, and Record with relationships and data methods.
import os
import pandas as pd
from typing import Dict

import json


class Record:
    """
    Record model which are part of a groups.

    >>> record1 = Record(record_id=1, name="Test Record 1", path = "/path/project/group/record1", step='raw', df=None)
    >>> record2 = Record(record_id=2, name="Test Record 2", path = "/path/project/group/record2", step='raw', df=None)

    >>> record1.name
    'Test Record 1'

    >>> record2.name
    'Test Record 2'
    """
    def __init__(self, record_id, name, path, step, df):
        self.id = record_id
        self.name = name
        self.path = path
        self.step = step
        self.project = None
        self.version = None
        self.notes = {} #Column(String, nullable=True)
        self.parent_record = None
        self.group = None
        self.pars = None # I think this feature can be removed in future versions
        self.data = df  #df should be a Pandas DataFrame
        if hasattr(df, 'columns'):
            if 'time' in df.columns:
                self.timeKey = 'time'
            elif 'Time' in df.columns:
                self.timeKey = 'Time'
            elif 't' in df.columns:
                self.timeKey = 't'   
            else:
                self.timeKey = None

        self.child_records = []
        #self.verDict = {'preprocessed-VR-sessions':'preprocessedVRsessions','preprocessed-VR-sessions-gated':'preprocessedVRsessions-gated'}
        

    def to_dict(self):
        return self.data.to_dict(orient="records")

    def set_ver(self, ver):
        self.version = ver

    def add_child_record(self, record):
        self.child_records.append(record)

    def isProcRecordInProcFile(self):
        strVer = self.version
        pars = self.group.loadPars()
        return (self.name in pars[strVer].keys())
    
    def loadProcRecordFromProcFile(self):
        strVer = self.version
        pars = self.group.loadPars()
        #print('timeKey',self.timeKey)
        dfS = self.data[self.timeKey]
        tInt = pars[strVer][self.name]['t0'],pars[strVer][self.name]['t1']
        tInt1 = dfS.min(),dfS.max()
        assert tInt==tInt1, ('mismatch error between csv and pars',self.name,'tInt',tInt,'tInt1',tInt1)
        self.pars = pars[strVer][self.name]

    def putProcRecordInProcFile(self):
        strVer = self.version
        pars = self.group.loadPars()
        print('putProcRecordInProcFile pars',self.name, pars)
        print('timeKey',self.timeKey)
        dfS = self.data[self.timeKey]
        tInt = float(dfS.min()),float(dfS.max())
        if strVer not in pars.keys():
            pars[strVer] = {}
        pars[strVer][self.name] = {'t0':tInt[0],'t1':tInt[1]}
        self.pars = pars[strVer][self.name]
        self.group.updateParFile(strVer, pars[strVer])
        print('end putProcRecordInProcFile pars',self.name, pars)   

class Group:
    """
    Group model for managing groups of records which are part of a project.

    >>> group1 = Group(group_id=1, name="Test Group 1", path = "/path/project/group1", step='raw')
    >>> group2 = Group(group_id=2, name="Test Group 2", path = "/path/project/group2", step='raw')

    >>> group1.name
    'Test Group 1'

    >>> group2.name
    'Test Group 2'

    >>> record1 = Record(record_id=1, name="Test Record 1", path = "/path/project/group/record1", step='raw', df=None)
    >>> record2 = Record(record_id=2, name="Test Record 2", path = "/path/project/group/record2", step='raw', df=None)
    >>> group1.add_record(record1)
    >>> group1.add_record(record2)

    >>> [g.name for g in group1.records]
    ['Test Record 1', 'Test Record 2']
    
    """
    def __init__(self, group_id, name, path, step):
        self.id = group_id
        self.name = name
        self.path = path 
        self.step = step
        self.version = None
        self.pars_path = None # I think this feature can be removed in future versions
        self.pars = None # I think this feature can be removed in future versions
        self.panoramic = False
        self.gated = None 
        self.startDate = None  
        self.endDate = None 
        self.notes = {} 


        self.parent_group = None
        self.project = None

        self.records = []
        self.child_groups = []

    def add_record(self, record):
        self.records.append(record)

    def add_child_group(self, group):
        self.child_groups.append(group)

    def set_ver(self, ver):
        self.version = ver

    def parsFileExists(self):
        file = os.path.normpath(os.path.join( self.path,'pars.json') )
        return os.path.isfile(file)

    def loadPars(self):
        file = os.path.normpath(os.path.join( self.path,'pars.json') )
        self.pars_path = file
        with open(file) as f:
            pars = json.load(f)
        #print("loaded pars",file,pars)
        self.pars = pars
        # TODO: we will need to check if an other proc version is added'
        return pars
    
    def putPar(self):
        file = os.path.normpath(os.path.join( self.path,'pars.json') )
        print('putPar',file)
        print('self.name',self.name,self.parent_group)
        assert self.parent_group is not None, 'parent_group is None'
        pars = {'group': self.parent_group.name,
                'raw records folder': os.path.normpath(self.parent_group.path),
                'raw records': [r.name for r in self.parent_group.records],
                'bbox':{},
                'preprocessed-VR-sessions':{} }
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(pars, f, ensure_ascii=False, indent=4) 
        self.pars = pars
        return pars

    def updateParFile(self,key, value):
        file = os.path.normpath(os.path.join( self.path,'pars.json') )
        with open(file) as f:
            parsOld = json.load(f)
        #ver = 'preprocessed-VR-sessions-gated'
        #for c in self.child_groups:
        #    if c.version == ver:
        #        a = c.pars[ver] # assuming the first record has the pars
        #        b = self.pars[ver]
        #        print('old pars[preprocessed-VR-sessions-gated]',a)
        #        print('self.pars[preprocessed-VR-sessions-gated]',b)
        #        self.pars[ver] = a | b
        #print('self.pars[preprocessed-VR-sessions-gated] 2',self.pars[ver])
        self.pars = parsOld
        self.pars[key] = value
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(self.pars, f, ensure_ascii=False, indent=4) 
        return self.pars


    def set_panoramic(self, panoramic):
        self.panoramic = panoramic
        if self.parsFileExists():
            d = self.loadPars()
        self.pars['panoramic'] = True


    # def isParsLoaded(self):
    #     return self.pars is not None
    

    

    


class Project:
    """
    Project model for managing projects folders containing groups and other attributes.


    >>> project1 = Project(project_id=1, name="Test Project 1",path = "/path/project1",step='raw')
    >>> project2 = Project(project_id=2, name="Test Project 2",path = "/path/project2",step='raw')

    >>> project1.name
    'Test Project 1'

    >>> project2.name
    'Test Project 2'

    >>> group1 = Group(group_id=1, name="Test Group 1", path = "/path/project1/group1", step='raw')
    >>> group2 = Group(group_id=2, name="Test Group 2", path = "/path/project2/group2", step='raw')
    >>> group3 = Group(group_id=1, name="Test Group 3", path = "/path/project2/group3", step='raw')


    >>> group1.name
    'Test Group 1'

    >>> group2.name
    'Test Group 2'

    >>> project1.add_group(group1)

    >>> [g.name for g in  project1.groups]
    ['Test Group 1']

    >>> project2.add_group(group2)
    >>> project2.add_group(group3)

    >>> [g.name for g in  project2.groups]
    ['Test Group 2', 'Test Group 3']

    """
    def __init__(self, project_id, name, path, step):
        self.id = project_id
        self.name = name
        self.path = path #Column(String, nullable=True)
        self.step = step
        self.startDate = None  #Column(Date, nullable=True)
        self.endDate = None #endDate #Column(Date, nullable=True)
        self.notes = {} #Column(String, nullable=True)
        self.parent_project = None

        self.groups = []
        self.child_projects = []

    def add_group(self, group):
        self.groups.append(group)

    def add_child_project(self, project):
        self.child_projects.append(project)


class DataContainer:
    """
    DataContainer is a data structure that allows to acces the data in the frontend apps
    """
    def __init__(self, rawProjectsPath, procProjectsPath, allowedProjects, processes): #, processesDerivatives):
        self.projects = []
        self.groups = []
        self.records = []

        self.rawProjectsPath =  rawProjectsPath # = d['rawProjectsPath']
        self.procProjectsPath = procProjectsPath # = d['procProjectsPath']
        self.allowedProjects = allowedProjects #= d['allowedProjects']
        self.processes = processes # = d['processes']
        #self.processesDerivatives = processesDerivatives # = d['processesDerivatives']

    def get_project(self,project_name,step):
        filterProjects = [pr for pr in self.projects if (pr.name == project_name) and pr.step == step]
        assert len(filterProjects) < 2, "too many projects with the same name and step"
        assert len(filterProjects) > 0, "there is no project with the name and step project_name:" + project_name + " step:" + step
        project = filterProjects[0]
        return project
    
    def get_group(self,project_name,group_name,step,version=None):
        project = self.get_project(project_name,step)
        #print('project',project.name,project.step,project.groups)
        filterGroups = [gr for gr in project.groups if (gr.name == group_name)]
        if isinstance(version, str):
            filterGroups = [gr for gr in filterGroups if gr.version == version]
        assert len(filterGroups) < 2, "too many groups with the same name, project, and step"+str( [(gr.name,gr.version) for gr in filterGroups ] )

        if len(filterGroups) == 1:
            group = filterGroups[0]
            return group
        else:
            return None
        
    def patch_group(self,project_name, group_name, step, ver, update_data):
        project = self.get_project(project_name,step)
        #print('project',project.name,project.step,project.groups)
        filterGroups = [gr for gr in project.groups if (gr.name == group_name)]
        if isinstance(ver, str):
            filterGroups = [gr for gr in filterGroups if gr.version == ver]

        if len(filterGroups) == 1:
            group = filterGroups[0]
            for key, value in update_data.items():
                print('patch_group_keys',key, value)
                if hasattr(group, key):
                    setattr(group, key, value)
                    group.pars[key] = value
                    group.updateParFile(key, value)
                else:
                    raise ValueError(f"Attribute {key} not found in Group")
            return group
        else:
            return None
    
    def get_record(self,project_name,group_name,record_name,step,version=None):
        group = self.get_group(project_name,group_name,step,version)
        #print('group',group, [r.name for r in group.records])
        if group is None:
            print('group is None')
            return None
        filterRecords = [r for r in group.records if (r.name == record_name) ] 
        if isinstance(version, str):
            filterRecords = [r for r in filterRecords if r.version == version]
        assert len(filterRecords) <= 1, "Error: to many records with the same name, group, project, and step!!! "+str(filterRecords)
        #print('recordFiltered',filterRecords)
        if len(filterRecords) == 1:
            record = filterRecords[0]
            return record
        else:
            return None

    def get_groups_in_project(self,project_name,step,version=None):
        project = self.get_project(project_name,step)
        groupsInProj = [gr for gr in project.groups if gr.step == step] 
        if isinstance(version, str):
            groupsInProj = [gr for gr in project.groups if gr.step == step and gr.version == version]
        return groupsInProj

    def get_recods_in_project_and_group(self,project_name,group_name,step,version=None):
        project = self.get_project(project_name,step)
        #print('project',project.name,project.step,project.groups)
        filterGroups = [gr for gr in project.groups if (gr.name == group_name)]
        if isinstance(version, str):
            filterGroups = [gr for gr in filterGroups if gr.version == version]
        recordsInGroup = [r for g in filterGroups for r in g.records if r.step == step]
        if isinstance(version, str):
            recordsInGroup = [r for g in filterGroups for r in g.records if  r.step == step and r.version == version]
        return recordsInGroup

        
    def update_groupsInProj(self,project_name):
        #groups = g.groups
        print('update_groupsInProj',project_name)
        if project_name in self.allowedProjects:
            groupsInProj = self.get_groups_in_project(project_name, step= 'raw') #[gr.name for gr in groups if (gr.project.name ==  project_name) and gr.step == 'raw'] #os.listdir(rawProjectsPath + project_name)
            return [gr.name for gr in groupsInProj]
        else:
            return []
        
    def update_recordsInGroup(self,project_name,group_name):
        #records = g.records
        print('update_recordsInProj',project_name)
        print(group_name)
        if isinstance(group_name, str):#project_name in allowedProjects: 
            #ids, recordsInGroup, dfSs, df  = loadData(group_name,project_name)
            recordsInGroup = self.get_recods_in_project_and_group(project_name,group_name,step='raw') #[r.name for r in records if (r.project.name == project_name) and (r.group.name == group_name) and r.step == 'raw']
            print("recordsInGroup",recordsInGroup)
            return [re.name for re in recordsInGroup]
        else:
            return []
        
    def add_record(self,group,fName,record_path, data, saveFile=False, version = None, parent_record=None):
        i = len(self.records) + 1
        #print('data',data)
        newRecord = Record(i, fName, record_path, group.step, data) 
        if version is not None:
            newRecord.set_ver(version) #'preprocessed-VR-sessions-gated')

        newRecord.group = group #ungatedGroup
        newRecord.project = group.project #ungatedGroup.project
        group.add_record(newRecord) #ungatedGroup.add_record(ungatedRecord)

        if saveFile:
            data.to_csv(newRecord.path,index=False,na_rep='NA') #(keeperPath+'/'+fname+'-preprocessed.csv',index=False,na_rep='NA')
            newRecord.putProcRecordInProcFile()

        if parent_record is not None:
            newRecord.parent_record = parent_record
            parent_record.add_child_record(newRecord)
            self.records.append(newRecord)
        
        self.records.append(newRecord)
    
    def remove_record(self,record):
        #verDict = {'preprocessed-VR-sessions':'preprocessedVRsessions','preprocessed-VR-sessions-gated':'preprocessedVRsessions-gated'}
        if record is not None:
            procGroup = record.group
            strVer = record.version
            print('remove name',record.name)
            if isinstance(procGroup.pars, dict):
                print('keys',procGroup.pars[strVer].keys()) #print('keys',procGroup.pars['preprocessedVRsessions'].keys())
                if record.name in procGroup.pars[strVer].keys():
                    print('remove',record.name)
                    del procGroup.pars[strVer][record.name] #del procGroup.pars['preprocessedVRsessions'][record.name]
                print('keys',procGroup.pars[strVer].keys()) #print('keys',procGroup.pars['preprocessedVRsessions'].keys())
                procGroup.updateParFile(strVer, procGroup.pars[strVer]) #procGroup.updateParFile('preprocessedVRsessions', procGroup.pars['preprocessedVRsessions'])
            if os.path.isfile(record.path):
                os.remove(record.path)
            self.records.remove(record)
            procGroup.records.remove(record)
            parentRecord = record.parent_record
            parentRecord.child_records.remove(record)
            #childRecords


    def get_records(self,path):
        """"
        Utility function for loading alist of records from a directory. It is assumed that the records are csv files.
        Only the files with the extension .csv are loaded.
        The function returns a list of tuples with the dataframe, the name of the record and the path to the record.
        The name of the record is the name of the file without the extension.
        The path to the record is the full path to the file.
        The function also sorts the records by name.

        >>> path = './test/records/raw/event1/group1/'

        >>> rawProjectsPath = './test/records/raw/'
        >>> procProjectsPath = './test/records/proc/'   
        >>> allowedProjects = ['event1','event2'] 
        >>> processes = ['preprocessed-VR-sessions','preprocessed-VR-sessions-gated'] 
        >>> dataContainer = DataContainer(rawProjectsPath, procProjectsPath, allowedProjects, processes)

        >>> dfs = dataContainer.get_records(path)

        >>> [(df[0].shape, df[1], df[2]) for df in dfs] 
        [((100, 11), 'U1', './test/records/raw/event1/group1/U1.csv'), ((100, 11), 'U2', './test/records/raw/event1/group1/U2.csv'), ((100, 11), 'U3', './test/records/raw/event1/group1/U3.csv'), ((100, 11), 'U4', './test/records/raw/event1/group1/U4.csv')]


        """
        dfs = []
        record_names = os.listdir(path)
        record_names.sort()
        for record_name in record_names:
            record_path = os.path.join(path, record_name)
            if os.path.isfile(record_path) and record_path.endswith('.csv'):
                df = pd.read_csv(record_path, skipinitialspace=True)
                record_name = record_name.split('.')[0]
                dfs.append([df,record_name,record_path])
        return dfs


    def load_all(self, step):
        """
        Utility function for loading datastructure give the path of the directory with the projects.
        >>> rawProjectsPath = './test/records/raw/'
        >>> procProjectsPath = './test/records/proc/'   
        >>> allowedProjects = ['event1','event2'] 
        >>> processes = ['preprocessed-VR-sessions','preprocessed-VR-sessions-gated'] 
        >>> dataContainer = DataContainer(rawProjectsPath, procProjectsPath, allowedProjects, processes)
        >>> dataContainer.load_all('raw')
        >>> [(p.id, p.name,type(p)) for p in dataContainer.projects]
        [(1, 'event1', <class 'data_container.Project'>), (2, 'event2', <class 'data_container.Project'>)]
        >>> project = dataContainer.projects[0]
        >>> [(g.id, g.name,type(g)) for g in project.groups]
        [(1, 'group1', <class 'data_container.Group'>), (2, 'group2', <class 'data_container.Group'>)]
        >>> group = project.groups[0]
        >>> r = group.records[0]
        >>> type(r)
        <class 'data_container.Record'>
        >>> [(r.id, r.name, r.step,r.version) for r in group.records]
        [(1, 'U1', 'raw', None), (2, 'U2', 'raw', None), (3, 'U3', 'raw', None), (4, 'U4', 'raw', None)]
        >>> r = dataContainer.records[0]
        >>> type(r)
        <class 'data_container.Record'>

        >>> dataContainer.load_all('proc')
        >>> [(p.id, p.name, p.step) for p in dataContainer.projects]
        [(1, 'event1', 'raw'), (2, 'event2', 'raw'), (3, 'event1', 'proc'), (4, 'event2', 'proc')]
        >>> project = dataContainer.projects[2]
        >>> type(project)
        <class 'data_container.Project'>
        >>> [(g.id, g.name, g.project.name,g.step,g.version) for g in project.groups]
        [(5, 'group1', 'event1', 'proc', 'preprocessed-VR-sessions'), (6, 'group1', 'event1', 'proc', 'preprocessed-VR-sessions-gated'), (7, 'group2', 'event1', 'proc', 'preprocessed-VR-sessions'), (8, 'group2', 'event1', 'proc', 'preprocessed-VR-sessions-gated')]
        >>> group = project.groups[0]
        >>> type(group)
        <class 'data_container.Group'>
        >>> [(r.id, r.name, r.step,r.version) for r in group.records]
        [(8, 'U1-preprocessed', 'proc', 'preprocessed-VR-sessions'), (9, 'U2-preprocessed', 'proc', 'preprocessed-VR-sessions')]
        >>> r = group.records[0]
        >>> type(r) 
        <class 'data_container.Record'>
        >>> r.group.name
        'group1'
        >>> r = dataContainer.records[0]
        >>> type(r)
        <class 'data_container.Record'>

        """
        #projects = self.projects
        #groups = self.groups
        #records = self.records

        # Create proc projects dir for each raw project dir if it does not exist
        #print('Create proc projects dir for each raw project dir if it does not exist',project_dir, step)
        if step == 'raw':
            project_names = os.listdir(self.rawProjectsPath )
            project_names.sort()
            for project_name in project_names:
                #print('project_name',project_name)
                if project_name in self.allowedProjects:
                    # check if project path exists in proc/, otherwise create it
                    project_path = os.path.join(self.procProjectsPath, project_name)
                    #print('project_path',project_path)
                    if not os.path.exists(project_path):
                        #print('make project_path')
                        os.makedirs(project_path)

        # Create proc group dir for each raw goup dir if it does not exist
        if step == 'raw':
            project_names = os.listdir(self.rawProjectsPath )
            project_names.sort()
            for project_name in project_names:
                if project_name in self.allowedProjects:
                    project_path = os.path.join(self.rawProjectsPath , project_name)
                    if os.path.isdir(project_path):
                        group_names = os.listdir(project_path)
                        group_names.sort()
                        for group_name in group_names:
                            group_path = os.path.join(project_path, group_name)
                            #print('group_path',group_path)
                            #check if group path exists in proc/, otherwise create it
                            if os.path.isdir(group_path):
                                if not os.path.exists(os.path.join(self.procProjectsPath, project_name, group_name)):
                                    os.makedirs(os.path.join(self.procProjectsPath, project_name, group_name))
                                for ver in self.processes: #['preprocessed-VR-sessions','preprocessed-VR-sessions-gated']:
                                    if not os.path.exists(os.path.join(self.procProjectsPath, project_name, group_name, ver)):
                                        os.makedirs(os.path.join(self.procProjectsPath, project_name, group_name, ver))

        # Load projects

        if step == 'raw':
            project_dir = self.rawProjectsPath
        if step == 'proc':
            project_dir = self.procProjectsPath

        projectsInner = []
        i = len(self.projects) +1
        project_names = os.listdir(project_dir)
        project_names.sort()
        for project_name in project_names:
            project_path = os.path.join(project_dir, project_name)
            #print('project_path',project_path)
            if os.path.isdir(project_path):
                project = Project(i, f"{project_name}",project_path,step)
                project.step = step
                #print(project.name,project.step)
                i = i + 1
                projectsInner.append(project)
        #projects = projects + projectsInner
        #print('projectsInner', [(p.id, p.name, p.path) for p in projectsInner])
        

        # Load groups
        groupsInner = []
        i = len(self.groups) + 1
        if step == 'raw':
            for project in projectsInner:
                group_names = os.listdir(project.path)
                group_names.sort()
                for group_name in group_names:
                    group_path = os.path.join(project.path, group_name)
                    group_path = os.path.normpath(group_path)
                    #print('group_path',group_path)
                    #if os.path.isfile(group_path) and group_path.endswith('.csv'):
                    if os.path.isdir(group_path):
                        group = Group(i, f"{group_name}",group_path,step)
                        group.project = project
                        i = i + 1
                        groupsInner.append(group)
                        project.add_group(group)
            #print('groupsInner', [(g.id, g.name, g.path) for g in groupsInner])

        if step == 'proc':
            for project in projectsInner:
                group_names = os.listdir(project.path)
                group_names.sort()
                #print('project',project.name,project.path,group_names)
                for group_name in group_names:
                    group_path = os.path.join(project.path, group_name)
                    group_path = os.path.normpath(group_path)
                    if os.path.isdir(group_path):
                        #print('group_path',group_path)
                        for ver in os.listdir(group_path):
                            ver_path = os.path.join(group_path, ver)
                            #print('ver_path',ver_path)
                            if os.path.isdir(ver_path):
                                group = Group(i, f"{group_name}", group_path, step)
                                group.set_ver(ver)
                                if group.parsFileExists():
                                    pars = group.loadPars()
                                else:
                                    pars = group.putPar()
                                #print(group_name,'pars',pars.keys())
                                if 'panoramic' in pars.keys(): group.set_panoramic(pars['panoramic'])
                                group.project = project
                                i = i + 1
                                groupsInner.append(group)
                                project.add_group(group)  
        #groups = groups + groupsInner  

        # Load records
        #recordsInner = []
        i = len(self.records) + 1
        if step == 'raw':
            for group in groupsInner:
                dfs = self.get_records(group.path)
                for df,record_name,record_path in dfs:
                    self.add_record(group,record_name,record_path, df)
                    #record = Record(i, record_name, record_path, 'raw', df)
                    #record.group = group
                    #record.project = group.project
                    #i = i + 1
                    #recordsInner.append(record)
                    #group.add_record(record)

        if step == 'proc':
            for group in groupsInner:
                #for ver in os.listdir(group.path):
                ver = group.version
                #print(group.name,'ver',ver)
                if ver is not None:
                    ver_path = os.path.join(group.path, ver)
                    if os.path.isdir(ver_path):
                        dfs = self.get_records(ver_path)
                        for df,record_name,record_path in dfs:                            
                            self.add_record(group,record_name,record_path, df,version=ver)
        #print('recordsInner', [(r.id, r.name, type(r)) for r in recordsInner])
        #records = records + recordsInner
        

        self.projects = self.projects + projectsInner
        self.groups = self.groups + groupsInner
        #self.records = self.records + recordsInner
    
    def link_records(self):
        """
        Link record to parent record and child records.
        
        Parameters:
        ----------
        records : list of Record objects    
        
        Returns variables:
        ------- 
        records : list of Record objects
            List of Record objects with linked parent and child records.
        
        
        Example:
        ---------
        >>> rawProjectsPath = './test/records/raw/'
        >>> procProjectsPath = './test/records/proc/'   
        >>> allowedProjects = ['event1','event2'] 
        >>> processes = ['preprocessed-VR-sessions','preprocessed-VR-sessions-gated'] 
        >>> dataContainer = DataContainer(rawProjectsPath, procProjectsPath, allowedProjects, processes)
        >>> dataContainer.load_all('raw')
        >>> r = dataContainer.records[0]
        >>> print('r',r.name,type(r))
        r U1 <class 'data_container.Record'>
        >>> dataContainer.load_all('proc')
        >>> r = dataContainer.records[0]
        >>> print('r1',r.name,r.group.name,r.project.name,r.step,r.version)
        r1 U1 group1 event1 raw None
        >>> r = dataContainer.records[1]
        >>> print('r2',r.name,r.group.name,r.project.name,r.step,r.version)
        r2 U2 group1 event1 raw None
        >>> dataContainer.link_records()
        >>> records = dataContainer.records
        >>> [(r.id, r.name, r.step, r.version, r.parent_record.id, r.parent_record.name)  for r in records if r.parent_record is not None]        
        [(8, 'U1-preprocessed', 'proc', 'preprocessed-VR-sessions', 1, 'U1'), (9, 'U2-preprocessed', 'proc', 'preprocessed-VR-sessions', 2, 'U2'), (10, 'U2-preprocessed', 'proc', 'preprocessed-VR-sessions-gated', 9, 'U2-preprocessed')]
        
        
        """
        # link records to parent record and child records
        for r in self.records:
            if r.step == 'raw':
                #print('r',r.name,r.group.name,r.project.name,r.step,r.version)
                for r2 in self.records:
                    #if (r2.step == 'proc') and (r2.project.name == r.project.name) and (r2.group.name == r.group.name) and (r2.name.startswith(r.name)) and (r2.version == 'preprocessed-VR-sessions'):
                    #    print('r2',r2.name,r2.group.name,r2.project.name,r2.step,r2.version,r2.name.startswith(r.name))
                    if (r2.step == 'proc') and (r2.project.name == r.project.name) and (r2.group.name == r.group.name) and (r2.name.startswith(r.name)) and (r2.version == 'preprocessed-VR-sessions'):
                        r2.parent_record = r
                        r.add_child_record(r2)
                        #print('r2',r2.id,r2.name,r2.group.name,r2.project.name,r2.step,r2.version,r.child_records)
            if r.step == 'proc' and r.version == 'preprocessed-VR-sessions':
                for r2 in self.records:
                    if (r2.step == 'proc') and (r2.project.name == r.project.name) and (r2.group.name == r.group.name) and (r2.name.startswith(r.name)) and (r2.version == 'preprocessed-VR-sessions-gated'):
                        r2.parent_record = r
                        r.add_child_record(r2)

    def update_put_group_pars(self,group):
        # Check if group has a pars.json file and update it or create it
        assert isinstance(group, Group) and group.step == 'proc', 'group must be a Group object and step must be proc'
        #print('group.parent_group path',group.parent_group.path)
        if group.parsFileExists():
            pars = group.loadPars()
        else:
            pars = group.putPar()
        #print('pars',pars)
        keeperPath = os.path.normpath(os.path.join( group.path,group.version) ) # group.path +'/preprocessed-VR-sessions'
        if not os.path.exists(keeperPath):
            os.makedirs(keeperPath)
        keepers = os.listdir(keeperPath)   
        return pars,keepers

    def update_put_groups_pars(self):
        # Check if groups have a pars.json file and update it or create it
        groups = self.groups
        procGroups = [g for g in groups if (g.step == 'proc') and (g.version == 'preprocessed-VR-sessions')]
        for group in procGroups:
            pars,keepers = self.update_put_group_pars(group)
            #print('keepers',keepers)
            for g in group.records:
                assert g.name+'.csv' in keepers, 'record '+g.name+' not in keepers'+str(keepers)

    def update_put_record_pars(self,record):#,keepers):
        #find out if allready preprocessed. If trough check if csv and info in json match
        # Check if record group has a pars.json file and update it or create it
        assert isinstance(record, Record) and record.step == 'proc', 'record must be a Record object and step must be proc'
        assert record.group.parsFileExists(), 'it is assumed that pars are loaded in the group before that in the record with update_put_group_pars or update_put_groups_pars'
        if record.isProcRecordInProcFile():
            record.loadProcRecordFromProcFile()
        else:
            record.putProcRecordInProcFile()

    def update_put_records_pars(self):
        procRecords = [r for r in self.records if (r.step == 'proc') and (r.version == 'preprocessed-VR-sessions')]
        for record in procRecords:
            self.update_put_record_pars(record)

if __name__ == "__main__":
    rawProjectsPath = './test/records/raw/'
    procProjectsPath = './test/records/proc/'   
    allowedProjects = ['event1','event2'] 
    processes = ['preprocessed-VR-sessions','preprocessed-VR-sessions-gated'] 
    dataContainer = DataContainer(rawProjectsPath, procProjectsPath, allowedProjects, processes)
    dataContainer.load_all('raw')

    print('projects')
    print([(p.id, p.name,type(p)) for p in dataContainer.projects])
    print('groups')
    print([(g.id, g.name,type(g)) for g in dataContainer.groups])
    print('records')
    print([(r.id, r.name,type(r)) for r in dataContainer.records])
