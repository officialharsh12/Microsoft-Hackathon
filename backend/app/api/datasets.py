import json
from typing import List, Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel

from app.api.reviews import analyze_dataset, upload_csv
from app.database import get_db_connection

router = APIRouter(prefix="/datasets", tags=["Datasets"])


class DatasetMappingRequest(BaseModel):
    text_column: str
    date_column: Optional[str] = None
    rating_column: Optional[str] = None
    id_column: Optional[str] = None
    platform_column: Optional[str] = None
    version_column: Optional[str] = None


@router.get("", response_model=List[dict])
async def list_datasets():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, filename, dataset_name, product_id, organization_id, status, is_demo, review_count, created_at FROM datasets ORDER BY created_at DESC"
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/{dataset_id}", response_model=dict)
async def get_dataset(dataset_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, filename, dataset_name, product_id, organization_id, status, is_demo, review_count, valid_row_count, invalid_row_count, duplicate_count, metadata, created_at, completed_at FROM datasets WHERE id = ?",
        (dataset_id,),
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Dataset not found")
    payload = dict(row)
    if payload.get("metadata"):
        try:
            payload["metadata"] = json.loads(payload["metadata"])
        except Exception:
            pass
    return payload


@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    return await upload_csv(file)


@router.post("/{dataset_id}/mapping")
async def map_dataset_columns(dataset_id: int, payload: DatasetMappingRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM datasets WHERE id = ?",
        (dataset_id,),
    )
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Dataset not found")

    metadata = {
        "selected_columns": {
            "text_column": payload.text_column,
            "date_column": payload.date_column,
            "rating_column": payload.rating_column,
            "id_column": payload.id_column,
            "platform_column": payload.platform_column,
            "version_column": payload.version_column,
        }
    }
    cursor.execute(
        "UPDATE datasets SET text_col = ?, date_col = ?, rating_col = ?, id_col = ?, platform_col = ?, version_col = ?, metadata = ? WHERE id = ?",
        (
            payload.text_column,
            payload.date_column,
            payload.rating_column,
            payload.id_column,
            payload.platform_column,
            payload.version_column,
            json.dumps(metadata),
            dataset_id,
        ),
    )
    conn.commit()
    conn.close()
    return {"dataset_id": dataset_id, "status": "mapping_saved", "mapping": metadata["selected_columns"]}


@router.post("/{dataset_id}/analyze")
async def analyze_dataset_route(dataset_id: int, payload: dict):
    from app.api.reviews import AnalysisRequest
    return await analyze_dataset(AnalysisRequest(dataset_id=dataset_id, **payload))
