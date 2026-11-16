# ============================================================
# PetStoreInventoryManagementFunction 최종 호출 테스트
# ============================================================
#
# 목적
# ------------------------------------------------------------
# PetStore AI Agent에서 사용할 Inventory Lambda가
# 최종 배포 환경에서도 정상적으로 동작하는지 확인합니다.
#
# 최종 데이터 흐름
#
# ProductInformation Knowledge Base
#          ↓
# product_code 확인
#          ↓
# inventory_lookup(product_code)
#          ↓
# PetStoreInventoryManagementFunction
#          ↓
# 현재 재고정보 반환
#
# Lambda에 전달되는 최종 JSON 형식
#
# {
#     "product_code": "BP010"
# }
#
# ============================================================


# ============================================================
# 01. 필요한 라이브러리
# ============================================================

import os
import json
import sys

import boto3

from pathlib import Path
from dotenv import load_dotenv
from botocore.exceptions import ClientError


# ============================================================
# 02. 현재 Python 파일 위치 확인
# ============================================================
#
# 현재 파일:
#
# C:\PetStoreProject\app\PetStoreAgent\
#     test_inventory_lambda.py
#
# .env 파일도 같은 디렉터리에 있다고 가정합니다.
#
# C:\PetStoreProject\app\PetStoreAgent\.env
#
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

ENV_FILE = BASE_DIR / ".env"


# ============================================================
# 03. .env 파일 존재 여부 확인
# ============================================================

if not ENV_FILE.exists():

    raise FileNotFoundError(
        f".env 파일을 찾을 수 없습니다.\n"
        f"확인할 경로: {ENV_FILE}"
    )


# ============================================================
# 04. .env 파일 로드
# ============================================================

load_dotenv(
    dotenv_path=ENV_FILE
)


# ============================================================
# 05. 환경변수 읽기
# ============================================================

REGION = os.getenv(
    "PETSTORE_REGION",
    "ap-northeast-2"
)

INVENTORY_LAMBDA_NAME = os.getenv(
    "INVENTORY_LAMBDA_NAME"
)


# ============================================================
# 06. 필수 환경변수 확인
# ============================================================

if not INVENTORY_LAMBDA_NAME:

    raise ValueError(
        ".env 파일에 "
        "INVENTORY_LAMBDA_NAME이 없습니다."
    )


# ============================================================
# 07. 테스트할 상품 코드
# ============================================================
#
# ProductInformation Knowledge Base에서
# Bark Park Buddy의 상품코드가 BP010이라고 가정합니다.
#
# ============================================================

PRODUCT_CODE = "BP010"


# ============================================================
# 08. AWS Lambda Client 생성
# ============================================================

lambda_client = boto3.client(
    "lambda",
    region_name=REGION
)


# ============================================================
# 09. Lambda에 전달할 Payload
# ============================================================
#
# 매우 중요
#
# 이전 구조:
#
# {
#     "function": "getInventory",
#     "parameters": [...]
# }
#
# 를 사용하지 않습니다.
#
# 최종 Agent와 Lambda 사이에서는 다음 형식으로 통일합니다.
#
# {
#     "product_code": "BP010"
# }
#
# ============================================================

payload = {
    "product_code": PRODUCT_CODE
}


# ============================================================
# 10. 테스트 시작 정보 출력
# ============================================================

print()
print("=" * 60)
print("Inventory Lambda 호출 시작")
print("=" * 60)

print(
    "Region       :",
    REGION
)

print(
    "Lambda       :",
    INVENTORY_LAMBDA_NAME
)

print(
    "Product Code :",
    PRODUCT_CODE
)

print(
    ".env File    :",
    ENV_FILE
)


# ============================================================
# 11. Lambda에 실제 전달되는 JSON 확인
# ============================================================

print()
print("=" * 60)
print("Lambda 실제 전송 Payload")
print("=" * 60)

print(
    json.dumps(
        payload,
        indent=2,
        ensure_ascii=False
    )
)


# ============================================================
# 12. Lambda 호출
# ============================================================

try:

    response = lambda_client.invoke(

        # .env에서 읽은 Lambda 이름
        FunctionName=INVENTORY_LAMBDA_NAME,

        # Lambda 실행 완료까지 기다린 후 결과 수신
        InvocationType="RequestResponse",

        # Python Dictionary → JSON → UTF-8 Bytes
        Payload=json.dumps(
            payload,
            ensure_ascii=False
        ).encode("utf-8")
    )


# ============================================================
# 13. AWS Client 오류
# ============================================================

except ClientError as error:

    print()
    print("=" * 60)
    print("AWS Lambda 호출 실패")
    print("=" * 60)

    print(error)

    sys.exit(1)


# ============================================================
# 14. 기타 오류
# ============================================================

except Exception as error:

    print()
    print("=" * 60)
    print("예상하지 못한 오류 발생")
    print("=" * 60)

    print(error)

    sys.exit(1)


# ============================================================
# 15. Lambda HTTP 상태 확인
# ============================================================

status_code = (
    response
    .get("ResponseMetadata", {})
    .get("HTTPStatusCode")
)

print()
print("=" * 60)
print("AWS Lambda 호출 상태")
print("=" * 60)

print(
    "HTTP Status :",
    status_code
)


# ============================================================
# 16. Lambda 응답 Payload 읽기
# ============================================================

response_payload = (
    response["Payload"]
    .read()
    .decode("utf-8")
)


print()
print("=" * 60)
print("Lambda 원본 응답")
print("=" * 60)

print(response_payload)


# ============================================================
# 17. Lambda 자체 실행 오류 확인
# ============================================================
#
# Python 예외 등이 Lambda 내부에서 발생하면
# FunctionError가 포함될 수 있습니다.
#
# ============================================================

if "FunctionError" in response:

    print()
    print("=" * 60)
    print("Lambda 함수 내부 실행 오류")
    print("=" * 60)

    print(response_payload)

    sys.exit(1)


# ============================================================
# 18. JSON 응답 파싱
# ============================================================

try:

    result = json.loads(
        response_payload
    )

except json.JSONDecodeError as error:

    print()
    print("=" * 60)
    print("Lambda 응답 JSON 변환 실패")
    print("=" * 60)

    print(error)

    print()
    print(
        "Lambda 원본 응답:",
        response_payload
    )

    sys.exit(1)


# ============================================================
# 19. Lambda 비즈니스 처리 결과 확인
# ============================================================

if not result.get("success"):

    print()
    print("=" * 60)
    print("재고 조회 실패")
    print("=" * 60)

    print(
        "message :",
        result.get(
            "message",
            "알 수 없는 오류"
        )
    )

    # Lambda에 received_event 진단 기능이 있다면
    # 실제 받은 Event도 확인합니다.

    if result.get("received_event"):

        print()
        print("Lambda가 실제 받은 Event:")

        print(
            json.dumps(
                result.get("received_event"),
                indent=2,
                ensure_ascii=False
            )
        )

    sys.exit(1)


# ============================================================
# 20. 정상적인 재고정보 추출
# ============================================================

product_code = result.get(
    "product_code"
)

name = result.get(
    "name"
)

quantity = result.get(
    "quantity"
)

reorder_level = result.get(
    "reorder_level"
)

status = result.get(
    "status"
)

last_updated = result.get(
    "last_updated"
)


# ============================================================
# 21. 재고 조회 결과 출력
# ============================================================

print()
print("=" * 60)
print("상품 재고 조회 결과")
print("=" * 60)

print(
    "success       :",
    result.get("success")
)

print(
    "product_code  :",
    product_code
)

print(
    "name          :",
    name
)

print(
    "quantity      :",
    quantity
)

print(
    "reorder_level :",
    reorder_level
)

print(
    "status        :",
    status
)

print(
    "last_updated  :",
    last_updated
)


# ============================================================
# 22. 필수 응답 필드 확인
# ============================================================
#
# 재고 수량은 실제 운영에서 변경될 수 있기 때문에
#
# quantity == 30
#
# 처럼 특정 수량을 성공 조건으로 사용하지 않습니다.
#
# 대신 API 계약에 필요한 필드가 제대로 반환되는지
# 확인합니다.
#
# ============================================================

required_fields = [
    "product_code",
    "name",
    "quantity",
    "reorder_level",
    "status",
    "last_updated"
]


missing_fields = []

for field in required_fields:

    if result.get(field) is None:

        missing_fields.append(
            field
        )


# ============================================================
# 23. 누락 필드가 있는 경우
# ============================================================

if missing_fields:

    print()
    print("=" * 60)
    print("테스트 결과 확인 필요")
    print("=" * 60)

    print(
        "다음 필드가 Lambda 응답에 없습니다:"
    )

    for field in missing_fields:

        print(
            "-",
            field
        )

    sys.exit(1)


# ============================================================
# 24. 상품코드 확인
# ============================================================

if product_code != PRODUCT_CODE:

    print()
    print("=" * 60)
    print("테스트 결과 확인 필요")
    print("=" * 60)

    print(
        "요청한 상품코드:",
        PRODUCT_CODE
    )

    print(
        "응답 상품코드:",
        product_code
    )

    sys.exit(1)


# ============================================================
# 25. 최종 성공
# ============================================================

print()
print("=" * 60)
print("Inventory Lambda 테스트 성공")
print("=" * 60)

print(
    f"{product_code} 상품의 재고 정보를 "
    f"정상적으로 조회했습니다."
)

print()

print(
    f"상품명       : {name}"
)

print(
    f"현재 재고    : {quantity}개"
)

print(
    f"재주문 기준  : {reorder_level}개"
)

print(
    f"재고 상태    : {status}"
)

print(
    f"최종 업데이트: {last_updated}"
)

print("=" * 60)