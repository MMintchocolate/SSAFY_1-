"""
Django ↔ FastAPI 모델 서버 프록시 클라이언트

Django는 모델을 직접 로드하지 않습니다.
분석 요청을 FastAPI 모델 서버(MODEL_SERVER_URL)로 포워딩합니다.

[구조]
  Vue/모바일 → Django /api/voicephishing/analyze/ → FastAPI :8001/predict/...
"""

import requests
from django.conf import settings

MODEL_SERVER_URL = getattr(settings, 'MODEL_SERVER_URL', 'http://localhost:8001')
_TIMEOUT = 60  # 초 (대용량 오디오 감안)


# ─── 텍스트 분석 프록시 ──────────────────────────────────────────────────────

def predict_from_text(text: str) -> float:
    """FastAPI /predict/text 호출 → 확률 반환"""
    try:
        res = requests.post(
            f'{MODEL_SERVER_URL}/predict/text',
            json={'text': text},
            timeout=_TIMEOUT,
        )
        res.raise_for_status()
        return float(res.json()['probability'])
    except requests.exceptions.ConnectionError:
        raise RuntimeError('모델 서버에 연결할 수 없습니다. FastAPI 서버가 실행 중인지 확인하세요.')
    except requests.exceptions.HTTPError as e:
        detail = e.response.json().get('detail', str(e)) if e.response else str(e)
        raise RuntimeError(f'모델 서버 오류: {detail}')


# ─── 오디오 분석 프록시 ──────────────────────────────────────────────────────

def predict_from_audio(audio_path: str) -> tuple[float, str]:
    """FastAPI /predict/audio 호출 → (확률, 스크립트) 반환"""
    try:
        with open(audio_path, 'rb') as f:
            filename = audio_path.split('/')[-1].split('\\')[-1]
            res = requests.post(
                f'{MODEL_SERVER_URL}/predict/audio',
                files={'file': (filename, f)},
                timeout=_TIMEOUT,
            )
        res.raise_for_status()
        data = res.json()
        return float(data['probability']), data.get('transcript', '')
    except requests.exceptions.ConnectionError:
        raise RuntimeError('모델 서버에 연결할 수 없습니다. FastAPI 서버가 실행 중인지 확인하세요.')
    except requests.exceptions.HTTPError as e:
        detail = e.response.json().get('detail', str(e)) if e.response else str(e)
        raise RuntimeError(f'모델 서버 오류: {detail}')


# ─── 레이블 변환 ─────────────────────────────────────────────────────────────

def probability_to_label(prob: float) -> str:
    if prob >= 0.7: return '위험'
    if prob >= 0.4: return '의심'
    return '안전'
