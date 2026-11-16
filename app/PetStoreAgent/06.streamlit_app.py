# ============================================================
# Pet Store AI Agent - Streamlit UI
# ============================================================
#
# 현재 main.py의 Agent를 직접 사용합니다.
#
# main.py
#   ├─ Amazon Nova Pro
#   ├─ ProductInformation Knowledge Base
#   ├─ PetCaringKnowledge Knowledge Base
#   ├─ Inventory Lambda
#   ├─ User Lambda
#   ├─ agent
#   └─ clean_response
#
# streamlit_app.py
#   └─ 사용자 Web UI
#
# ============================================================


# ============================================================
# 01. 라이브러리 Import
# ============================================================

import streamlit as st


# ------------------------------------------------------------
# main.py에서 현재 실제 존재하는 객체를 가져옵니다.
#
# 기존:
# from main import process_pet_store_request
#
# 수정:
# agent와 clean_response를 직접 사용합니다.
# ------------------------------------------------------------

from main import agent, clean_response


# ============================================================
# 02. Streamlit 페이지 설정
# ============================================================

st.set_page_config(
    page_title="Pet Store AI Agent",
    page_icon="🐶",
    layout="centered",
    initial_sidebar_state="collapsed"
)


# ============================================================
# 03. CSS 디자인
# ============================================================

st.markdown(
    """
    <style>

    /* 전체 화면 */
    .block-container {
        max-width: 1050px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    /* 메인 제목 */
    h1 {
        font-size: 44px !important;
        font-weight: 800 !important;
        margin-bottom: 10px !important;
    }

    /* 소제목 */
    h2 {
        font-size: 30px !important;
        font-weight: 750 !important;
    }

    h3 {
        font-size: 25px !important;
        font-weight: 700 !important;
    }

    /* 일반 글자 */
    p {
        font-size: 18px !important;
        line-height: 1.7 !important;
    }

    li {
        font-size: 18px !important;
        line-height: 1.7 !important;
    }

    /* 입력창 Label */
    label {
        font-size: 20px !important;
        font-weight: 700 !important;
    }

    /* 질문 입력창 */
    textarea {
        font-size: 20px !important;
        line-height: 1.6 !important;
    }

    /* 버튼 */
    div.stButton > button {
        min-height: 56px;
        font-size: 19px !important;
        font-weight: 700 !important;
        border-radius: 10px;
    }

    /* Primary 실행 버튼 */
    div.stButton > button[kind="primary"] {
        min-height: 65px;
        font-size: 22px !important;
        font-weight: 800 !important;
    }

    /* Expander */
    details {
        font-size: 17px !important;
    }

    /* Caption */
    .stCaption {
        font-size: 15px !important;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# 04. Session State 초기화
# ============================================================

if "answer" not in st.session_state:
    st.session_state.answer = ""


if "last_question" not in st.session_state:
    st.session_state.last_question = ""


if "example_prompt" not in st.session_state:
    st.session_state.example_prompt = ""


# ============================================================
# 05. Streamlit에서 Agent를 호출하는 함수
# ============================================================

def run_pet_store_agent(user_message: str) -> str:
    """
    main.py의 Pet Store Agent를 직접 호출합니다.

    처리 순서:

    사용자 질문
        ↓
    agent()
        ↓
    Nova Pro
        ↓
    필요한 Tool 선택
        ↓
    Knowledge Base / Lambda
        ↓
    clean_response()
        ↓
    최종 문자열
    """

    try:

        # ----------------------------------------------------
        # 사용자 질문 정리
        # ----------------------------------------------------

        user_message = str(
            user_message
        ).strip()


        # ----------------------------------------------------
        # 빈 질문 방지
        # ----------------------------------------------------

        if not user_message:

            return "질문을 입력해 주세요."


        # ----------------------------------------------------
        # 터미널 로그
        # ----------------------------------------------------

        print(
            f"[STREAMLIT REQUEST] "
            f"{user_message}"
        )


        # ----------------------------------------------------
        # Pet Store Agent 실행
        # ----------------------------------------------------

        response = agent(
            user_message
        )


        # ----------------------------------------------------
        # Agent 결과 정리
        # ----------------------------------------------------

        answer = clean_response(
            response
        )


        # ----------------------------------------------------
        # 터미널 응답 로그
        # ----------------------------------------------------

        print(
            f"[STREAMLIT RESPONSE] "
            f"{answer}"
        )


        return answer


    except Exception as error:

        # ----------------------------------------------------
        # 실제 오류는 Streamlit 실행 터미널에도 표시
        # ----------------------------------------------------

        print(
            f"[STREAMLIT ERROR] "
            f"{type(error).__name__}: "
            f"{error}"
        )


        # ----------------------------------------------------
        # UI에 표시할 오류
        # ----------------------------------------------------

        return (
            "요청 처리 중 오류가 발생했습니다.\n\n"
            f"오류 유형: {type(error).__name__}\n\n"
            f"오류 내용: {error}"
        )


# ============================================================
# 06. 화면 제목
# ============================================================

st.title("🐶 Pet Store AI Agent")


st.markdown(
    """
    Amazon Bedrock **Nova Pro**, **Knowledge Base**,
    **AWS Lambda**를 활용한 Pet Store AI Agent입니다.
    """
)


# ============================================================
# 07. 시스템 구성 보기
# ============================================================

with st.expander(
    "AI Agent 구성 보기",
    expanded=False
):

    st.markdown(
        """
        ### Pet Store AI Agent 구성

        사용자  
        ↓  
        **Streamlit UI**  
        ↓  
        **Pet Store AI Agent**  
        ↓  
        **Amazon Nova Pro**

        Agent가 질문을 분석하여 필요한 기능을 선택합니다.

        **상품 정보**

        ProductInformation Knowledge Base

        **반려동물 관리**

        PetCaringKnowledge Knowledge Base

        **현재 재고**

        Inventory Management Lambda

        **회원 정보**

        User Management Lambda
        """
    )


# ============================================================
# 08. 예제 질문
# ============================================================

st.subheader("예제 질문")


# ------------------------------------------------------------
# 첫 번째 줄
# ------------------------------------------------------------

col1, col2 = st.columns(2)


with col1:

    if st.button(
        "강아지 사료 검색",
        use_container_width=True
    ):

        st.session_state.example_prompt = (
            "강아지 사료 상품명과 가격을 알려줘"
        )


with col2:

    if st.button(
        "사료 + 재고금액 조회",
        use_container_width=True
    ):

        st.session_state.example_prompt = (
            "강아지 사료 상품명, 가격, "
            "현재 재고와 전체 재고금액을 알려줘"
        )


# ------------------------------------------------------------
# 두 번째 줄
# ------------------------------------------------------------

col3, col4 = st.columns(2)


with col3:

    if st.button(
        "DD006 재고 조회",
        use_container_width=True
    ):

        st.session_state.example_prompt = (
            "DD006 현재 재고를 알려줘"
        )


with col4:

    if st.button(
        "USER-001 회원 조회",
        use_container_width=True
    ):

        st.session_state.example_prompt = (
            "USER-001 회원 정보를 알려줘"
        )


# ------------------------------------------------------------
# 세 번째 줄
# ------------------------------------------------------------

if st.button(
    "강아지 관리 방법",
    use_container_width=True
):

    st.session_state.example_prompt = (
        "강아지를 건강하게 관리하는 방법을 알려줘"
    )


# ============================================================
# 09. 질문 입력
# ============================================================

st.divider()


st.subheader("Pet Store에 질문하세요")


user_prompt = st.text_area(

    "질문 입력",

    value=st.session_state.example_prompt,

    placeholder=(
        "예: 강아지 사료 상품명, 가격, "
        "현재 재고와 전체 재고금액을 알려줘"
    ),

    height=150
)


# ============================================================
# 10. AI Agent 실행 버튼
# ============================================================

run_button = st.button(

    "AI Agent 실행",

    type="primary",

    use_container_width=True
)


# ============================================================
# 11. Agent 실행
# ============================================================

if run_button:

    prompt = user_prompt.strip()


    # --------------------------------------------------------
    # 질문 없음
    # --------------------------------------------------------

    if not prompt:

        st.warning(
            "질문을 입력해 주세요."
        )


    # --------------------------------------------------------
    # 질문 있음
    # --------------------------------------------------------

    else:

        # 이전 답변 제거
        st.session_state.answer = ""

        # 현재 질문 저장
        st.session_state.last_question = prompt


        # ----------------------------------------------------
        # Agent 실행
        # ----------------------------------------------------

        with st.spinner(
            "Pet Store AI Agent가 요청을 처리하고 있습니다..."
        ):

            answer = run_pet_store_agent(
                prompt
            )


        # ----------------------------------------------------
        # 답변 저장
        # ----------------------------------------------------

        st.session_state.answer = answer


# ============================================================
# 12. AI 답변 출력
# ============================================================

if st.session_state.answer:

    st.divider()


    st.subheader("AI 답변")


    # --------------------------------------------------------
    # Markdown 사용
    #
    # 예:
    #
    # **상품명:** Doggy Delights
    # - 가격: $54.99
    # - 현재 재고: 20개
    #
    # 등을 보기 좋게 출력합니다.
    # --------------------------------------------------------

    st.markdown(
        st.session_state.answer
    )


# ============================================================
# 13. 실행 질문 확인
# ============================================================

if (
    st.session_state.last_question
    and st.session_state.answer
):

    with st.expander(
        "실행한 질문 보기",
        expanded=False
    ):

        st.write(
            st.session_state.last_question
        )


# ============================================================
# 14. 현재 연결 정보
# ============================================================

with st.expander(
    "현재 연결 정보",
    expanded=False
):

    st.markdown(
        """
        **AWS Region**

        `ap-northeast-2`

        **AI Model**

        `Amazon Nova Pro`

        **Product Knowledge Base**

        `H6IWBKNDPD`

        **Pet Care Knowledge Base**

        `ZW3BDOIVGS`

        **Inventory Lambda**

        `PetStoreInventoryManagementFunction`

        **User Lambda**

        `PetStoreUserManagementFunction`
        """
    )


# ============================================================
# 15. 하단 설명
# ============================================================

st.divider()


st.caption(
    "Pet Store AI Agent | "
    "Amazon Bedrock Nova Pro + "
    "Knowledge Bases + AWS Lambda"
)