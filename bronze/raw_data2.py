import ccxt
import pandas as pd
from datetime import datetime
import time
import os
from datetime import datetime, timedelta

# 1. Binance 거래소 객체 생성 (rateLimit 준수)
exchange = ccxt.binance({
    'rateLimit': 1200,  # 밀리초 단위
    'enableRateLimit': True,  # 자동 딜레이 적용
})

# 2. 설정값
symbol = 'BTC/USDT'
timeframes = ['15m', '30m', '1h', '4h', '1d']

now = datetime.utcnow()

# 종료 시각: 현재 시각 (UTC)
end_date_str = now.strftime('%Y-%m-%dT%H:%M:%SZ')


# 시작 시각: 현재 시각에서 15분 전
start_date_str = (now - timedelta(minutes=15)).strftime('%Y-%m-%dT%H:%M:%SZ')


since_default = exchange.parse8601(start_date_str)
end_ts = exchange.parse8601(end_date_str)

limit = 1000  # 한 번 요청 시 최대 캔들 수 (Binance 제한)

for timeframe in timeframes:
    filename = f"BTC_USDT_{timeframe}.csv"

    # 파일이 이미 존재하면 마지막 기록된 시각 이후의 데이터만 가져오기 위한 시작 시점을 설정
    if os.path.exists(filename):
        try:
            existing_df = pd.read_csv(filename, index_col='datetime', parse_dates=True)
        except Exception as e:
            print(f"{filename} 파일을 읽는 중 오류 발생: {e}")
            existing_df = None

        if existing_df is not None and not existing_df.empty:
            # CSV의 인덱스는 datetime 형식이므로, 마지막 시각을 타임스탬프로 변환
            last_datetime = existing_df.index[-1]
            last_ts = int(last_datetime.timestamp() * 1000)
            # 마지막 기록 이후 1ms부터 시작 (중복 방지)
            current_since = last_ts + 1
            print(f"{filename} 파일이 존재합니다. 마지막 기록 시각: {last_datetime}")
        else:
            current_since = since_default
            print(f"{filename} 파일이 비어 있으므로, {pd.to_datetime(current_since, unit='ms')}부터 데이터 수집을 시작합니다.")
    else:
        current_since = since_default
        print(f"{filename} 파일이 존재하지 않습니다. {pd.to_datetime(current_since, unit='ms')}부터 데이터 수집을 시작합니다.")

    # 실제 데이터 수집 종료 시점은 현재 시간과 지정한 종료 시점 중 더 이른 쪽을 사용
    now_ts = exchange.milliseconds()
    new_end_ts = min(now_ts, end_ts)

    print(f"\n=== {timeframe} 데이터 수집 시작 (시작 시각: {pd.to_datetime(current_since, unit='ms')}) ===")
    new_data = []  # 새로 수집된 데이터 저장 리스트

    # current_since가 new_end_ts보다 작을 동안 반복 호출
    while current_since < new_end_ts:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=current_since, limit=limit)
            # 디버그용: 가져온 데이터 출력
            print(ohlcv)
        except Exception as e:
            print(f"데이터 수집 중 오류 발생: {e}")
            break

        if not ohlcv:
            print("더 이상 반환되는 데이터가 없습니다.")
            break

        new_data += ohlcv  # 데이터 누적

        last_timestamp = ohlcv[-1][0]
        # 만약 진행이 없는 경우 무한 루프 방지
        if last_timestamp == current_since:
            break

        # 다음 조회 시점을 마지막 캔들 이후 1ms로 설정
        current_since = last_timestamp + 1

        # API 호출 간 딜레이 (rateLimit 준수)
        time.sleep(exchange.rateLimit / 1000)

    # 새로 수집된 데이터가 없으면 건너뜀
    if not new_data:
        print(f"{timeframe}에 추가할 새로운 데이터가 없습니다. 스킵합니다.")
        continue

    # 4. 누적 데이터(리스트)를 DataFrame으로 변환
    # 캔들 데이터 형식: [timestamp, open, high, low, close, volume]
    new_df = pd.DataFrame(new_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    # timestamp를 datetime으로 변환 (UTC 기준)
    new_df['datetime'] = pd.to_datetime(new_df['timestamp'], unit='ms')
    new_df.set_index('datetime', inplace=True)
    new_df.drop('timestamp', axis=1, inplace=True)

    # 5. CSV 파일에 데이터 추가: 파일이 존재하면 append, 없으면 새 파일 생성
    if os.path.exists(filename):
        new_df.to_csv(filename, mode='a', header=False)
        print(f"{timeframe} CSV 파일에 새로운 데이터가 추가되었습니다: {filename}")
    else:
        new_df.to_csv(filename)
        print(f"{timeframe} CSV 파일이 생성되었습니다: {filename}")

    # 6. 저장된 CSV 파일 로드 (검증용)
    try:
        loaded_df = pd.read_csv(filename, index_col='datetime', parse_dates=True)
        print(f"로드한 {timeframe} 데이터의 앞부분:")
        print(loaded_df.head())
    except Exception as e:
        print(f"{filename} 파일을 로드하는 중 오류 발생: {e}")
