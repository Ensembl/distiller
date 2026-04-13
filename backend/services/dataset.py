from core.database import get_db_connection
from models.dataset import DatasetConfig


def fetch_config(dataset_path) -> DatasetConfig:
    conn = get_db_connection(dataset_path)