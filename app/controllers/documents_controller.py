import logging

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies.auth import require_active_user, require_admin_user
from app.models.document import Document
from app.models.user import User
from app.operations.documents.save import Save as SaveDocument
from app.operations.system.inquire import Inquire
from app.schemas.document import DocumentCollection, DocumentOut
from app.schemas.system import InquirePayload
from app.services.document_queue import configured_sqs_queue, enqueue_document
from app.storage import build_public_url, delete_file


ITEMS_PER_PAGE = 20
router = APIRouter(tags=["documents"])
logger = logging.getLogger("talaragapi")


@router.get("/documents", response_model=DocumentCollection)
def index(
    request: Request,
    query: str | None = None,
    document_type: str | None = None,
    page: int = 1,
    per_page: int = ITEMS_PER_PAGE,
    _current_user: User = Depends(require_active_user),
    session: Session = Depends(get_db),
):
    filters = _document_filters(query=query, document_type=document_type)
    return _document_collection_response(request, session, filters, page, per_page)


@router.get("/documents/{document_id}", response_model=DocumentOut)
def show(
    request: Request,
    document_id: str,
    _current_user: User = Depends(require_active_user),
    session: Session = Depends(get_db),
):
    document = session.get(Document, document_id)
    if document is None:
        return JSONResponse(status_code=404, content={"message": "not found"})
    return _serialize_document(document, request.app.state.settings)


@router.post("/documents", response_model=DocumentOut, status_code=201)
def create(
    request: Request,
    name: str | None = Form(default=None),
    description: str | None = Form(default=None),
    document_type: str | None = Form(default=None),
    status: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    _current_user: User = Depends(require_active_user),
    session: Session = Depends(get_db),
):
    cmd = SaveDocument(
        session=session,
        settings=request.app.state.settings,
        name=name,
        description=description,
        document_type=document_type,
        status=status,
        file=file,
    )
    cmd.execute()

    if cmd.valid():
        _enqueue_document_if_pending(cmd.document, request.app.state.settings)
        return _serialize_document(cmd.document, request.app.state.settings)
    return JSONResponse(status_code=422, content=cmd.payload)


@router.put("/documents/{document_id}", response_model=DocumentOut)
def update(
    request: Request,
    document_id: str,
    name: str | None = Form(default=None),
    description: str | None = Form(default=None),
    document_type: str | None = Form(default=None),
    status: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    _current_user: User = Depends(require_active_user),
    session: Session = Depends(get_db),
):
    document = session.get(Document, document_id)
    if document is None:
        return JSONResponse(status_code=404, content={"message": "not found"})

    cmd = SaveDocument(
        session=session,
        settings=request.app.state.settings,
        document=document,
        name=name if name is not None else document.name,
        description=description if description is not None else document.description,
        document_type=document_type if document_type is not None else document.document_type,
        status=status if status is not None else document.status,
        file=file,
    )
    cmd.execute()

    if cmd.valid():
        _enqueue_document_if_pending(cmd.document, request.app.state.settings, file_uploaded=file is not None)
        return _serialize_document(cmd.document, request.app.state.settings)
    return JSONResponse(status_code=422, content=cmd.payload)


@router.delete("/documents/{document_id}")
def delete(
    request: Request,
    document_id: str,
    _current_user: User = Depends(require_active_user),
    session: Session = Depends(get_db),
):
    document = session.get(Document, document_id)
    if document is None:
        return JSONResponse(status_code=404, content={"message": "not found"})

    storage_key = document.storage_key
    session.delete(document)
    session.commit()
    if storage_key:
        delete_file(storage_key, request.app.state.settings)
    return {"message": "ok"}


@router.post("/documents/{document_id}/rerun", response_model=DocumentOut)
def rerun(
    request: Request,
    document_id: str,
    _current_user: User = Depends(require_admin_user),
    session: Session = Depends(get_db),
):
    document = session.get(Document, document_id)
    if document is None:
        return JSONResponse(status_code=404, content={"message": "not found"})
    if document.status not in {"pending", "failed"}:
        logger.warning("Rejected rerun for document_id=%s because status=%s", document.id, document.status)
        return JSONResponse(status_code=422, content={"message": "document must be pending or failed"})
    if not document.storage_key:
        logger.warning("Rejected rerun for document_id=%s because storage_key is missing", document.id)
        return JSONResponse(status_code=422, content={"message": "document is missing a storage key"})
    if not configured_sqs_queue():
        logger.warning("Rejected rerun for document_id=%s because SQS_QUEUE is not configured", document.id)
        return JSONResponse(status_code=503, content={"message": "SQS_QUEUE is not configured"})

    if document.status == "failed":
        document.status = "pending"
        session.add(document)
        session.commit()
        session.refresh(document)

    logger.info("Re-run requested for document_id=%s key=%s", document.id, document.storage_key)
    enqueue_document(request.app.state.settings, document.id, document.storage_key)
    return _serialize_document(document, request.app.state.settings)


@router.get("/public/documents", response_model=DocumentCollection)
def public_index(
    request: Request,
    query: str | None = None,
    document_type: str | None = None,
    page: int = 1,
    per_page: int = ITEMS_PER_PAGE,
    session: Session = Depends(get_db),
):
    filters = _document_filters(query=query, document_type=document_type)
    return _document_collection_response(request, session, filters, page, per_page)


@router.get("/public/document_types")
def public_document_types(request: Request):
    return {"document_types": request.app.state.settings.DOCUMENT_TYPES}


@router.post("/inquire")
def inquire(
    request: Request,
    payload: InquirePayload,
    session: Session = Depends(get_db),
):
    cmd = Inquire(
        session=session,
        settings=request.app.state.settings,
        query=payload.query,
        document_types=payload.document_types,
        k=payload.k,
    )
    cmd.execute()

    if cmd.valid():
        return StreamingResponse(
            _stream_text(cmd.answer, request.app.state.settings.INFERENCE_STREAM_CHUNK_SIZE),
            media_type="text/plain",
        )
    return JSONResponse(status_code=422, content=cmd.payload)


def _document_collection_response(request, session, filters, page, per_page):
    count_stmt = select(func.count()).select_from(Document)
    documents_stmt = select(Document).order_by(Document.created_at.desc())

    for entry in filters:
        count_stmt = count_stmt.where(entry)
        documents_stmt = documents_stmt.where(entry)

    total = session.scalar(count_stmt) or 0
    total_pages = max((total + per_page - 1) // per_page, 1)
    records = (
        session.execute(documents_stmt.offset((page - 1) * per_page).limit(per_page)).scalars().all()
        if total > 0
        else []
    )
    return {
        "records": [_serialize_document(record, request.app.state.settings) for record in records],
        "total_pages": total_pages,
        "current_page": page,
        "next_page": page + 1 if page < total_pages else None,
        "prev_page": page - 1 if page > 1 else None,
    }


def _document_filters(*, query=None, document_type=None):
    filters = []
    if query:
        pattern = f"%{query}%"
        filters.append(
            or_(
                Document.name.ilike(pattern),
                Document.description.ilike(pattern),
                Document.original_filename.ilike(pattern),
            )
        )
    if document_type:
        filters.append(Document.document_type == document_type)
    return filters


def _serialize_document(document, settings):
    return document.to_dict(download_url=build_public_url(document.storage_key, settings))


def _enqueue_document_if_pending(document, settings, file_uploaded=True):
    if not file_uploaded:
        logger.info("Skipping enqueue for document_id=%s because no new file was uploaded", document.id)
        return False
    if document.status != "pending":
        logger.info("Skipping enqueue for document_id=%s because status=%s", document.id, document.status)
        return False
    if not document.storage_key:
        logger.warning("Skipping enqueue for document_id=%s because storage_key is missing", document.id)
        return False
    if not configured_sqs_queue():
        logger.warning("Skipping enqueue for document_id=%s because SQS_QUEUE is not configured", document.id)
        return False
    return enqueue_document(settings, document.id, document.storage_key)


def _stream_text(text, chunk_size):
    for index in range(0, len(text or ""), max(int(chunk_size or 1), 1)):
        yield text[index : index + max(int(chunk_size or 1), 1)]
