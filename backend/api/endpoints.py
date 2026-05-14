from fastapi import APIRouter, Query, HTTPException, Depends

from core.config import get_config
from services.dataset import fetch_config, records

router = APIRouter()

config = get_config()


@router.get("/datasets")
def list_datasets():
    return config

@router.get("/{dataset}/dataset-config")
def dataset_config(dataset: str):
    return fetch_config(dataset)

@router.get("/{dataset}/records")
def get_dataset_records(dataset: str):
    return records(dataset)

@router.get("/{dataset}/records/download")
def download_dataset_records(dataset: str):
    return "TBA"
