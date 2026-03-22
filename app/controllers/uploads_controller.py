from fastapi import APIRouter, File, Form, Request, UploadFile

from app.schemas.upload import UploadResponse
from app.storage import local_file_response, store_file


router = APIRouter()


@router.post("/uploads", response_model=UploadResponse, status_code=201)
def create_upload(request: Request, file: UploadFile = File(...), filename: str | None = Form(default=None)):
    result = store_file(file, request.app.state.settings, filename=filename)
    return {"file": result}


@router.get("/files/{key:path}")
def show_file(request: Request, key: str):
    return local_file_response(key, request.app.state.settings)
