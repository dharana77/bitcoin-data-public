import pandas as pd
import numpy as np


def calculate_max_drawdown(equity_curve):
    """
    equity_curve: 거래마다 누적 자본(예: [1.0, 1.02, 0.98, ...])
    최대 낙폭(MDD)을 계산하여 반환합니다.
    """
    equity_array = np.array(equity_curve)
    running_max = np.maximum.accumulate(equity_array)
    drawdown = (equity_array - running_max) / running_max
    max_drawdown = drawdown.min()  # 가장 큰 손실(음수 값)
    return max_drawdown


def backtest_strategy(df, target_days, start_time_str, end_time_str, initial_capital=1.0):
    """
    df: OHLCV 데이터가 들어있는 DataFrame, 인덱스는 datetime
    target_days: 거래를 실행할 요일 리스트 (예: [0, 2] -> 월요일과 수요일)
    start_time_str: 거래 구간 시작 시간 (예: "10:00")
    end_time_str: 거래 구간 종료 시간 (예: "15:00")
    initial_capital: 초기 자본 (기본 1.0)

    각 해당 일마다, 지정 시간 구간의 첫 봉의 open 가격으로 long 진입, 마지막 봉의 close 가격으로 청산했다고 가정합니다.
    각 거래의 수익률을 계산하고, 누적 자본, 변동성(표준편차), 최대 낙폭(MDD)을 산출합니다.
    """
    # 인덱스가 DatetimeIndex가 아니라면 변환
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)

    # 거래일과 시간 정보를 따로 컬럼으로 추가
    df['date'] = df.index.date
    df['time'] = df.index.time

    trades = []  # 각 거래의 정보를 저장할 리스트
    unique_dates = sorted(df['date'].unique())

    for d in unique_dates:
        daily_data = df[df['date'] == d]
        # 해당 일의 요일 확인 (월:0, 화:1, …, 일:6)
        if daily_data.index[0].weekday() not in target_days:
            continue

        # 지정한 시간 구간 (예: "10:00" ~ "15:00")에 해당하는 데이터 필터링
        daily_window = daily_data.between_time(start_time_str, end_time_str)
        if daily_window.empty:
            continue

        # 거래 진입: 해당 구간의 첫 봉의 open 가격
        entry_price = daily_window.iloc[0]['open']
        # 거래 청산: 해당 구간의 마지막 봉의 close 가격
        exit_price = daily_window.iloc[-1]['close']

        trade_return = (exit_price / entry_price) - 1  # 단일 거래 수익률
        trades.append({
            'date': d,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'return': trade_return
        })

    trades_df = pd.DataFrame(trades)

    # 누적 자본(Equity Curve) 시뮬레이션
    equity = [initial_capital]
    for r in trades_df['return']:
        equity.append(equity[-1] * (1 + r))
    # 첫 항(initial_capital)은 제외하고 거래 종료시점의 자본만 사용
    equity_curve = equity[1:]

    # 전체 성과 지표 계산
    cumulative_return = (equity_curve[-1] / initial_capital - 1) if equity_curve else 0
    volatility = np.std(trades_df['return']) if not trades_df.empty else 0
    max_drawdown = calculate_max_drawdown(equity_curve) if equity_curve else 0

    results = {
        'trades': trades_df,
        'equity_curve': equity_curve,
        'cumulative_return': cumulative_return,
        'volatility': volatility,
        'max_drawdown': max_drawdown
    }
    return results


# ============================================
# 1. CSV 파일로 저장된 데이터를 로드합니다.
#    (여기서는 예시로 "BTC_USDT_15m.csv" 파일을 사용합니다.)
# ============================================
data_filename = "../bronze/BTC_USDT_15m.csv"  # 실제 데이터 파일명에 맞게 수정하세요.
df = pd.read_csv(data_filename, index_col='datetime', parse_dates=True)

# ============================================
# 2. 백테스팅 파라미터 설정
# ============================================
# 예시: 월요일(0)과 수요일(2)에, 매일 10:00부터 15:00까지의 시간 구간에 long 포지션 진입/청산
target_days = [0, 1, 2, 3, 4]  # 월요일과 수요일
start_time_str = "22:00"  # 진입 시간
end_time_str = "00:00"  # 청산 시간

# ============================================
# 3. 백테스팅 실행
# ============================================
results = backtest_strategy(df, target_days, start_time_str, end_time_str, initial_capital=1.0)

# 결과 출력
print("=== 백테스팅 결과 ===")
print("총 거래 횟수:", len(results['trades']))
print("누적 수익률: {:.2%}".format(results['cumulative_return']))
print("거래 수익률 변동성(표준편차): {:.2%}".format(results['volatility']))
print("최대 낙폭(MDD): {:.2%}".format(results['max_drawdown']))

print("\n거래 상세 내역 (상위 5건):")
print(results['trades'].head())
