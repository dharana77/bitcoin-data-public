# combine_features.py

import pandas as pd


def load_and_resample(csv_file, prefix, resample_rule='15min'):
    """
    csv_file: 해당 시간 프레임의 기술지표가 포함된 CSV 파일 경로
    prefix: 해당 파일의 피처명 앞에 붙은 접두어 (예: "15m", "1h", "4h", "d")
    resample_rule: 리샘플링 규칙 (기본: '15T' = 15분)

    - CSV 파일을 불러와 datetime 인덱스를 파싱하고 정렬한 후,
    - 전체 피처(열)에 prefix가 이미 붙어 있다고 가정하고,
      resample_rule에 따라 forward fill 방식으로 리샘플링합니다.
    - 리샘플링 후 DataFrame을 반환합니다.
    """
    df = pd.read_csv(csv_file, index_col='datetime', parse_dates=True)
    df.sort_index(inplace=True)
    # 리샘플링 후 forward fill (시간 간격에 맞춰 값 채움)
    df_resampled = df.resample(resample_rule).ffill()
    return df_resampled


if __name__ == "__main__":
    # CSV 파일 경로 (실제 파일명으로 수정)
    csv_15m = "../silver/processed_15m.csv"  # 15분 봉 데이터 (기술지표 포함)
    csv_1h = "../silver/processed_1h.csv"  # 1시간 봉 데이터
    csv_4h = "../silver/processed_4h.csv"  # 4시간 봉 데이터
    csv_d = "../silver/processed_d.csv"  # 일봉 데이터

    # 각 시간별 데이터 불러오기 (15분 데이터는 그대로 사용)
    df_15m = pd.read_csv(csv_15m, index_col='datetime', parse_dates=True)
    df_15m.sort_index(inplace=True)
    df_15m = df_15m.add_prefix('15m_')  # Add prefix to 15min data columns

    # 1시간, 4시간, 일봉 데이터는 15분 간격으로 리샘플링하여 결합합니다.
    df_1h_resampled = load_and_resample(csv_1h, prefix="1h", resample_rule='15min')
    df_4h_resampled = load_and_resample(csv_4h, prefix="4h", resample_rule='15min')
    df_d_resampled = load_and_resample(csv_d, prefix="d", resample_rule='15min')

    # 만약 각 CSV 파일 내의 피처들이 이미 접두어가 붙어 있다면 그대로 사용하고,
    # 그렇지 않으면 아래와 같이 add_prefix를 적용할 수 있습니다.
    # 예:
    # df_1h_resampled = load_and_resample(csv_1h, prefix="1h", resample_rule='15T').add_prefix("1h_")
    # (여기서는 processed CSV 파일에 이미 prefix가 붙어 있다고 가정)

    # 15분 데이터를 기본으로 다른 리샘플된 데이터와 인덱스 기준으로 병합합니다.
    df_combined = df_15m.join(df_1h_resampled, how='left', lsuffix='_x', rsuffix='_y')
    df_combined = df_combined.join(df_4h_resampled, how='left', lsuffix='', rsuffix='_4h')
    df_combined = df_combined.join(df_d_resampled, how='left', lsuffix='', rsuffix='_d')

    # 결측치가 남아 있을 경우 제거 (실제 데이터 상황에 따라 처리)
    df_combined.dropna(inplace=True)

    # 결합된 데이터를 CSV 파일로 저장 (필요한 경우)
    output_file = "combined_data.csv"
    df_combined.to_csv(output_file)
    print(f"결합된 데이터가 '{output_file}'에 저장되었습니다.")
