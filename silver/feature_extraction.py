# feature_extraction.py

import pandas as pd
import ta  # pip install ta


def read_and_preprocess(csv_file, prefix):
    """
    csv_file: 각 시간 프레임의 원본 OHLCV 데이터 CSV 파일 경로.
    prefix: 각 지표 컬럼명 앞에 붙일 접두어 (예: "15m", "1h", "4h", "d").

    - CSV 파일을 읽어 인덱스를 datetime으로 파싱하고 정렬.
    - RSI, SMA, BollingerBands %B, MACD 히스토그램, Elder Ray, Force Index, ROC, Price-SMA Diff 등의 기술지표를 계산.
    - 계산된 지표 컬럼에는 prefix가 붙습니다.

    반환:
        전처리된 DataFrame
    """
    # CSV 파일 읽기 (인덱스를 datetime으로 파싱)
    df = pd.read_csv(csv_file, index_col='datetime', parse_dates=True)
    df.sort_index(inplace=True)

    # RSI (14)
    df[f'{prefix}_rsi'] = ta.momentum.RSIIndicator(close=df['close'], window=14).rsi()

    # 단순 이동평균 (SMA, 20)
    df[f'{prefix}_sma_20'] = ta.trend.SMAIndicator(close=df['close'], window=20).sma_indicator()

    # 볼린저 밴드 %B (20기간, 표준편차 2)
    bb = ta.volatility.BollingerBands(close=df['close'], window=20, window_dev=2)
    df[f'{prefix}_bb_percent'] = bb.bollinger_pband()

    # MACD 히스토그램 (diff)
    macd = ta.trend.MACD(close=df['close'])
    df[f'{prefix}_macd_diff'] = macd.macd_diff()

    # Elder Ray: 13기간 EMA 및 Bull/Bear Power
    df[f'{prefix}_ema_13'] = ta.trend.EMAIndicator(close=df['close'], window=13).ema_indicator()
    df[f'{prefix}_elder_bull'] = df['high'] - df[f'{prefix}_ema_13']
    df[f'{prefix}_elder_bear'] = df['low'] - df[f'{prefix}_ema_13']

    # Force Index (13)
    df[f'{prefix}_force_index'] = ta.volume.ForceIndexIndicator(close=df['close'], volume=df['volume'],
                                                                window=13).force_index()

    # ROC (12)
    df[f'{prefix}_roc'] = ta.momentum.ROCIndicator(close=df['close'], window=12).roc()

    # 종가와 SMA 차이
    df[f'{prefix}_price_sma_diff'] = df['close'] - df[f'{prefix}_sma_20']

    # 결측치 제거
    df.dropna(inplace=True)
    return df


if __name__ == "__main__":
    # 각 시간 프레임별 원본 CSV 파일 경로를 딕셔너리로 정의합니다.
    csv_files = {
        "15m": "../bronze/BTC_USDT_15m.csv",
        "1h": "../bronze/BTC_USDT_1h.csv",
        "4h": "../bronze/BTC_USDT_4h.csv",
        "d": "../bronze/BTC_USDT_1d.csv"  # 일봉 데이터
    }

    # 각 파일에 대해 전처리 후 결과를 별도의 CSV 파일로 저장합니다.
    for prefix, csv_path in csv_files.items():
        print(f"Processing {csv_path} with prefix '{prefix}' ...")
        df_processed = read_and_preprocess(csv_path, prefix)
        output_file = f"processed_{prefix}.csv"
        df_processed.to_csv(output_file)
        print(f"Saved processed data to {output_file}\n")