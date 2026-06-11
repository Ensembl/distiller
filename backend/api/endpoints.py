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

@router.get("/{dataset}/dataset-config")
def dataset_config(dataset: str):
    return fetch_config(dataset)

@router.get("/{dataset}/records")
def get_dataset_records(dataset: str, payload:Payload | None ):
    return records(dataset)

@router.post("/{dataset}/records")
def post_dataset_records(dataset: str):
    return records(dataset)

@router.get("/{dataset}/records/download")
def download_dataset_records(dataset: str):
    return "TBA"
