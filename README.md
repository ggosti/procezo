# procezo
Procezo is a fullstack Python application for time-series CSV data analytics. In Procezo, time-series CSV data are called records, and they are organized by project and group folders. Procezo features a FastAPI backend and a Plotly Dash frontend. The system is designed for robustness, scalability, and clarity in handling structured CSV datasets.


## Features

- File-tree-based organization: `data/project/group/*.csv`
- Simple deployment of interfaces and Jupyter Notebooks for time-series data process modules (filtering/cleaning recods) and aggregate modules (analytics and machine learning models)
- Dash frontend with dropdown filters, tables, and plots
- REST API with FastAPI for project/group/data access
- Modular architecture with shared data container

## Project structure

```
procezo/
├── app/ # FastAPI backend
│  ├── api/ # API routes
│  ├── core/ # Global state, configuration
│  ├── services/ # Domain logic (DataContainer, etc.)
│  └── main.py # FastAPI app entrypoint
│
├── dash_app/ # Dash frontend
│  ├── layout.py # Dash layout
│  ├── callbacks.py # Interactivity
│  └── app.py # Mounted Dash app
│
├── data/ # Your record data (project/group/*.csv)
│  ├── records/
|     ├── proc/
|     └── raw/
│        ├── event1/
|        |   ├── group1/
|        |   |  ├── U1.csv
|        |   |  ├── U2.csv
|        |   |  ├── U3.csv
|        |   |  └── U4.csv
|        |   └── group2/
|        |      └── abc.csv
│        └── event2/
|            ├── group2/
|            |   └── abc.csv
|            └── group2/
|               └── abc.csv
│
├── run.py # Entrypoint script for running app
├── requirements.txt # Dependencies
└── README.md # This file
```

## Installation

1. **Clone the repo**

```bash
 git clone https://github.com/ggosti/procezo.git
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
## Test

This web app is based on a data structure made on the class DataContainer defined in `app/services/data_container.py`. 
models.py defines classes for projects, groups, and records.
To test DataContainer class:
```bash
python -m doctest app/services/data_container.py
```
To test api endpoints, use 
```bash
http://127.0.0.1:8000/docs
```

## Running the App

Star environment:
```bash
source venv/bin/activate  # or venv\Scripts\activate on Windows
```
Start the app locally:
```bash
python run.py
```

This sets up the FastAPI backend and a Plotly Dash frontend

- FastAPI: http://localhost:8000/docs

- Dash frontend: http://localhost:8000/dashboard

## Architecture Overview

Procezo uses a layered architecture:
- Records Tree → loaded into → DataContainer
- FastAPI API reads from DataContainer and exposes endpoints
- Dash interacts only through FastAPI APIs for a robust, decoupled design

See /api/... for endpoints and /dashboard for the interactive UI.
  
## Example API Calls

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
GET /api/records/{project}/{group}
```
- Get CSV data as JSON:

```
GET /api/record/{project}/{group}/{filename}
```

## Development Notes

Procezo is part of the Interlupo pipeline, it can either be used together with Kapto or it can be integrated into a custom pipeline.
If it is used as a standalone :
- To add data: place CSVs under data/<project>/<group>/
- To reload data: restart the app (TODO: implement live reload logic)
- To modify interfaces: edit dash_app/layout.py and callbacks.py
- To implement new notebooks: edit example Jupyter Notebook

## To Do / Ideas

- Add caching (e.g. Redis or TTL-based reloading)
- Add file upload support
- Support multi-user session states
- Dockerize the app for deployment

## License

GPL-3.0 License — see `LICENSE` file.

## Contributing
Contributions are welcome! Fork the repo, create a branch, and open a PR.
