import json
import re
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import yfinance as yf
from rest_framework import status
from rest_framework.decorators import api_view
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
    """GET /api/stocks/ml/predict/?symbol=TSLA"""
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

        return Response({
            'symbol':        symbol,
            'signal':        pred,
            'signal_label':  label_map.get(pred, '?'),
            'probabilities': proba_dict,
            'latest_date':   str(base.index[-1].date()),
            'predicted_at':  datetime.now().strftime('%Y-%m-%d %H:%M'),
        })

    except Exception as e:
        import traceback; traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
