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

