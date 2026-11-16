# ============================================================
# AWS boto3 연결 테스트
# ============================================================

import os
import boto3

from pathlib import Path
from dotenv import load_dotenv


# ============================================================
# 1. .env 파일 읽기
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_FILE)


# ============================================================
# 2. AWS Region 가져오기
# ============================================================

REGION = os.getenv(
    "PETSTORE_REGION",
    "ap-northeast-2"
)


# ============================================================
# 3. boto3 Session 생성
# ============================================================

session = boto3.Session(
    region_name=REGION
)


# ============================================================
# 4. 현재 AWS 로그인 정보 확인
#
# STS = Security Token Service
# 현재 어떤 AWS 사용자/Role로 로그인되어 있는지 확인합니다.
# ============================================================

sts_client = session.client("sts")

identity = sts_client.get_caller_identity()


# ============================================================
# 5. AWS Client 생성
# ============================================================

# Lambda 호출용
lambda_client = session.client(
    "lambda"
)

# Bedrock Knowledge Base 호출용
kb_client = session.client(
    "bedrock-agent-runtime"
)

# Amazon Nova 호출용
bedrock_runtime = session.client(
    "bedrock-runtime"
)


# ============================================================
# 6. 결과 출력
# ============================================================

print("========================================")
print("AWS boto3 연결 테스트")
print("========================================")

print("AWS Region :", REGION)
print("Account ID :", identity["Account"])
print("ARN        :", identity["Arn"])

print()
print("Lambda Client             : 생성 성공")
print("Bedrock Agent Runtime     : 생성 성공")
print("Bedrock Runtime           : 생성 성공")

print("========================================")
print("AWS boto3 연결 성공")
print("========================================")