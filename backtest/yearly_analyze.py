import pandas as pd
import numpy as np


def calculate_max_drawdown(equity_curve):
    """
    equity_curve: 각 거래 후 누적 자본 (예: [1.0, 1.05, 0.95, ...])
    최대 낙폭(MDD)을 계산하여 반환합니다.
    (음수 값으로 반환되며, 예: -0.20는 20%의 낙폭)
    """
    equity_array = np.array(equity_curve)
    running_max = np.maximum.accumulate(equity_array)
    drawdown = (equity_array - running_max) / running_max
    max_drawdown = drawdown.min()
    return max_drawdown


def backtest_strategy_by_year(df, target_days, start_time_str, end_time_str,
                              initial_capital=1.0, leverage=1, stop_loss_pct=0.0):
    """
    df: OHLCV 데이터가 들어있는 DataFrame (인덱스는 datetime)
    target_days: 거래 실행 요일 리스트 (예: [0, 2] -> 월요일과 수요일)
    start_time_str: 거래 구간 시작 시간 (예: "10:00")
    end_time_str: 거래 구간 종료 시간 (예: "15:00")
    initial_capital: 각 연도별 초기 자본 (기본값 1.0)
    leverage: 적용할 레버리지 (1부터 100까지 가능)
    stop_loss_pct: 스탑로스 비율 (예: 0.02이면 2% 하락 시 손절)

    [작업 순서]
    1. 각 거래일마다(특정 요일에 한정), 지정 시간 구간의 데이터를 추출합니다.
    2. 해당 구간의 첫 봉의 open 가격으로 진입한 후,
       intraday 데이터를 순차적으로 확인하여, 만약 어떤 봉의 low가
       (entry_price * (1 - stop_loss_pct)) 이하로 떨어지면 즉시 스탑로스가 발동하여
       exit_price를 스탑로스 가격으로 지정하고 거래를 종료합니다.
    3. 스탑로스가 발동하지 않으면 구간의 마지막 봉의 close 가격으로 거래를 청산합니다.
    4. 단일 거래 수익률에 레버리지를 적용한 후, (효과적 수익률 = leverage * trade_return)
       손실은 -100% 이하로 확산되지 않도록 -1로 제한합니다.
    5. 연도별로 그룹화하여 각 연도 내 거래들을 복리로 누적 계산(누적 자본, 복리 수익률, 변동성, 최대 낙폭)을 수행합니다.
    """
    # 인덱스가 DatetimeIndex가 아니면 변환
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)

    # 날짜와 시간 정보를 별도 컬럼으로 추가 (일자별 그룹화를 위해)
    df['date'] = df.index.date
    df['time'] = df.index.time

    trades = []  # 각 거래의 정보를 저장할 리스트
    unique_dates = sorted(df['date'].unique())

    for d in unique_dates:
        daily_data = df[df['date'] == d]
        # 해당 일의 요일이 target_days에 포함되어 있는지 확인 (월요일=0, 화요일=1, …)
        if daily_data.index[0].weekday() not in target_days:
            continue

        # 지정한 시간 구간 (예: "10:00" ~ "15:00")에 해당하는 데이터 필터링
        daily_window = daily_data.between_time(start_time_str, end_time_str)
        if daily_window.empty:
            continue

        # 거래 진입: 해당 구간의 첫 봉의 open 가격
        entry_price = daily_window.iloc[0]['open']
        # 스탑로스 가격 (스탑로스 pct가 지정된 경우)
        stop_price = entry_price * (1 - stop_loss_pct) if stop_loss_pct > 0 else None

        triggered_stop_loss = False
        exit_price = None

        # intraday 데이터를 순차적으로 확인: 스탑로스 조건이 발생하면 즉시 거래 종료
        for idx, row in daily_window.iterrows():
            if stop_loss_pct > 0 and row['low'] <= stop_price:
                triggered_stop_loss = True
                exit_price = stop_price  # 스탑로스 가격으로 거래 종료
                break

        # 스탑로스가 발동하지 않은 경우, 지정 구간의 마지막 봉의 close 가격으로 청산
        if not triggered_stop_loss:
            exit_price = daily_window.iloc[-1]['close']

        # 단일 거래 수익률 계산
        base_return = (exit_price / entry_price) - 1
        # 레버리지 적용
        effective_return = base_return * leverage
        # 손실은 최대 -100%로 제한
        effective_return = max(effective_return, -1)

        year = daily_data.index[0].year  # 거래일의 연도

        trades.append({
            'date': d,
            'year': year,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'base_return': base_return,
            'leverage': leverage,
            'effective_return': effective_return,
            'stop_loss_triggered': triggered_stop_loss
        })

    trades_df = pd.DataFrame(trades)

    # 연도별로 거래 내역을 그룹화하여 백테스팅 결과 계산
    results_by_year = {}
    for year, group in trades_df.groupby('year'):
        # 복리 누적 수익률: 모든 거래의 (1 + effective_return)을 곱한 후 1을 빼줌
        compound_return = np.prod(1 + group['effective_return'].values) - 1

        # 누적 자본 (Equity Curve): 초기 자본에 각 거래의 (1 + effective_return)을 누적 곱함
        equity_curve = initial_capital * np.cumprod(1 + group['effective_return'].values)

        # 거래 수익률의 표준편차 (변동성)
        volatility = np.std(group['effective_return'].values)
        # 최대 낙폭(MDD) 계산
        mdd = calculate_max_drawdown(equity_curve)

        results_by_year[year] = {
            'trades': group,
            'equity_curve': equity_curve,
            'cumulative_return': compound_return,
            'volatility': volatility,
            'max_drawdown': mdd
        }

    return results_by_year, trades_df


# =======================================================
# 1. CSV 파일로 저장된 데이터를 로드합니다.
# =======================================================
data_filename = "../bronze/BTC_USDT_15m.csv"  # 실제 파일명에 맞게 수정하세요.
df = pd.read_csv(data_filename, index_col='datetime', parse_dates=True)

# =======================================================
# 2. 백테스팅 파라미터 설정
# =======================================================
# 예시: 월요일(0)과 수요일(2)에, 매일 10:00부터 15:00까지의 구간에서 long 포지션 진입/청산
target_days = [0]  # 월요일과 수요일
start_time_str = "10:00"  # 진입 시간
end_time_str = "12:30"  # 청산 시간

# 사용할 레버리지 (1부터 100까지 지정 가능)
leverage = 10  # 예시: 10배 레버리지 사용

# 스탑로스 비율 지정 (예: 0.02이면 2% 하락 시 손절)
stop_loss_pct = 0.02

# =======================================================
# 3. 연도별 백테스팅 실행 (복리, 레버리지 및 스탑로스 적용)
# =======================================================
results_by_year, trades_df = backtest_strategy_by_year(df, target_days, start_time_str, end_time_str,
                                                       initial_capital=1.0, leverage=leverage,
                                                       stop_loss_pct=stop_loss_pct)

# =======================================================
# 4. 연도별 백테스팅 결과 출력
# =======================================================
for year, res in sorted(results_by_year.items()):
    print(f"=== {year}년 백테스팅 결과 ===")
    print("총 거래 횟수:", len(res['trades']))
    print("연도별 복리 누적 수익률: {:.2%}".format(res['cumulative_return']))
    print("거래 수익률 변동성 (표준편차): {:.2%}".format(res['volatility']))
    print("최대 낙폭 (MDD): {:.2%}".format(res['max_drawdown']))
    print("거래 상세 내역 (상위 3건):")
    print(res['trades'].head(3))
    print("\n")