# This script will create an endpoint that returns the publications of a user
from typing import Union
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from app.dblp_publication_model import generate_data

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/dblp-records/{date}")
def latest_dblp_records(date: str):
    return StreamingResponse(generate_data(date), media_type="text/plain")