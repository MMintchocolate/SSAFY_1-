# 보이스피싱 탐지 모델 디렉토리

이 디렉토리에 학습된 모델 파일을 배치하세요.

## 모델 파일 배치

| 파일 | 설명 |
|------|------|
| `model.pt` | PyTorch 모델 (권장) |
| `model.pkl` | scikit-learn / 기타 pickle 모델 |
| `tokenizer/` | 토크나이저 파일 디렉토리 |
| `config.json` | 모델 설정 파일 |

## 연동 방법

모델 파일을 배치한 후 `../inference.py`의 TODO 블록을 채워주세요.

```python
# inference.py > _load_model() 함수 내부
import torch
_model = torch.load(MODEL_DIR / 'model.pt', map_location='cpu')
_model.eval()
```

## 지원 입력 형식

- **텍스트**: `.txt` 파일 (통화 스크립트)
- **오디오**: `.wav`, `.mp3`, `.m4a` (ASR → 텍스트 변환 후 분석)

## 프록시 구조 (모바일)

```
모바일 앱
    │  (HTTPS POST /api/voicephishing/analyze/)
    ▼
Django API 서버 (이 백엔드)
    │
    ▼
inference.py → 모델 추론
    │
    ▼
결과 반환 (probability, label, transcript)
```

모바일 앱에서는 파일을 업로드하면 서버에서 추론 후 결과를 받습니다.
온디바이스 추론이 아닌 **서버 사이드 추론** 방식입니다.
