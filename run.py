import uvicorn
import json

if __name__ == "__main__":
    with open('config.json') as f:
        d = json.load(f)
    FASTAPI_URL_base = d['FASTAPI_URL_base']
    FASTAPI_PORT = d['FASTAPI_PORT']
    FASTAPI_URL = f"http://{FASTAPI_URL_base}:{FASTAPI_PORT}/api"
    print(f"Starting FastAPI server at {FASTAPI_URL}")

    uvicorn.run("app.main:app", host=FASTAPI_URL_base, port=FASTAPI_PORT, reload=True, log_level="debug")