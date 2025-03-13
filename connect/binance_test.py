import requests


def check_binance_status():
    """
    Binance API의 접근 가능 여부를 ping 엔드포인트를 통해 확인합니다.

    Returns:
        True: API 접근 가능
        False: API 접근 불가능 (에러 발생)
    """
    url = "https://api.binance.com/api/v3/ping"
    try:
        # GET 요청을 보내고 타임아웃은 10초로 설정
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # HTTP 에러가 발생하면 예외 발생
        print("Binance API is accessible.")
        return True
    except requests.exceptions.RequestException as e:
        print("Binance API is not accessible.")
        print("Error:", e)
        return False


if __name__ == '__main__':
    check_binance_status()
