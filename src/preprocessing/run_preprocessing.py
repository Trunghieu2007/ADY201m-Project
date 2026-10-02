# Điều phối thực thi và kiểm định toàn bộ pipeline tiền xử lý dữ liệu
from .preprocess import run
from .validate_processed import validate

if __name__ == "__main__":
    run()
    result = validate()
    print(result)
    raise SystemExit(0 if result["result"] == "PASS" else 1)
