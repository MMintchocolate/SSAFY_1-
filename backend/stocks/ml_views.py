import json
import re
import requests as req
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import yfinance as yf
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

MODEL_DIR = Path(__file__).resolve().parent.parent / 'ml_models'

FEAT_COLS = [
    'feat_ma_ratio', 'feat_rsi', 'feat_macd_hist', 'feat_bb_pos',
    'feat_return_1d', 'feat_return_3d', 'feat_return_5d',
    'feat_vol_ratio', 'feat_usd_idx_chg', 'feat_us_10y_chg',
]


def _yf_ticker(symbol: str) -> str:
    """종목 코드 → yfinance 티커 (한국 6자리 숫자 → .KS 접미사)"""
    s = symbol.strip().upper()
    if re.match(r'^\d{6}$', s):
        return s + '.KS'
    return s


def _safe_fn(symbol: str) -> str:
    """파일명용 안전 문자열"""
    return re.sub(r'[^\w]', '_', symbol.upper())


def _paths(symbol: str):
    fn = _safe_fn(symbol)
    return MODEL_DIR / f'{fn}_lgbm.pkl', MODEL_DIR / f'{fn}_lgbm_meta.json'


def _dl(ticker, start, end):
    import pandas as pd
    df = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
    return df


def _fetch_raw(stock_ticker: str, start, end):
    stock = _dl(stock_ticker, start, end)
    dxy   = _dl('DX-Y.NYB', start, end)
    tnx   = _dl('^TNX',     start, end)
    if stock.empty:
        raise ValueError(f'데이터 없음: {stock_ticker}')
    base = stock[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
    base = base.join(dxy['Close'].rename('DXY'), how='left')
    base = base.join(tnx['Close'].rename('TNX'), how='left')
    base['DXY'] = base['DXY'].ffill()
    base['TNX'] = base['TNX'].ffill()
    return base


def _build_features(base):
    close = base['Close']
    base['feat_ma_ratio']    = close.rolling(50).mean() / close.rolling(200).mean()
    delta = close.diff()
    gain  = delta.where(delta > 0, 0)
    loss  = -delta.where(delta < 0, 0)
    base['feat_rsi']         = 100 - (100 / (1 + gain.rolling(14).mean() / (loss.rolling(14).mean() + 1e-9)))
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd  = ema12 - ema26
    base['feat_macd_hist']   = macd - macd.ewm(span=9, adjust=False).mean()
    ma20     = close.rolling(20).mean()
    std20    = close.rolling(20).std()
    bb_upper = ma20 + 2 * std20
    bb_lower = ma20 - 2 * std20
    base['feat_bb_pos']      = (close - bb_lower) / (bb_upper - bb_lower + 1e-9)
    base['feat_return_1d']   = close.pct_change(1)
    base['feat_return_3d']   = close.pct_change(3)
    base['feat_return_5d']   = close.pct_change(5)
    base['feat_vol_ratio']   = base['Volume'] / (base['Volume'].rolling(5).mean() + 1e-9)
    base['feat_usd_idx_chg'] = base['DXY'].pct_change(1)
    base['feat_us_10y_chg']  = base['TNX'].pct_change(1)
    return base


def _label(df, tp=0.05, sl=0.025, days=5):
    closes = df['Close'].values
    labels = []
    for i in range(len(closes)):
        if i + days >= len(closes):
            labels.append(float('nan'))
            continue
        entry = closes[i]; label = 0
        for j in range(1, days + 1):
            ret = (closes[i + j] - entry) / entry
            if ret >= tp:    label = 1; break
            elif ret <= -sl: label = 2; break
        labels.append(label)
    df['label'] = labels
    return df


@api_view(['POST'])
def ml_train(request):
    """
    POST /api/stocks/ml/train/?symbol=TSLA
    POST /api/stocks/ml/train/?symbol=005930
    데이터 수집 → 피처 → Triple Barrier 레이블 → LightGBM 학습 → 모델 저장
    """
    symbol = (request.GET.get('symbol') or request.data.get('symbol', '')).strip().upper()
    if not symbol:
        return Response({'error': 'symbol 파라미터가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        import lightgbm as lgb
        import joblib
        from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
    except ImportError as e:
        return Response({'error': f'패키지 미설치: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    try:
        ticker = _yf_ticker(symbol)
        end    = datetime.today()
        start  = end - timedelta(days=5 * 365 + 60)

        base = _fetch_raw(ticker, start, end)
        base = _build_features(base)
        base = _label(base, tp=0.05, sl=0.025, days=5)

        df = base[FEAT_COLS + ['label']].dropna().copy()
        if df.empty:
            return Response({'error': f'{symbol}: 유효 데이터 없음 (상장 기간 부족 등)'}, status=status.HTTP_400_BAD_REQUEST)
        df['label'] = df['label'].astype(int)

        X = df[FEAT_COLS]
        y = df['label']
        split   = max(1, int(len(X) * 0.8))
        X_train, X_test = X.iloc[:split], X.iloc[split:]
        y_train, y_test = y.iloc[:split], y.iloc[split:]

        model = lgb.LGBMClassifier(
            n_estimators=100, learning_rate=0.05,
            max_depth=4, num_leaves=15,
            class_weight='balanced', random_state=42, verbosity=-1,
        )
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        acc    = float(accuracy_score(y_test, y_pred))
        report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
        cm     = confusion_matrix(y_test, y_pred, labels=[0, 1, 2]).tolist()

        feat_imp = sorted(
            [{'feature': f, 'importance': int(v)}
             for f, v in zip(FEAT_COLS, model.feature_importances_)],
            key=lambda x: x['importance'], reverse=True,
        )

        MODEL_DIR.mkdir(exist_ok=True)
        model_path, meta_path = _paths(symbol)
        joblib.dump(model, model_path)

        label_map = {'0': '관망(0)', '1': '매수(1)', '2': '매도(2)'}
        per_class = {
            label_map[k]: {
                'precision': round(v['precision'], 3),
                'recall':    round(v['recall'],    3),
                'f1':        round(v['f1-score'],  3),
                'support':   int(v['support']),
            }
            for k, v in report.items() if k in ('0', '1', '2')
        }

        meta = {
            'symbol':     symbol,
            'yf_ticker':  ticker,
            'trained_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'total_rows': len(df),
            'train_rows': len(X_train),
            'test_rows':  len(X_test),
            'accuracy':   round(acc, 4),
            'class_dist': {str(k): int(v) for k, v in y.value_counts().sort_index().items()},
            'feat_imp':   feat_imp,
        }
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2))

        return Response({**meta, 'per_class': per_class, 'confusion_matrix': cm})

    except Exception as e:
        import traceback; traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def ml_predict(request):
    """GET /api/stocks/ml/predict/?symbol=TSLA  — 예측 후 로그인 유저면 DB에 저장"""
    symbol = request.GET.get('symbol', '').strip().upper()
    if not symbol:
        return Response({'error': 'symbol 파라미터가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

    model_path, _ = _paths(symbol)
    if not model_path.exists():
        return Response({'error': f'{symbol} 모델 없음. 먼저 학습하세요.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        import joblib
        model  = joblib.load(model_path)
        ticker = _yf_ticker(symbol)
        end    = datetime.today()
        start  = end - timedelta(days=500)

        base    = _fetch_raw(ticker, start, end)
        base    = _build_features(base)
        feat_df = base[FEAT_COLS].dropna()

        if feat_df.empty:
            return Response({'error': '최신 데이터 피처 계산 실패 (데이터 부족)'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        row     = feat_df.iloc[[-1]]
        pred    = int(model.predict(row)[0])
        proba   = model.predict_proba(row)[0].tolist()
        classes = [int(c) for c in model.classes_]

        label_map  = {0: '관망', 1: '매수', 2: '매도/보류'}
        proba_dict = {c: round(p, 4) for c, p in zip(classes, proba)}
        latest_date = str(base.index[-1].date())

        # ── 로그인 유저면 DB에 저장 ────────────────────────────────
        if request.user and request.user.is_authenticated:
            from .models import UserPredictionCache
            UserPredictionCache.objects.update_or_create(
                user=request.user, symbol=symbol,
                defaults={
                    'signal':       pred,
                    'signal_label': label_map.get(pred, '?'),
                    'prob_hold':    proba_dict.get(0, 0),
                    'prob_buy':     proba_dict.get(1, 0),
                    'prob_sell':    proba_dict.get(2, 0),
                    'latest_date':  latest_date,
                }
            )

        return Response({
            'symbol':        symbol,
            'signal':        pred,
            'signal_label':  label_map.get(pred, '?'),
            'probabilities': proba_dict,
            'latest_date':   latest_date,
            'predicted_at':  datetime.now().strftime('%Y-%m-%d %H:%M'),
        })

    except Exception as e:
        import traceback; traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


FEAT_KR = {
    'feat_ma_ratio':    'MA50/MA200 비율 (1↑=상승추세)',
    'feat_rsi':         'RSI 14일 (30↓매수, 70↑매도)',
    'feat_macd_hist':   'MACD 히스토그램 (양수=상승모멘텀)',
    'feat_bb_pos':      '볼린저 밴드 위치 (0=하단, 1=상단)',
    'feat_return_1d':   '1일 수익률',
    'feat_return_3d':   '3일 수익률',
    'feat_return_5d':   '5일 수익률',
    'feat_vol_ratio':   '거래량 비율 (5일 평균 대비)',
    'feat_usd_idx_chg': '달러지수 일변화율',
    'feat_us_10y_chg':  '미국 10년 금리 일변화율',
}


@api_view(['GET'])
def ml_explain(request):
    """
    GET /api/stocks/ml/explain/?symbol=TSLA
    ML 예측 결과 + Gemini 근거 설명 반환.
    """
    symbol = request.GET.get('symbol', '').strip().upper()
    if not symbol:
        return Response({'error': 'symbol 파라미터가 필요합니다.'}, status=400)

    model_path, meta_path = _paths(symbol)
    if not model_path.exists():
        return Response({'error': f'{symbol} 모델 없음. 먼저 학습하세요.'}, status=400)

    try:
        import joblib
        model  = joblib.load(model_path)
        ticker = _yf_ticker(symbol)
        end    = datetime.today()
        start  = end - timedelta(days=500)

        base    = _fetch_raw(ticker, start, end)
        base    = _build_features(base)
        feat_df = base[FEAT_COLS].dropna()

        if feat_df.empty:
            return Response({'error': '피처 계산 실패'}, status=500)

        row     = feat_df.iloc[[-1]]
        pred    = int(model.predict(row)[0])
        proba   = model.predict_proba(row)[0].tolist()
        classes = [int(c) for c in model.classes_]

        label_map  = {0: '관망', 1: '매수', 2: '매도/보류'}
        proba_dict = {c: round(p * 100, 1) for c, p in zip(classes, proba)}

        # 피처 값 (오늘)
        feat_vals = {f: round(float(row[f].iloc[0]), 6) for f in FEAT_COLS}

        # 모델 피처 중요도 (학습 기준)
        feat_imp = sorted(
            zip(FEAT_COLS, model.feature_importances_),
            key=lambda x: x[1], reverse=True,
        )
    except Exception as e:
        return Response({'error': str(e)}, status=500)

    # ── Gemini 프롬프트 ────────────────────────────────────────────────
    signal_label = label_map.get(pred, '?')
    p_vals = {label_map.get(c, c): p for c, p in proba_dict.items()}

    feat_lines = '\n'.join(
        f'  - {FEAT_KR[f]}: {feat_vals[f]:+.4f}' for f in FEAT_COLS
    )
    imp_lines = '\n'.join(
        f'  {i+1}. {FEAT_KR[f]} (중요도 {int(imp)})'
        for i, (f, imp) in enumerate(feat_imp[:5])
    )

    prompt = f"""당신은 머신러닝 모델의 예측 결과를 쉽게 해설하는 전문가입니다.

아래는 LightGBM 모델이 {symbol} 종목에 대해 오늘 예측한 매매 시그널입니다.

[예측 결과]
- 시그널: {signal_label}
- 확률: 관망 {proba_dict.get(0, 0)}% / 매수 {proba_dict.get(1, 0)}% / 매도 {proba_dict.get(2, 0)}%

[오늘의 지표 피처 값]
{feat_lines}

[모델이 가장 중요하게 보는 피처 TOP 5 (학습 기준)]
{imp_lines}

[모델 학습 기준]
- 익절 조건: 5일 내 +5% 이상 → 매수(1)
- 손절 조건: 5일 내 -2.5% 이하 → 매도/보류(2)
- 그 외 → 관망(0)

다음 형식으로 오늘 '{signal_label}' 을 예측한 이유를 투자자가 이해하기 쉽게 설명해 주세요:

## 예측 근거
오늘의 지표 값과 모델 중요도를 바탕으로, 예측에 가장 크게 기여한 3~4가지 요인을 구체적인 수치와 함께 설명합니다.

## 시그널 신뢰도
예측 확률 분포와 지표 일관성을 바탕으로 이 예측의 신뢰 수준을 평가합니다.

## 반대 시그널 주의
현재 {signal_label} 예측과 반대 방향을 가리키는 지표가 있다면 함께 설명합니다.

마지막 줄에 '본 예측은 과거 데이터 기반 통계 모델이며 미래 수익을 보장하지 않습니다.'라고 명시하세요."""

    try:
        gms_base = 'https://gms.ssafy.io/gmsapi/generativelanguage.googleapis.com/v1beta/models'
        res = req.post(
            f'{gms_base}/{settings.GMS_MODEL}:generateContent',
            headers={'Content-Type': 'application/json', 'x-goog-api-key': settings.GMS_KEY},
            json={'contents': [{'parts': [{'text': prompt}]}]},
            timeout=60,
        )
        res.raise_for_status()
        explanation = res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
    except Exception as e:
        return Response({'error': f'AI 설명 생성 실패: {e}'}, status=502)

    # ── 로그인 유저면 AI 설명도 DB에 저장 ────────────────────────
    if request.user and request.user.is_authenticated:
        from .models import UserPredictionCache
        UserPredictionCache.objects.update_or_create(
            user=request.user, symbol=symbol,
            defaults={
                'signal':       pred,
                'signal_label': signal_label,
                'prob_hold':    proba_dict.get(0, 0),
                'prob_buy':     proba_dict.get(1, 0),
                'prob_sell':    proba_dict.get(2, 0),
                'latest_date':  str(base.index[-1].date()),
                'explanation':  explanation,
            }
        )

    return Response({
        'symbol':        symbol,
        'signal':        pred,
        'signal_label':  signal_label,
        'probabilities': proba_dict,
        'feat_values':   feat_vals,
        'latest_date':   str(base.index[-1].date()),
        'explanation':   explanation,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ml_saved(request):
    """GET /api/stocks/ml/saved/  — 로그인 유저의 저장된 예측 목록"""
    from .models import UserPredictionCache
    items = UserPredictionCache.objects.filter(user=request.user)
    data = []
    for item in items:
        data.append({
            'symbol':        item.symbol,
            'signal':        item.signal,
            'signal_label':  item.signal_label,
            'probabilities': {0: item.prob_hold, 1: item.prob_buy, 2: item.prob_sell},
            'latest_date':   item.latest_date,
            'predicted_at':  item.predicted_at.strftime('%Y-%m-%d %H:%M'),
            'explanation':   item.explanation,
        })
    return Response(data)


@api_view(['GET'])
def ml_status(request):
    """
    GET /api/stocks/ml/status/             → 학습된 모든 모델 목록
    GET /api/stocks/ml/status/?symbol=TSLA → 특정 종목 모델 상태
    """
    symbol = request.GET.get('symbol', '').strip().upper()

    if symbol:
        model_path, meta_path = _paths(symbol)
        if not model_path.exists():
            return Response({'trained': False, 'symbol': symbol})
        try:
            meta = json.loads(meta_path.read_text())
            return Response({'trained': True, **meta})
        except Exception:
            return Response({'trained': True, 'symbol': symbol})

    # 전체 모델 목록
    models = []
    if MODEL_DIR.exists():
        for meta_file in sorted(MODEL_DIR.glob('*_lgbm_meta.json')):
            try:
                meta = json.loads(meta_file.read_text())
                models.append(meta)
            except Exception:
                pass
    return Response({'models': models})
