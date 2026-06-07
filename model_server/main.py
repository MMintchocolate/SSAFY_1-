"""
보이스피싱 탐지 FastAPI 모델 서버

실행 방법:
    uvicorn main:app --host 0.0.0.0 --port 8001 --reload

엔드포인트:
    GET  /health           서버 상태 확인
    POST /predict/text     텍스트(스크립트) → 확률
    POST /predict/audio    오디오 파일 → 확률 + 스크립트
"""

import os
import tempfile
import pathlib
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from inference import (
    load_model,
    predict_from_text,
    predict_from_audio,
    probability_to_label,
)

MODEL_DIR = pathlib.Path(__file__).parent / 'model'


# ─── 앱 시작 시 모델 로드 ────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_model()        # 서버 시작 시 1회 로드
    yield
    # (shutdown 시 정리가 필요하면 여기에 추가)


app = FastAPI(
    title='보이스피싱 탐지 모델 서버',
    version='1.0.0',
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:8000'],  # Django만 허용 (직접 외부 노출 X)
    allow_methods=['GET', 'POST'],
    allow_headers=['*'],
)


# ─── 응답 스키마 ─────────────────────────────────────────────────────────────

class PredictResponse(BaseModel):
    probability: float
    label: str
    transcript: str = ''


# ─── 헬스 체크 ───────────────────────────────────────────────────────────────

@app.get('/health')
async def health():
    return {'status': 'ok', 'model_dir': str(MODEL_DIR)}


# ─── 텍스트 분석 ─────────────────────────────────────────────────────────────

class TextRequest(BaseModel):
    text: str

@app.post('/predict/text', response_model=PredictResponse)
async def predict_text(req: TextRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail='텍스트가 비어 있습니다.')
    try:
        prob = predict_from_text(req.text)
        return PredictResponse(
            probability=round(prob, 4),
            label=probability_to_label(prob),
            transcript=req.text,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── 오디오 분석 ─────────────────────────────────────────────────────────────

ALLOWED_AUDIO = {'.wav', '.mp3', '.m4a', '.ogg', '.flac'}

@app.post('/predict/audio', response_model=PredictResponse)
async def predict_audio(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_AUDIO:
        raise HTTPException(
            status_code=415,
            detail=f'지원하지 않는 오디오 형식입니다. 지원: {", ".join(ALLOWED_AUDIO)}',
        )
    try:
        content = await file.read()
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            prob, transcript = predict_from_audio(tmp_path)
        finally:
            os.unlink(tmp_path)

        return PredictResponse(
            probability=round(prob, 4),
            label=probability_to_label(prob),
            transcript=transcript,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
