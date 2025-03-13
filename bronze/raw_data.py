import ccxt
import pandas as pd
from datetime import datetime
import time

# 1. Binance 거래소 객체 생성 (rateLimit을 준수하도록 설정)
exchange = ccxt.binance({
    'rateLimit': 1200,  # 밀리초 단위
    'enableRateLimit': True,  # 자동 딜레이 적용
})

# 2. 설정값
symbol = 'BTC/USDT'  # Binance에서는 BTC/USDT 거래쌍 사용 (BTC-USD와 유사)
# timeframes = ['15m', '30m', '1h', '4h']  # 가져올 데이터의 시간 간격
timeframes = ['15m', '30m', '1h', '4h', '1d']

# 데이터 기간 (ISO8601 형식 사용)
# 2025년은 미래일 수 있으므로, 실제 거래소 데이터는 현재 시점까지 제공됩니다.
start_date_str = "2024-12-20T00:00:00Z"
end_date_str = "2025-02-10T00:00:00Z"

# 타임스탬프(밀리초)로 변환
since = exchange.parse8601(start_date_str)
end_ts = exchange.parse8601(end_date_str)

limit = 1000  # 한 번 요청 시 최대 캔들 수 (Binance 제한)

# 3. 각 시간 간격별로 데이터 수집, CSV 저장, 로드 예시
for timeframe in timeframes:
    all_ohlcv = []  # 누적 데이터 저장 리스트
    current_since = since
    print(f"\n=== {timeframe} 데이터 수집 시작 ===")

    # 반복해서 데이터를 가져오기 (각 요청은 최대 1000개의 캔들)
    while current_since < end_ts:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=current_since, limit=limit)
            print(ohlcv)
        except Exception as e:
            print(f"데이터 수집 중 오류 발생: {e}")
            break

        # 더 이상 데이터가 없으면 중단
        if not ohlcv:
            print("더 이상 반환되는 데이터가 없습니다.")
            break

        all_ohlcv += ohlcv  # 결과 누적

        # 마지막 캔들의 타임스탬프를 기준으로 다음 조회 시점을 설정 (중복 방지 위해 +1ms)
        last_timestamp = ohlcv[-1][0]
        if last_timestamp == current_since:
            # 진행이 없으면 무한 루프 방지를 위해 탈출
            break
        current_since = last_timestamp + 1

        # API 호출 간 딜레이 (rateLimit 준수)
        time.sleep(exchange.rateLimit / 1000)

    # 4. 누적 데이터(리스트)를 DataFrame으로 변환
    # 캔들 형식: [timestamp, open, high, low, close, volume]
    df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    # timestamp를 datetime 형식으로 변환 (UTC 기준)
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('datetime', inplace=True)
    df.drop('timestamp', axis=1, inplace=True)

    # 5. CSV 파일로 저장
    filename = f"BTC_USDT_{timeframe}.csv"
    df.to_csv(filename)
    print(f"{timeframe} 데이터가 CSV 파일로 저장되었습니다: {filename}")

    # 6. 저장된 CSV 파일 로드 (검증용)
    loaded_df = pd.read_csv(filename, index_col='datetime', parse_dates=True)
    print(f"로드한 {timeframe} 데이터의 앞부분:")
    print(loaded_df.head())
