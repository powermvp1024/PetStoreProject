# ============================================================
# PetStoreUserManagementFunction 최종 호출 테스트
# ============================================================
#
# 목적
# ------------------------------------------------------------
# PetStore AI Agent에서 사용하는 User Lambda가
# 정상적으로 회원정보를 반환하는지 확인합니다.
#
# 최종 데이터 흐름
#
# PetStoreAgent
#      ↓
# user_lookup("USER-001")
#      ↓
# {
#     "user_id": "USER-001"
# }
#      ↓
# PetStoreUserManagementFunction
#      ↓
# 회원정보 반환
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
# 02. 현재 파일 및 .env 경로
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

ENV_FILE = BASE_DIR / ".env"


# ============================================================
# 03. .env 파일 존재 여부 확인
# ============================================================

if not ENV_FILE.exists():

    raise FileNotFoundError(
        f".env 파일을 찾을 수 없습니다.\n"
        f"확인 경로: {ENV_FILE}"
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

USER_LAMBDA_NAME = os.getenv(
    "USER_LAMBDA_NAME"
)


# ============================================================
# 06. 필수 환경변수 확인
# ============================================================

if not USER_LAMBDA_NAME:

    raise ValueError(
        ".env 파일에 "
        "USER_LAMBDA_NAME이 없습니다."
    )


# ============================================================
# 07. 조회할 회원 ID
# ============================================================
#
# 중요
#
# 기존:
#
# usr_001
#
# 수정:
#
# USER-001
#
# Lambda 내부 회원 ID와 동일하게 사용합니다.
#
# ============================================================

USER_ID = "USER-001"


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
# 최종 Agent에서도 동일한 JSON 구조를 사용합니다.
#
# {
#     "user_id": "USER-001"
# }
#
# function / parameters 구조를 사용하지 않습니다.
#
# ============================================================

payload = {
    "user_id": USER_ID
}


# ============================================================
# 10. 호출 정보 출력
# ============================================================

print()

print("=" * 60)
print("User Lambda 호출 시작")
print("=" * 60)

print(
    "Region        :",
    REGION
)

print(
    "Lambda        :",
    USER_LAMBDA_NAME
)

print(
    "조회 User ID :",
    USER_ID
)

print(
    ".env File     :",
    ENV_FILE
)


# ============================================================
# 11. Lambda 실제 전송 Payload 출력
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

        # 호출할 Lambda 함수
        FunctionName=USER_LAMBDA_NAME,

        # Lambda 실행 완료 후 응답을 기다립니다.
        InvocationType="RequestResponse",

        # Python Dictionary
        #       ↓
        # JSON 문자열
        #       ↓
        # UTF-8 Byte 데이터
        Payload=json.dumps(
            payload,
            ensure_ascii=False
        ).encode("utf-8")
    )


# ============================================================
# 13. AWS Client 오류 처리
# ============================================================

except ClientError as error:

    print()

    print("=" * 60)
    print("AWS Lambda 호출 실패")
    print("=" * 60)

    print(error)

    sys.exit(1)


# ============================================================
# 14. 기타 오류 처리
# ============================================================

except Exception as error:

    print()

    print("=" * 60)
    print("예상하지 못한 오류 발생")
    print("=" * 60)

    print(error)

    sys.exit(1)


# ============================================================
# 15. AWS Lambda 호출 상태 확인
# ============================================================

http_status = (
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
    http_status
)


# ============================================================
# 16. Lambda 응답 읽기
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
# 17. Lambda 내부 실행 오류 확인
# ============================================================

if "FunctionError" in response:

    print()

    print("=" * 60)
    print("Lambda 함수 내부 실행 오류")
    print("=" * 60)

    print(response_payload)

    sys.exit(1)


# ============================================================
# 18. JSON 응답 → Python Dictionary
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
# 19. Lambda 처리 결과 확인
# ============================================================

if not result.get("success"):

    print()

    print("=" * 60)
    print("사용자 조회 실패")
    print("=" * 60)

    print(
        "message :",
        result.get(
            "message",
            "알 수 없는 오류"
        )
    )

    # Lambda에서 received_event를 반환하는 경우
    # 실제 전달된 Event도 출력합니다.

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
# 20. 사용자 정보 추출
# ============================================================
#
# Lambda 구현에 따라
#
# user_id
#
# 또는
#
# id
#
# 로 반환할 수 있으므로 둘 다 대응합니다.
#
# ============================================================

user_id = (
    result.get("user_id")
    or result.get("id")
)

name = result.get(
    "name"
)

email = result.get(
    "email"
)

subscription_status = result.get(
    "subscription_status"
)

subscription_end = result.get(
    "subscription_end"
)


# ============================================================
# 21. 사용자 조회 결과 출력
# ============================================================

print()

print("=" * 60)
print("사용자 조회 결과")
print("=" * 60)

print(
    "success             :",
    result.get("success")
)

print(
    "user_id             :",
    user_id
)

print(
    "name                :",
    name
)

print(
    "email               :",
    email
)

print(
    "subscription_status :",
    subscription_status
)

print(
    "subscription_end    :",
    subscription_end
)


# ============================================================
# 22. 필수 User ID 확인
# ============================================================

if not user_id:

    print()

    print("=" * 60)
    print("테스트 결과 확인 필요")
    print("=" * 60)

    print(
        "Lambda 응답에 "
        "user_id 또는 id가 없습니다."
    )

    sys.exit(1)


# ============================================================
# 23. 요청 ID와 응답 ID 비교
# ============================================================

if user_id != USER_ID:

    print()

    print("=" * 60)
    print("테스트 결과 확인 필요")
    print("=" * 60)

    print(
        "요청 User ID:",
        USER_ID
    )

    print(
        "응답 User ID:",
        user_id
    )

    sys.exit(1)


# ============================================================
# 24. 최종 성공
# ============================================================

print()

print("=" * 60)
print("User Lambda 테스트 성공")
print("=" * 60)

print(
    f"{USER_ID} 사용자 정보를 "
    f"정상적으로 조회했습니다."
)

print()

print(
    f"사용자 이름   : {name}"
)

print(
    f"이메일        : {email}"
)

print(
    f"구독 상태     : {subscription_status}"
)

print(
    f"구독 종료일   : {subscription_end}"
)

print("=" * 60)