from fastapi import APIRouter, Query, HTTPException, Depends

router = APIRouter()

@router.get("/test")
def hello():
    return "hello"

@router.get("/datasets")
def list_datasets():
    return "TBA"

@router.get("/{dataset}/dataset-config")
def dataset_config(dataset: str):
    return "TBA"

@router.get("/{dataset}/records")
def get_dataset_records(dataset: str):
    return "TBA"

@router.get("/{dataset}/records/download")
def download_dataset_records(dataset: str):
    return "TBA"
