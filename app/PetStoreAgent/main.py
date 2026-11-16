# ============================================================
# Pet Store AI Agent
# Final Deployment Version
# ============================================================
#
# 주요 기능
# ------------------------------------------------------------
# 1. ProductInformation Knowledge Base 검색
# 2. PetCaringKnowledge Knowledge Base 검색
# 3. Inventory Lambda를 이용한 실시간 재고 조회
# 4. User Lambda를 이용한 회원 정보 조회
# 5. Amazon Nova Pro 기반 AI Agent
# 6. AWS Bedrock AgentCore Runtime 배포
#
#
# 전체 구조
# ------------------------------------------------------------
#
# 사용자
#   ↓
# PetStore AI Agent
#   │
#   ├── product_search()
#   │       └── ProductInformation KB
#   │
#   ├── pet_care_search()
#   │       └── PetCaringKnowledge KB
#   │
#   ├── inventory_lookup()
#   │       └── PetStoreInventoryManagementFunction
#   │
#   └── user_lookup()
#           └── PetStoreUserManagementFunction
#
# ============================================================


# ============================================================
# 01. 필요한 라이브러리 Import
# ============================================================

import json
import os
import re

import boto3

from botocore.exceptions import ClientError

from strands import Agent, tool
from strands.models import BedrockModel

from bedrock_agentcore.runtime import BedrockAgentCoreApp


# ============================================================
# 02. 기본 환경 설정
# ============================================================

# AWS Region
REGION = os.getenv(
    "PETSTORE_REGION",
    "ap-northeast-2"
)


# ------------------------------------------------------------
# ProductInformation Knowledge Base
# ------------------------------------------------------------

PRODUCT_KB_ID = os.getenv(
    "PRODUCT_KB_ID",
    "LTAAXCBPNS"
)


# ------------------------------------------------------------
# PetCaringKnowledge Knowledge Base
# ------------------------------------------------------------

PET_CARE_KB_ID = os.getenv(
    "PET_CARE_KB_ID",
    "0ETB2OLDFT"
)


# ------------------------------------------------------------
# Inventory Lambda
# ------------------------------------------------------------

INVENTORY_LAMBDA_NAME = os.getenv(
    "INVENTORY_LAMBDA_NAME",
    "PetStoreInventoryManagementFunction"
)


# ------------------------------------------------------------
# User Lambda
# ------------------------------------------------------------

USER_LAMBDA_NAME = os.getenv(
    "USER_LAMBDA_NAME",
    "PetStoreUserManagementFunction"
)


# ------------------------------------------------------------
# Amazon Nova Pro
# ------------------------------------------------------------

MODEL_ID = os.getenv(
    "NOVA_MODEL_ID",
    "apac.amazon.nova-pro-v1:0"
)


# ============================================================
# 03. AgentCore Application 생성
# ============================================================

app = BedrockAgentCoreApp()


# ============================================================
# 04. AWS Client 생성
# ============================================================

# ------------------------------------------------------------
# Lambda Client
# ------------------------------------------------------------

lambda_client = boto3.client(
    "lambda",
    region_name=REGION
)


# ------------------------------------------------------------
# Bedrock Knowledge Base Runtime Client
# ------------------------------------------------------------

kb_client = boto3.client(
    "bedrock-agent-runtime",
    region_name=REGION
)


# ============================================================
# 05. Amazon Nova Pro 모델 생성
# ============================================================

model = BedrockModel(
    model_id=MODEL_ID,
    region_name=REGION,
    temperature=0.1
)


# ============================================================
# 06. Lambda 공통 호출 함수
# ============================================================

def invoke_lambda(function_name: str, payload: dict) -> dict:
    """
    AWS Lambda를 동기 방식으로 호출합니다.

    Parameters
    ----------
    function_name:
        호출할 Lambda 함수 이름

    payload:
        Lambda로 전달할 JSON 데이터

    Returns
    -------
    dict
        Lambda에서 반환된 JSON 결과
    """

    try:

        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(
                payload,
                ensure_ascii=False
            ).encode("utf-8")
        )

        # ----------------------------------------------------
        # Lambda 응답 읽기
        # ----------------------------------------------------

        raw_payload = response["Payload"].read()

        if not raw_payload:

            return {
                "success": False,
                "message": "Lambda 응답이 없습니다."
            }

        result = json.loads(
            raw_payload.decode("utf-8")
        )

        # ----------------------------------------------------
        # Lambda 자체 실행 오류 확인
        # ----------------------------------------------------

        if response.get("FunctionError"):

            return {
                "success": False,
                "message": "Lambda 실행 중 오류가 발생했습니다.",
                "detail": result
            }

        # ----------------------------------------------------
        # API Gateway 형식의 Lambda 응답도 처리
        #
        # 예:
        #
        # {
        #     "statusCode": 200,
        #     "body": "{\"success\": true}"
        # }
        # ----------------------------------------------------

        if (
            isinstance(result, dict)
            and "body" in result
        ):

            body = result["body"]

            if isinstance(body, str):

                try:

                    result = json.loads(body)

                except json.JSONDecodeError:

                    result = {
                        "success": True,
                        "body": body
                    }

        return result

    except ClientError as error:

        print(
            f"[Lambda ClientError] "
            f"{function_name}: {error}"
        )

        return {
            "success": False,
            "message": str(error)
        }

    except Exception as error:

        print(
            f"[Lambda Error] "
            f"{function_name}: {error}"
        )

        return {
            "success": False,
            "message": str(error)
        }


# ============================================================
# 07. Knowledge Base 공통 검색 함수
# ============================================================

def retrieve_kb(
    knowledge_base_id: str,
    query: str,
    number_of_results: int = 10
) -> list:
    """
    Amazon Bedrock Knowledge Base를 검색합니다.

    검색된 원문을 삭제하거나 변경하지 않고
    Agent에게 전달하기 위한 공통 함수입니다.
    """

    try:

        response = kb_client.retrieve(

            knowledgeBaseId=knowledge_base_id,

            retrievalQuery={
                "text": query
            },

            retrievalConfiguration={
                "vectorSearchConfiguration": {
                    "numberOfResults": number_of_results
                }
            }
        )

        results = []

        # ----------------------------------------------------
        # 검색 결과 정리
        # ----------------------------------------------------

        for item in response.get(
            "retrievalResults",
            []
        ):

            content = item.get(
                "content",
                {}
            )

            text = content.get(
                "text",
                ""
            )

            if not text:
                continue

            results.append(
                {
                    "text": text,
                    "score": item.get("score")
                }
            )

        return results

    except ClientError as error:

        print(
            f"[Knowledge Base ClientError] "
            f"{knowledge_base_id}: {error}"
        )

        return []

    except Exception as error:

        print(
            f"[Knowledge Base Error] "
            f"{knowledge_base_id}: {error}"
        )

        return []


# ============================================================
# 08. 상품 종류 참고 판별 함수
# ============================================================

def detect_product_type(text: str) -> str:
    """
    Knowledge Base의 상품 설명에서 상품 종류를
    참고용으로 판별합니다.

    중요:
    이 함수의 결과만으로 KB 검색 결과를 삭제하지 않습니다.

    최종 상품 분류는 Nova Pro가 원본 text를 읽고
    SYSTEM_PROMPT의 규칙에 따라 결정합니다.
    """

    if not text:
        return "other"

    value = text.lower()


    # ========================================================
    # 1. 강아지/고양이 사료
    #
    # 간식보다 먼저 food를 검사합니다.
    # ========================================================

    if (
        "wet dog food" in value
        or "dry dog food" in value
        or "dog food" in value
    ):
        return "dog_food"


    if (
        "wet cat food" in value
        or "dry cat food" in value
        or "cat food" in value
    ):
        return "cat_food"


    # ========================================================
    # 2. 간식
    # ========================================================

    if (
        "dog treats" in value
        or "dog treat" in value
        or "chew bones" in value
        or "dog chews" in value
    ):
        return "dog_treat"


    if (
        "cat treats" in value
        or "cat treat" in value
    ):
        return "cat_treat"


    # ========================================================
    # 3. 장난감
    # ========================================================

    if (
        "puzzle toys" in value
        or "toys" in value
        or "toy" in value
        or "ball" in value
        or "scratching post" in value
    ):
        return "toy"


    # ========================================================
    # 4. 기타
    # ========================================================

    return "other"


# ============================================================
# 09. Product Knowledge Base Tool
# ============================================================

@tool
def product_search(query: str) -> str:
    """
    Pet Store 상품 정보를 검색합니다.

    상품명, 상품 코드, 상품 설명,
    카테고리, 가격 등의 기본 상품 정보를
    조회할 때 사용합니다.

    중요:
    이 Tool에서는 KB 검색 결과를 강제로 제거하지 않습니다.

    모든 검색 결과의 원본 text를 Agent에게 전달합니다.

    현재 실제 재고는 이 Tool에서 판단하지 않습니다.
    재고는 inventory_lookup을 사용해야 합니다.
    """

    print(
        f"[TOOL] product_search: {query}"
    )

    # --------------------------------------------------------
    # ProductInformation Knowledge Base 검색
    # --------------------------------------------------------

    results = retrieve_kb(
        PRODUCT_KB_ID,
        query,
        number_of_results=15
    )

    # --------------------------------------------------------
    # 검색 실패
    # --------------------------------------------------------

    if not results:

        return json.dumps(
            {
                "success": False,
                "message": (
                    "ProductInformation Knowledge Base에서 "
                    "상품 정보를 검색할 수 없습니다."
                )
            },
            ensure_ascii=False
        )


    # --------------------------------------------------------
    # 검색 결과를 삭제하지 않고 그대로 Agent에게 전달
    # --------------------------------------------------------

    formatted_results = []

    for result in results:

        text = result.get(
            "text",
            ""
        )

        formatted_results.append(
            {
                # KB 원본 상품 정보
                "text": text,

                # Python이 판단한 참고용 상품 종류
                "detected_product_type":
                    detect_product_type(text),

                # Vector Search 점수
                "score": result.get("score")
            }
        )


    # --------------------------------------------------------
    # Agent에게 JSON 형식으로 전달
    # --------------------------------------------------------

    return json.dumps(
        {
            "success": True,

            "query": query,

            "results": formatted_results,

            "classification_rule": (
                "검색 결과를 상품명만으로 분류하지 마십시오. "
                "반드시 각 results 항목의 text에 포함된 "
                "상품 설명을 확인하십시오. "
                "dry/wet dog food는 강아지 사료입니다. "
                "dog treats와 chews는 강아지 간식입니다. "
                "dry/wet cat food는 고양이 사료입니다. "
                "cat treats는 고양이 간식입니다. "
                "toys는 장난감입니다. "
                "detected_product_type은 참고 정보이며 "
                "최종 분류는 text 원문을 기준으로 결정하십시오."
            )
        },
        ensure_ascii=False
    )


# ============================================================
# 10. Pet Care Knowledge Base Tool
# ============================================================

@tool
def pet_care_search(query: str) -> str:
    """
    반려동물 관리 및 돌봄 정보를 검색합니다.

    예:
    - 강아지 건강 관리
    - 고양이 관리
    - 식사 관리
    - 생활 습관
    - 일반적인 반려동물 돌봄 정보
    """

    print(
        f"[TOOL] pet_care_search: {query}"
    )

    results = retrieve_kb(
        PET_CARE_KB_ID,
        query,
        number_of_results=8
    )

    if not results:

        return json.dumps(
            {
                "success": False,
                "message": (
                    "PetCaringKnowledge Knowledge Base에서 "
                    "반려동물 관리 정보를 검색할 수 없습니다."
                )
            },
            ensure_ascii=False
        )

    return json.dumps(
        {
            "success": True,
            "query": query,
            "results": results
        },
        ensure_ascii=False
    )


# ============================================================
# 11. Inventory Lambda Tool
# ============================================================

@tool
def inventory_lookup(
    product_code: str
) -> str:
    """
    상품 코드로 현재 실제 재고를 조회합니다.

    반환 정보 예:
    - 상품 코드
    - 상품명
    - 현재 재고
    - 재주문 기준
    - 재고 상태
    - 마지막 업데이트
    """

    product_code = (
        product_code
        .strip()
        .upper()
    )

    print(
        f"[TOOL] inventory_lookup: "
        f"{product_code}"
    )

    if not product_code:

        return json.dumps(
            {
                "success": False,
                "message": "상품 코드가 필요합니다."
            },
            ensure_ascii=False
        )

    result = invoke_lambda(
        INVENTORY_LAMBDA_NAME,
        {
            "product_code": product_code
        }
    )

    return json.dumps(
        result,
        ensure_ascii=False
    )


# ============================================================
# 12. User Lambda Tool
# ============================================================

@tool
def user_lookup(
    user_id: str
) -> str:
    """
    회원 ID로 회원 정보를 조회합니다.

    반환 정보 예:
    - 회원 ID
    - 회원 이름
    - 회원 등급
    - 포인트
    - 반려동물 종류
    - 반려동물 이름
    """

    user_id = (
        user_id
        .strip()
        .upper()
    )

    print(
        f"[TOOL] user_lookup: "
        f"{user_id}"
    )

    if not user_id:

        return json.dumps(
            {
                "success": False,
                "message": "회원 ID가 필요합니다."
            },
            ensure_ascii=False
        )

    result = invoke_lambda(
        USER_LAMBDA_NAME,
        {
            "user_id": user_id
        }
    )

    return json.dumps(
        result,
        ensure_ascii=False
    )


# ============================================================
# 13. Agent System Prompt
# ============================================================

SYSTEM_PROMPT = """
당신은 Pet Store AI Agent입니다.

사용자의 질문을 분석하고 필요한 Tool만 사용하여
정확한 답변을 한국어로 제공하십시오.


============================================================
1. Tool 사용 규칙
============================================================

상품명, 상품 코드, 상품 설명, 상품 카테고리,
가격에 관한 질문:

→ product_search를 사용하십시오.


현재 재고 수량, 재주문 기준,
재고 상태에 관한 질문:

→ inventory_lookup을 사용하십시오.


회원 이름, 회원 등급, 포인트,
반려동물 정보에 관한 질문:

→ user_lookup을 사용하십시오.


반려동물 관리, 건강, 생활 습관,
돌봄 정보에 관한 질문:

→ pet_care_search를 사용하십시오.



============================================================
2. 상품 분류의 가장 중요한 규칙
============================================================

product_search가 반환한 상품을
상품명만 보고 분류하지 마십시오.

반드시 results의 text에 포함된
상품 설명을 읽고 최종 상품 종류를 결정하십시오.


detected_product_type은 참고 정보입니다.

최종 판단은 반드시 원본 text를 기준으로 하십시오.



============================================================
3. 강아지 사료 분류 규칙
============================================================

다음 설명은 강아지 사료입니다.

- dog food
- dry dog food
- wet dog food
- grain-free dry dog food


예:

Doggy Delights
설명:
Grain-free dry dog food

→ 강아지 사료
→ "강아지 사료" 질문에 포함



다음은 강아지 사료가 아닙니다.

- dog treats
- dog treat
- chew
- chews
- chew bones
- toys
- puzzle toys


예:

Bark Bites
설명:
Savory dog treats

→ 강아지 간식
→ "강아지 사료" 질문에서 제외


Canine Carnival
설명:
toys / chews

→ 장난감 또는 간식
→ "강아지 사료" 질문에서 제외



============================================================
4. 고양이 사료 분류 규칙
============================================================

다음 설명은 고양이 사료입니다.

- cat food
- dry cat food
- wet cat food


예:

Meow Munchies
설명:
Gourmet wet cat food

→ 고양이 사료
→ "고양이 사료" 질문에 포함



다음은 고양이 사료가 아닙니다.

- cat treats
- cat treat
- toys
- cat toys


예:

Kitty Krunchers
설명:
Crunchy cat treats

→ 고양이 간식
→ "고양이 사료" 질문에서 제외


Feline Fiesta
설명:
toys and treats

→ 장난감/간식
→ "고양이 사료" 질문에서 제외



============================================================
5. 재고 조회 규칙
============================================================

Knowledge Base의 상품 설명을 이용하여
현재 재고를 추측해서는 안 됩니다.

현재 재고에 대한 질문이 들어오면:

1. product_search로 필요한 상품을 찾습니다.
2. 상품 설명을 기준으로 요청한 카테고리에 해당하는
   상품만 선택합니다.
3. 선택된 상품의 상품 코드를 확인합니다.
4. 상품 코드별로 inventory_lookup을 한 번씩 호출합니다.
5. inventory_lookup의 quantity를 현재 재고로 사용합니다.


inventory_lookup이 success=false를 반환하면:

"해당 상품의 현재 재고 데이터는 확인할 수 없습니다."

라고 설명하십시오.


재고를 임의로 생성하지 마십시오.



============================================================
6. 가격 규칙
============================================================

상품 가격은 반드시
ProductInformation Knowledge Base의
product_search 결과를 사용하십시오.

가격을 임의로 생성하지 마십시오.

Inventory Lambda의 quantity는 재고 수량이며
가격이 아닙니다.



============================================================
7. 전체 재고금액 계산 규칙
============================================================

사용자가 전체 재고금액을 요청하면
다음 공식을 사용하십시오.


상품별 재고금액 = 상품 단가 × 현재 재고 수량


전체 재고금액 = 모든 상품별 재고금액의 합계


예:

상품 가격 = $54.99

현재 재고 = 20개


계산:

$54.99 × 20 = $1,099.80


계산 결과를 제공할 때
반드시 사용한 가격과 재고 수량을 같이 보여주십시오.



============================================================
8. Tool 호출 순서
============================================================

예를 들어 사용자가 다음과 같이 질문합니다.


"강아지 사료 상품명, 가격, 현재 재고와
전체 재고금액을 알려줘"


다음 순서로 처리하십시오.


STEP 1

product_search 호출


STEP 2

검색 결과의 text를 확인


STEP 3

실제 강아지 사료만 선택


STEP 4

선택한 상품의 product_code 확인


STEP 5

각 product_code에 대해 inventory_lookup 호출


STEP 6

가격 × quantity 계산


STEP 7

최종 답변 작성



============================================================
9. Tool 반복 호출 방지
============================================================

동일한 질문에 대해
동일한 Tool을 동일한 인자로 반복 호출하지 마십시오.


product_search 결과에서 필요한 상품 코드와
가격을 이미 확보했다면 product_search를
다시 호출하지 마십시오.


inventory_lookup 결과를 받은 상품 코드는
다시 inventory_lookup하지 마십시오.


필요한 정보가 확보되면 Tool 호출을 종료하고
최종 답변을 작성하십시오.



============================================================
10. 정확성 규칙
============================================================

Tool이 반환하지 않은 다음 정보를
임의로 생성하지 마십시오.

- 상품
- 상품 코드
- 가격
- 재고
- 회원 정보
- 포인트


검색 또는 조회되지 않은 정보는

"확인할 수 없습니다."

라고 답하십시오.


Tool 호출에 실패한 경우
성공한 것처럼 답하지 마십시오.



============================================================
11. 회원 정보 규칙
============================================================

회원 정보를 요청받으면
반드시 user_lookup을 사용하십시오.


예:

"USER-001 회원 정보를 알려줘"


→ user_lookup("USER-001")


Lambda가 반환한:

- name
- membership
- points
- pet_type
- pet_name

을 사용하여 답변하십시오.



============================================================
12. 반려동물 관리 규칙
============================================================

반려동물 건강, 관리, 돌봄 등에 관한 질문은
pet_care_search를 사용하십시오.


Knowledge Base 검색 결과를 근거로 답변하고
검색되지 않은 전문적인 의료 내용을
임의로 생성하지 마십시오.



============================================================
13. 최종 답변 형식
============================================================

답변은 한국어로 작성하십시오.


상품이 여러 개인 경우 가능한 한 다음 정보를
구분하여 표시하십시오.

- 상품 코드
- 상품명
- 상품 분류
- 가격
- 현재 재고
- 상품별 재고금액


전체 재고금액을 요청한 경우
마지막에 전체 금액을 표시하십시오.


불필요한 사과 문구를 반복하지 마십시오.

Tool 이름이나 내부 처리 과정을
최종 사용자에게 설명하지 마십시오.

내부 추론 과정도 표시하지 마십시오.


최종 답변 안에 문자 그대로의 다음 escape 문자열을
출력하지 마십시오.

\\n
/n
\\r
\\t
"""


# ============================================================
# 14. Pet Store Agent 생성
# ============================================================

agent = Agent(

    model=model,

    tools=[
        product_search,
        pet_care_search,
        inventory_lookup,
        user_lookup
    ],

    system_prompt=SYSTEM_PROMPT
)


# ============================================================
# 15. Agent 응답 정리 함수
# ============================================================

def clean_response(response) -> str:
    """
    Strands Agent가 반환한 결과를
    최종 사용자 응답 문자열로 정리합니다.
    """

    text = str(response).strip()


    # ========================================================
    # JSON 문자열이 여러 번 감싸진 경우 처리
    # ========================================================

    for _ in range(3):

        try:

            decoded = json.loads(text)

            # ------------------------------------------------
            # JSON 문자열
            # ------------------------------------------------

            if isinstance(decoded, str):

                text = decoded.strip()

                continue


            # ------------------------------------------------
            # {"answer": "..."} 형태
            # ------------------------------------------------

            if (
                isinstance(decoded, dict)
                and "answer" in decoded
            ):

                text = str(
                    decoded["answer"]
                ).strip()

                continue


            break

        except Exception:

            break


    # ========================================================
    # thinking 태그 제거
    # ========================================================

    text = re.sub(
        r"<thinking>.*?</thinking>",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE
    )


    text = re.sub(
        r"</?thinking>",
        "",
        text,
        flags=re.IGNORECASE
    )


    # ========================================================
    # 실제 문자열 escape가 포함된 경우 정리
    # ========================================================

    for _ in range(3):

        old_text = text

        text = text.replace(
            "\\r\\n",
            "\n"
        )

        text = text.replace(
            "\\n",
            "\n"
        )

        text = text.replace(
            "\\r",
            "\n"
        )

        text = text.replace(
            "\\t",
            " "
        )

        text = text.replace(
            "/n",
            "\n"
        )

        if text == old_text:

            break


    # ========================================================
    # CR 제거
    # ========================================================

    text = text.replace(
        "\r",
        ""
    )


    text = text.strip()


    # ========================================================
    # 바깥쪽 따옴표 제거
    # ========================================================

    while (
        len(text) >= 2
        and text.startswith('"')
        and text.endswith('"')
    ):

        text = text[1:-1].strip()


    # ========================================================
    # 줄 끝 공백 제거
    # ========================================================

    lines = [
        line.rstrip()
        for line in text.splitlines()
    ]


    text = "\n".join(
        lines
    )


    # ========================================================
    # 빈 줄이 너무 많이 생성되는 것 방지
    # ========================================================

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )


    return text.strip()


# ============================================================
# 16. AgentCore Runtime Entrypoint
# ============================================================

@app.entrypoint
def invoke(payload):
    """
    AWS Bedrock AgentCore Runtime에서
    요청을 받는 진입점입니다.
    """

    try:

        # ====================================================
        # 입력 Prompt 추출
        # ====================================================

        if isinstance(
            payload,
            dict
        ):

            prompt = (
                payload.get("prompt")
                or payload.get("message")
                or payload.get("input")
                or ""
            )

        else:

            prompt = str(
                payload
            )


        prompt = str(
            prompt
        ).strip()


        # ====================================================
        # 빈 질문 방지
        # ====================================================

        if not prompt:

            return "질문을 입력해 주세요."


        # ====================================================
        # 요청 로그
        # ====================================================

        print(
            f"[REQUEST] {prompt}"
        )


        # ====================================================
        # Agent 실행
        # ====================================================

        response = agent(
            prompt
        )


        # ====================================================
        # 최종 응답 정리
        # ====================================================

        answer = clean_response(
            response
        )


        # ====================================================
        # 응답 로그
        # ====================================================

        print(
            f"[RESPONSE] {answer}"
        )


        # ====================================================
        # AgentCore 최종 응답
        # ====================================================

        return answer


    except Exception as error:

        print(
            f"[Agent Error] "
            f"{type(error).__name__}: "
            f"{error}"
        )

        return (
            "요청 처리 중 오류가 발생했습니다. "
            "AgentCore Runtime 로그를 확인해 주세요."
        )


# ============================================================
# 17. Local 실행
# ============================================================

if __name__ == "__main__":

    app.run()