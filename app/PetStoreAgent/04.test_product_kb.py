# ============================================================
# ProductInformation KB + Amazon Nova Pro RAG 테스트
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
# 2. 환경변수 가져오기
# ============================================================

REGION = os.getenv(
    "PETSTORE_REGION",
    "ap-northeast-2"
)

PRODUCT_KB_ID = os.getenv(
    "PRODUCT_KB_ID"
)

NOVA_MODEL_ID = os.getenv(
    "NOVA_MODEL_ID",
    "amazon.nova-pro-v1:0"
)


# ============================================================
# 3. 필수 환경변수 확인
# ============================================================

if not PRODUCT_KB_ID:
    raise ValueError(
        ".env 파일에 PRODUCT_KB_ID가 없습니다."
    )


# ============================================================
# 4. AWS Client 생성
# ============================================================

# Knowledge Base 검색용
kb_client = boto3.client(
    "bedrock-agent-runtime",
    region_name=REGION
)


# Amazon Nova 호출용
bedrock_runtime = boto3.client(
    "bedrock-runtime",
    region_name=REGION
)


# ============================================================
# 5. 사용자가 질문할 내용
# ============================================================

USER_QUESTION = """
Bark Park Buddy 제품의
제품 코드와 가격을 알려주세요.
"""


print("=" * 60)
print("사용자 질문")
print("=" * 60)

print(USER_QUESTION.strip())

print()


# ============================================================
# 6. ProductInformation Knowledge Base 검색
# ============================================================

print("=" * 60)
print("1단계 - ProductInformation KB 검색")
print("=" * 60)


response = kb_client.retrieve(

    knowledgeBaseId=PRODUCT_KB_ID,

    retrievalQuery={
        "text": USER_QUESTION
    },

    retrievalConfiguration={
        "vectorSearchConfiguration": {
            "numberOfResults": 5
        }
    }
)


# ============================================================
# 7. Knowledge Base 검색 결과 가져오기
# ============================================================

results = response.get(
    "retrievalResults",
    []
)


print(
    "검색 결과 개수 :",
    len(results)
)

print()


# ============================================================
# 8. 검색 결과를 하나의 Context로 합치기
#
# Nova에게 전달하기 위해
#
# 검색 결과 #1
# 검색 결과 #2
# ...
#
# 형태의 문자열로 만듭니다.
# ============================================================

context_parts = []


for index, item in enumerate(
    results,
    start=1
):

    content = item.get(
        "content",
        {}
    )

    text = content.get(
        "text",
        ""
    )

    if text:

        context_parts.append(
            f"[검색 결과 {index}]\n{text}"
        )


# 모든 검색 결과 합치기
CONTEXT = "\n\n".join(
    context_parts
)


# ============================================================
# 9. 검색 결과 출력
# ============================================================

print("=" * 60)
print("Knowledge Base 검색 결과")
print("=" * 60)

print(CONTEXT)

print()


# ============================================================
# 10. 검색 결과가 없는 경우 종료
# ============================================================

if not CONTEXT:

    print(
        "Knowledge Base에서 관련 문서를 찾지 못했습니다."
    )

    raise SystemExit(1)


# ============================================================
# 11. Nova에게 전달할 System Prompt
#
# Nova가 자기 지식으로 임의 답변하지 않고
# Knowledge Base에서 검색한 정보만 사용하도록 합니다.
# ============================================================

SYSTEM_PROMPT = """
당신은 온라인 Pet Store의 상품 안내 AI입니다.

반드시 제공된 ProductInformation Knowledge Base 검색 결과를
근거로만 답변하세요.

검색 결과에 없는 제품 코드나 가격을 임의로 만들지 마세요.

사용자가 상품 정보를 물어보면 다음 내용을 우선 확인하세요.

1. 상품 이름
2. 제품 코드
3. 가격

답변은 한국어로 간결하고 정확하게 작성하세요.
"""


# ============================================================
# 12. Nova에게 전달할 User Prompt
#
# 사용자 질문 + KB 검색 결과를 함께 전달합니다.
# ============================================================

NOVA_PROMPT = f"""
다음은 사용자의 질문입니다.

[사용자 질문]

{USER_QUESTION}


다음은 ProductInformation Knowledge Base에서
검색한 자료입니다.

[Knowledge Base 검색 결과]

{CONTEXT}


위 검색 결과를 근거로 사용자의 질문에 답변하세요.
"""


# ============================================================
# 13. Amazon Nova Pro 호출
#
# Bedrock Converse API를 사용합니다.
# ============================================================

print("=" * 60)
print("2단계 - Amazon Nova Pro 호출")
print("=" * 60)

print("Model :", NOVA_MODEL_ID)
print()


nova_response = bedrock_runtime.converse(

    modelId=NOVA_MODEL_ID,

    # System Prompt
    system=[
        {
            "text": SYSTEM_PROMPT
        }
    ],

    # User Message
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "text": NOVA_PROMPT
                }
            ]
        }
    ],

    # 모델 생성 설정
    inferenceConfig={
        "maxTokens": 1000,
        "temperature": 0.1,
        "topP": 0.9
    }
)


# ============================================================
# 14. Nova 응답에서 최종 텍스트 가져오기
# ============================================================

output_message = nova_response[
    "output"
][
    "message"
]


answer_parts = []


for content in output_message.get(
    "content",
    []
):

    if "text" in content:

        answer_parts.append(
            content["text"]
        )


FINAL_ANSWER = "\n".join(
    answer_parts
)


# ============================================================
# 15. Nova 최종 답변 출력
# ============================================================

print("=" * 60)
print("Amazon Nova 최종 답변")
print("=" * 60)

print(FINAL_ANSWER)

print()


# ============================================================
# 16. Token 사용량 출력
# ============================================================

usage = nova_response.get(
    "usage",
    {}
)


print("=" * 60)
print("Token 사용량")
print("=" * 60)

print(
    "Input Tokens :",
    usage.get("inputTokens")
)

print(
    "Output Tokens:",
    usage.get("outputTokens")
)

print(
    "Total Tokens :",
    usage.get("totalTokens")
)


print()
print("=" * 60)
print("ProductInformation KB + Nova 테스트 완료")
print("=" * 60)