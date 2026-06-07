"""
KoBERT (RobertaForSequenceClassification) 추론 모듈

모델 파일 구성 (model/ 디렉토리):
  config.json          — RobertaForSequenceClassification 설정
  model.safetensors    — 학습된 가중치
  tokenizer.json       — Fast tokenizer vocab/rules
  tokenizer_config.json
  threshold.txt        — 최적 분류 임계값 (0.8272...)
"""

import pathlib
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

MODEL_DIR = pathlib.Path(__file__).parent / 'model'

_model       = None
_tokenizer   = None
_threshold   = 0.5   # threshold.txt에서 로드됨

# Temperature Scaling: 값이 클수록 확률 분포가 퍼져서 민감도 낮아짐
# 1.0 = 원본 그대로 / 2.0 = 중간 / 3.0~4.0 = 덜 민감
TEMPERATURE  = 3.0


# ─── 모델 로딩 ───────────────────────────────────────────────────────────────

def load_model():
    global _model, _tokenizer, _threshold

    # 임계값 로드
    threshold_file = MODEL_DIR / 'threshold.txt'
    if threshold_file.exists():
        _threshold = float(threshold_file.read_text().strip())

    # 토크나이저 로드
    _tokenizer = AutoTokenizer.from_pretrained(
        str(MODEL_DIR),
        use_fast=True,
    )

    # 모델 로드
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    _model = AutoModelForSequenceClassification.from_pretrained(
        str(MODEL_DIR),
    )
    _model.to(device)
    _model.eval()

    print(f'[모델 서버] KoBERT 로드 완료 | device={device} | threshold={_threshold:.4f}')


def get_model():
    return _model, _tokenizer, _threshold


# ─── 텍스트 → 확률 ──────────────────────────────────────────────────────────

def predict_from_text(text: str) -> float:
    """
    텍스트를 받아 보이스피싱 확률 (0.0~1.0)을 반환합니다.
    label 1 = 보이스피싱, label 0 = 정상 (RobertaForSequenceClassification 기본 컨벤션)
    """
    model, tokenizer, _ = get_model()

    if model is None or tokenizer is None:
        return _rule_based_fallback(text)

    device = next(model.parameters()).device

    inputs = tokenizer(
        text,
        return_tensors='pt',
        truncation=True,
        max_length=512,
        padding=True,
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        logits = model(**inputs).logits          # shape: (1, num_labels)

    probs = torch.softmax(logits / TEMPERATURE, dim=-1)[0]  # temperature scaling

    # num_labels == 2 가정: index 1 = 보이스피싱 확률
    phishing_prob = probs[1].item() if probs.shape[0] >= 2 else probs[0].item()
    return float(phishing_prob)


# ─── 오디오 → (확률, 스크립트) ──────────────────────────────────────────────

def transcribe_audio(audio_path: str) -> str:
    """
    오디오 → 텍스트 (ASR).
    Whisper 등 ASR 모델을 사용하려면 아래 TODO를 채우세요.

    예시 (faster-whisper):
        from faster_whisper import WhisperModel
        asr = WhisperModel('small', device='cpu')
        segments, _ = asr.transcribe(audio_path, language='ko')
        return ' '.join(s.text for s in segments)
    """
    # ── TODO: ASR 구현 ────────────────────────────────────────────────────────
    return ''


def predict_from_audio(audio_path: str) -> tuple[float, str]:
    transcript = transcribe_audio(audio_path)
    prob = predict_from_text(transcript) if transcript else 0.0
    return prob, transcript


# ─── 레이블 변환 (모델 threshold 반영) ──────────────────────────────────────

def probability_to_label(prob: float) -> str:
    """
    threshold.txt에 저장된 최적 임계값 기준으로 레이블 결정.
      prob >= threshold       → '위험'  (모델이 피싱으로 확신하는 구간)
      prob >= threshold * 0.5 → '의심'  (경계 구간)
      prob <  threshold * 0.5 → '안전'
    """
    _, _, threshold = get_model()
    if prob >= threshold:
        return '위험'
    if prob >= threshold * 0.5:
        return '의심'
    return '안전'


# ─── 규칙 기반 폴백 (모델 로드 실패 시) ─────────────────────────────────────

_PHISHING_KEYWORDS = [
    '계좌번호', '이체', '송금', '검사', '경찰', '금감원', '금융감독원',
    '납치', '구속', '범죄', '피의자', '수사', '안전계좌', '대출 상환',
    '환급', '세금 환급', '카드 정지', '개인정보', '주민등록번호',
    '비밀번호', 'OTP', '공인인증', '원격 접속',
]
_SAFE_KEYWORDS = ['감사합니다', '안녕하세요', '상담원', '고객센터']


def _rule_based_fallback(text: str) -> float:
    hit  = sum(1 for kw in _PHISHING_KEYWORDS if kw in text)
    safe = sum(1 for kw in _SAFE_KEYWORDS    if kw in text)
    return max(min(hit * 0.12 - safe * 0.05, 1.0), 0.0)
