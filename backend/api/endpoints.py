from fastapi import APIRouter, Query, HTTPException, Depends

from core.config import get_config
from services.dataset import fetch_config, records
from models.payload import Payload

router = APIRouter()

config = get_config()


@router.get("/datasets")
def list_datasets():
    c_payload = config.dict()
    for d in c_payload["datasets"]:
        del d["path"]
    return c_payload

@router.get("/dataset/{dataset}/dataset-config")
def dataset_config(dataset: str):
    return fetch_config(dataset)

@router.get("/dataset/{dataset}/records")
def get_dataset_records(dataset: str, payload:Payload | None = None ):
    return records(dataset)

@router.post("/dataset/{dataset}/records")
def post_dataset_records(dataset: str, payload:Payload):
    return records(dataset,payload)

@router.get("/dataset/{dataset}/records/download")
def download_dataset_records(dataset: str):
    return "TBA"
