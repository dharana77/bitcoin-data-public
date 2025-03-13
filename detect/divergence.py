import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import ta  # Technical Analysis Library

# 1. 데이터 로드
# CSV 파일은 인덱스가 datetime 형식이어야 하며, 최소한 'close' 컬럼이 필요합니다.
data_filename = "BTC_USDT_15m.csv"  # 파일명에 맞게 수정하세요.
df = pd.read_csv(data_filename, index_col='datetime', parse_dates=True)

# 2. RSI 계산 (기간 14 사용)
df['RSI'] = ta.momentum.rsi(df['close'], window=14)
df.dropna(inplace=True)

# 3. 로컬 극값(피벗) 찾기
# find_peaks를 이용하여 로컬 고점과 저점을 각각 탐지합니다.
# (distance 파라미터는 인접한 피크 간 최소 간격으로, 데이터의 특성에 따라 조정 필요)

# 가격의 로컬 저점 찾기: 가격의 음수에 대해 피크를 찾으면 로컬 저점을 검출할 수 있음
price_lows, _ = find_peaks(-df['close'], distance=10)
# RSI의 로컬 저점 찾기
rsi_lows, _ = find_peaks(-df['RSI'], distance=10)

# 가격의 로컬 고점 찾기
price_highs, _ = find_peaks(df['close'], distance=10)
# RSI의 로컬 고점 찾기
rsi_highs, _ = find_peaks(df['RSI'], distance=10)


# 4. 다이버전스 탐지 함수
def detect_bullish_divergence(df, price_lows, rsi_lows):
    """
    강세 다이버전스: 가격은 더 낮은 저점을 형성하는데 RSI는 더 높은 저점을 형성하는 경우
    반환: (이전 피크 시점, 현재 피크 시점) 튜플의 리스트
    """
    bullish_divs = []
    # 단순화를 위해, price_lows에 해당하는 RSI 값도 같은 인덱스에서 비교합니다.
    for i in range(1, len(price_lows)):
        idx_prev = price_lows[i - 1]
        idx_curr = price_lows[i]
        price_prev, price_curr = df['close'].iloc[idx_prev], df['close'].iloc[idx_curr]
        rsi_prev, rsi_curr = df['RSI'].iloc[idx_prev], df['RSI'].iloc[idx_curr]

        # 가격은 하락(낮은 저점)인데 RSI는 상승(높은 저점)인 경우
        if price_curr < price_prev and rsi_curr > rsi_prev:
            bullish_divs.append((df.index[idx_prev], df.index[idx_curr]))
    return bullish_divs


def detect_bearish_divergence(df, price_highs, rsi_highs):
    """
    약세 다이버전스: 가격은 더 높은 고점을 형성하는데 RSI는 더 낮은 고점을 형성하는 경우
    반환: (이전 피크 시점, 현재 피크 시점) 튜플의 리스트
    """
    bearish_divs = []
    for i in range(1, len(price_highs)):
        idx_prev = price_highs[i - 1]
        idx_curr = price_highs[i]
        price_prev, price_curr = df['close'].iloc[idx_prev], df['close'].iloc[idx_curr]
        rsi_prev, rsi_curr = df['RSI'].iloc[idx_prev], df['RSI'].iloc[idx_curr]

        # 가격은 상승(더 높은 고점)인데 RSI는 하락(더 낮은 고점)인 경우
        if price_curr > price_prev and rsi_curr < rsi_prev:
            bearish_divs.append((df.index[idx_prev], df.index[idx_curr]))
    return bearish_divs


bullish_divergences = detect_bullish_divergence(df, price_lows, rsi_lows)
bearish_divergences = detect_bearish_divergence(df, price_highs, rsi_highs)

# 5. 결과 출력
print("강세 다이버전스 (Bullish Divergences):")
for div in bullish_divergences:
    print(f"From {div[0]} to {div[1]}")

print("\n약세 다이버전스 (Bearish Divergences):")
for div in bearish_divergences:
    print(f"From {div[0]} to {div[1]}")

# 6. 시각화 (옵션)
plt.figure(figsize=(14, 6))
plt.plot(df.index, df['close'], label='Price', color='black')
plt.scatter(df.index[price_lows], df['close'].iloc[price_lows], marker='v', color='green', s=50, label='Price Lows')
plt.scatter(df.index[price_highs], df['close'].iloc[price_highs], marker='^', color='red', s=50, label='Price Highs')
for d in bullish_divergences:
    plt.axvspan(d[0], d[1], color='green', alpha=0.2)
for d in bearish_divergences:
    plt.axvspan(d[0], d[1], color='red', alpha=0.2)
plt.title("Price & Detected Divergences")
plt.legend()
plt.show()

plt.figure(figsize=(14, 6))
plt.plot(df.index, df['RSI'], label='RSI', color='orange')
plt.scatter(df.index[rsi_lows], df['RSI'].iloc[rsi_lows], marker='v', color='green', s=50, label='RSI Lows')
plt.scatter(df.index[rsi_highs], df['RSI'].iloc[rsi_highs], marker='^', color='red', s=50, label='RSI Highs')
plt.axhline(30, color='blue', linestyle='--', label='Oversold')
plt.axhline(70, color='blue', linestyle='--', label='Overbought')
plt.title("RSI & Detected Divergences")
plt.legend()
plt.show()