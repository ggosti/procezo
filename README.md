# procezo
Procezo is a fullstack Python application for time-series CSV data analytics. In Procezo time-series CSV data are called records.  Records are organized by project and group folders. It features a FastAPI backend and a Plotly Dash frontend. The system is designed for robustness, scalability, and clarity in handling structured CSV datasets.


## Features

- File-tree-based organization: `data/project/group/*.csv`
- Simple deployment of interfaces and Jupyter Notebooks for time-series data process modules (filtering/cleaning recods) and aggregate modules (analytics and machine learning models)
- Dash frontend with dropdown filters, tables, and plots
- REST API with FastAPI for project/group/data access
- Modular architecture with shared data container

## Project structure

procezo/
├── app/ # FastAPI backend
│ ├── api/ # API routes
│ ├── core/ # Global state, configuration
│ ├── services/ # Domain logic (DataContainer, etc.)
│ └── main.py # FastAPI app entrypoint
│
├── dash_app/ # Dash frontend
│ ├── layout.py # Dash layout
│ ├── callbacks.py # Interactivity
│ └── app.py # Mounted Dash app
│
├── data/ # Your CSV data (project/group/*.csv)
│ └── project1/
│ └── groupA/
│ └── data.csv
│
├── run.py # Entrypoint script for running app
├── requirements.txt # Dependencies
└── README.md # This file

## Installation

1. **Clone the repo**

```bash
 git clone https://github.com/your-user/procezo.git
 cd procezo
```

2. **Create the virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

## Running the App

Start the app locally:
```bash
python run.py
```
This sets up the FastAPI backend and a Plotly Dash frontend
- FastAPI: http://localhost:8000/docs
- Dash frontend: http://localhost:8000/dashboard

## Architecture Overview

Procezo uses a layered architecture:
- CSV File Tree → loaded into → DataContainer
- FastAPI API reads from DataContainer and exposes endpoints
- Dash interacts only through FastAPI APIs for a robust, decoupled design

See /api/... for endpoints and /dashboard for the interactive UI.
  
## Example API Calls:
- List projects:

```
GET /api/projects
```
- List groups in a project:

```
GET /api/groups/{project}
```

- List records (CSVs) in a group:

```
GET /api/files/{project}/{group}
```
- Get CSV data as JSON:

```
GET /api/data/{project}/{group}/{filename}
```

##Development Notes

Procezo is part of the Interlupo pipeline, it can either be used together with Kapto or it can be integrated into a custom pipeline.
If it is used as a standalone :
- To add data: place CSVs under data/<project>/<group>/
- To reload data: restart the app (TODO: implement live reload logic)
- To modify interfaces: edit dash_app/layout.py and callbacks.py
- To implement new notebooks: edit example Jupyter Notebbok

- 
