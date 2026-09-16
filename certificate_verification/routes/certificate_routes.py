from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import shutil

from services.ocr_service import extract_text
from services.parser_service import parse_certificate_text

from services.qr_service import decode_qr
from services.verification_service import verify_qr_data

from database.db import find_certificate

router = APIRouter()

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@router.post("/certificate/upload")
async def upload_certificate(file: UploadFile = File(...)):

    if not file.filename.lower().endswith(
        (".pdf", ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif")
    ):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format"
        )

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        text = extract_text(file_path)
        certificate_data = parse_certificate_text(text)

        qr_results = decode_qr(file_path)

        verification = None

        if qr_results:
            qr_data = qr_results[0]

            if "issued_to" in qr_data:
                verification = verify_qr_data(
                    qr_data,
                    certificate_data
                )

        database_record = find_certificate(certificate_data)

        database_match = False

        if database_record:
            database_match = True

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Certificate processing failed: {str(e)}"
        )

    return {
        "message": "Certificate processed successfully",
        "filename": file.filename,
        "certificate": certificate_data,
        "qr_data": qr_results,
        "verification": verification,
        "database_match": database_match
    }