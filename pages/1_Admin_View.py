"""
LangGraph 워크플로우를 시각화하는 어드민 페이지입니다.

메인 앱('app.py')에서 사용자가 소설을 선택하고 벡터 저장소 준비를 완료하면
세션 상태(session_state)에 저장되는 LangGraph 객체를 가져와
Mermaid 다이어그램으로 렌더링하여 보여줍니다.
"""
import streamlit as st
from streamlit_mermaid import st_mermaid

st.set_page_config(page_title="Admin: Graph View", layout="wide")
st.title("📊 LangGraph 워크플로우 시각화")

# 세션 상태에서 LangGraph 앱 객체 가져오기
if 'rag_app' in st.session_state and st.session_state.rag_app:
    rag_app = st.session_state.rag_app
    
    st.info("아래는 현재 활성화된 RAG 워크플로우의 구조입니다.")
    
    try:
        # LangGraph 객체에서 Mermaid 다이어그램 코드 생성
        mermaid_code = rag_app.get_graph().draw_mermaid()
        
        # --- Mermaid 구문 오류 수정을 위한 패치 ---
        # 1. HTML 공백(&nbsp;)을 실제 공백으로 변경
        mermaid_code_fixed = mermaid_code.replace("&nbsp;", " ")
        # 2. 누락된 'generate' 엣지 레이블 추가
        mermaid_code_fixed = mermaid_code_fixed.replace(
            'grade_documents -.-> generate;',
            'grade_documents -. "generate" .-> generate;'
        )
        
        # st_mermaid 컴포넌트를 사용하여 수정된 다이어그램 렌더링
        st_mermaid(mermaid_code_fixed)
        
        with st.expander("수정된 Mermaid 코드 보기"):
            st.code(mermaid_code_fixed, language="mermaid")

    except Exception as e:
        st.error(f"그래프를 시각화하는 중 오류가 발생했습니다: {e}")

else:
    st.warning(
        "LangGraph 객체를 찾을 수 없습니다. "
        "먼저 메인 페이지('app.py')로 돌아가서 소설을 선택하고 '선택 완료' 버튼을 눌러주세요."
    )
