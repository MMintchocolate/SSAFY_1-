import os
import tempfile

from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import status

from .inference import predict_from_text, predict_from_audio, probability_to_label
from .models import PhishingAnalysis


ALLOWED_AUDIO_EXT = {'.wav', '.mp3', '.m4a', '.ogg', '.flac'}
ALLOWED_TEXT_EXT  = {'.txt'}
MAX_FILE_SIZE     = 50 * 1024 * 1024  # 50 MB


@api_view(['POST'])
@parser_classes([MultiPartParser])
def analyze(request):
    """
    보이스피싱 분석 엔드포인트

    Request (multipart/form-data):
        file: 오디오 파일(.wav/.mp3/.m4a) 또는 텍스트 파일(.txt)

    Response:
        {
            "probability": 0.87,        # 0.0 ~ 1.0
            "label": "위험",             # "안전" | "의심" | "위험"
            "transcript": "...",        # 오디오일 경우 변환된 텍스트
            "file_type": "audio",       # "audio" | "text"
            "filename": "call.wav"
        }
    """
    uploaded = request.FILES.get('file')
    if not uploaded:
        return Response({'error': '파일이 필요합니다. (file 필드)'}, status=status.HTTP_400_BAD_REQUEST)

    if uploaded.size > MAX_FILE_SIZE:
        return Response({'error': '파일 크기는 50MB 이하여야 합니다.'}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

    ext = os.path.splitext(uploaded.name)[1].lower()
    if ext not in ALLOWED_AUDIO_EXT | ALLOWED_TEXT_EXT:
        return Response(
            {'error': f'지원하지 않는 파일 형식입니다. 지원 형식: .txt, .wav, .mp3, .m4a'},
            status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )

    try:
        if ext in ALLOWED_TEXT_EXT:
            # ── 텍스트 파일 분석 ────────────────────────────────────────────
            raw = uploaded.read()
            for enc in ('utf-8', 'euc-kr', 'cp949'):
                try:
                    text = raw.decode(enc)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                return Response({'error': '텍스트 인코딩을 인식할 수 없습니다. UTF-8 또는 EUC-KR 파일을 사용해 주세요.'}, status=status.HTTP_400_BAD_REQUEST)

            probability = predict_from_text(text)
            transcript  = text
            file_type   = 'text'

        else:
            # ── 오디오 파일 분석 ────────────────────────────────────────────
            suffix = ext
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                for chunk in uploaded.chunks():
                    tmp.write(chunk)
                tmp_path = tmp.name

            try:
                probability, transcript = predict_from_audio(tmp_path)
            finally:
                os.unlink(tmp_path)

            file_type = 'audio'

        label = probability_to_label(probability)

        # 분석 내역 DB 저장
        PhishingAnalysis.objects.create(
            original_filename=uploaded.name,
            file_type=file_type,
            transcript=transcript,
            probability=probability,
            label=label,
        )

        return Response({
            'probability': round(probability, 4),
            'label':       label,
            'transcript':  transcript,
            'file_type':   file_type,
            'filename':    uploaded.name,
        })

    except Exception as e:
        return Response({'error': f'분석 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def history(request):
    """최근 분석 내역 20건 반환"""
    records = PhishingAnalysis.objects.all()[:20]
    data = [
        {
            'id':        r.id,
            'filename':  r.original_filename,
            'file_type': r.file_type,
            'label':     r.label,
            'probability': round(r.probability, 4),
            'created_at': r.created_at.isoformat(),
        }
        for r in records
    ]
    return Response(data)
