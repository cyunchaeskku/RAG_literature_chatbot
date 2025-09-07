"""
RAG 챗봇을 위한 메인 Streamlit 애플리케이션 파일입니다.

이 파일은 사용자 인터페이스(UI), 상태 관리, 그리고 사용자의 소설 선택부터
챗봇의 답변 표시까지 전체 RAG 파이프라인을 제어하고 조율하는 역할을 합니다.
"""
import streamlit as st
from dotenv import load_dotenv
from pathlib import Path
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import OpenAIEmbeddings

from utils.db_utils import get_all_literatures, get_literature_details_by_titles
from utils.load_and_split_text_utils import split_documents
from utils.vector_store_utils import get_or_create_vector_store
from utils.rag_chain_utils import create_conversational_rag_chain
from utils.graph_utils import create_graph
from utils.highlight_utils import highlight_text

def main():
    load_dotenv()
    st.set_page_config(page_title="RAG Chatbot", page_icon="🤖", layout="wide")
    st.title("RAG 챗봇")

    CWD = Path.cwd()
    
    try:
        all_literatures = get_all_literatures()
        book_titles = [lit['title'] for lit in all_literatures]
    except Exception as e:
        st.error(f"데이터베이스 연결 실패: {e}")
        st.info("`scripts/setup_database.py`를 실행하여 DB를 설정하세요.")
        return

    st.subheader("검색할 소설을 선택하세요 (동일 언어만 가능):")
    
    selected_book_titles = st.multiselect("소설 선택", book_titles, label_visibility="collapsed")

    if st.button("선택 완료 및 벡터 저장소 준비"):
        if not selected_book_titles:
            st.warning("소설을 하나 이상 선택하세요!")
            st.session_state.clear()
        else:
            st.session_state.selected_book_titles = selected_book_titles
            st.rerun()

    st.divider()

    if 'selected_book_titles' in st.session_state and st.session_state.selected_book_titles:
        
        # --- 1. Data Preparation ---
        details = get_literature_details_by_titles(st.session_state.selected_book_titles)
        
        languages = {detail['language'] for detail in details}
        if len(languages) > 1:
            st.error("죄송합니다. 현재는 여러 언어의 책을 동시에 검색할 수 없습니다. 동일한 언어의 책만 선택해주세요.")
            st.stop()
        
        language = languages.pop()
        selected_names_display = ", ".join(st.session_state.selected_book_titles)

        with st.spinner("데이터베이스에서 본문을 로드하는 중..."):
            documents = [Document(page_content=d['body']) for d in details]
        
        with st.spinner("문서를 청크로 나누는 중..."):
            all_chunks = split_documents(documents)

        embedding_model_name = "text-embedding-3-small"
        if language == 'ko':
            st.info(f"한국어 임베딩 모델을 사용합니다: {embedding_model_name}")
            embeddings = OpenAIEmbeddings(model=embedding_model_name)
        else:
            st.info(f"영어(기본) 임베딩 모델을 사용합니다: {embedding_model_name}")
            embeddings = OpenAIEmbeddings(model=embedding_model_name)

        sanitized_model_name = embedding_model_name.replace("-", "_").replace("/", "_")
        sanitized_titles = [t.lower().replace(" ", "_") for t in sorted(st.session_state.selected_book_titles)]
        index_name_suffix = f"{language}_{sanitized_model_name}_{'_'.join(sanitized_titles)}"
        FAISS_INDEX_PATH = CWD / "faiss_literature" / index_name_suffix

        with st.spinner("벡터 저장소를 준비하는 중입니다..."):
            vector_store = get_or_create_vector_store(all_chunks, FAISS_INDEX_PATH, embeddings)
            st.success("벡터 저장소 준비가 완료되었습니다!")

        # --- 2. UI Layout and RAG Chain ---
        main_col, source_col = st.columns([2, 1])

        with main_col:
            st.header(f"'{selected_names_display}' (언어: {language.upper()})에 대해 질문해보세요")

            if 'rag_app' not in st.session_state:
                st.session_state.rag_app = create_graph(vector_store)

            if "messages" not in st.session_state:
                st.session_state.messages = []

            # 채팅 기록 표시
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            # 사용자 입력 처리
            if prompt := st.chat_input("질문을 입력해주세요."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    status_placeholder = st.empty()
                    answer_placeholder = st.empty()
                    
                    inputs = {"question": prompt}
                    final_state = {}
                    
                    for step in st.session_state.rag_app.stream(inputs):
                        node_name = list(step.keys())[0]
                        status_message = {
                            "translate_question": "질문 번역 중...",
                            "route_question": "질문 유형 분석 중...",
                            "retrieve": "소설 내용 검색 중...",
                            "grade_documents": "검색된 문서 평가 중...",
                            "generate": "답변 생성 중...",
                            "translate_generation": "답변 번역 중...",
                        }.get(node_name, "")
                        if status_message:
                            status_placeholder.info(status_message)
                        final_state.update(step)

                    status_placeholder.empty()
                    
                    answer = final_state.get("translate_generation", {}).get("generation", "죄송합니다, 답변을 생성하지 못했습니다.")
                    st.session_state.latest_sources = final_state.get("generate", {}).get("documents", [])
                    st.session_state.latest_keywords = final_state.get("generate", {}).get("keywords", [])
                    
                    answer_placeholder.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                    # Re-run to update the source column immediately
                    st.rerun()

        with source_col:
            st.subheader("참고 자료")
            
            if st.session_state.get("latest_keywords"):
                st.markdown("**주요 키워드:**")
                tags_html = "".join(f'<span style="background-color: #e0e0e0; border-radius: 5px; padding: 3px 8px; margin: 2px; display: inline-block;">{kw}</span>' for kw in st.session_state["latest_keywords"])
                st.markdown(tags_html, unsafe_allow_html=True)
                st.write("")

            if st.session_state.get("latest_sources"):
                keywords = st.session_state.get("latest_keywords", [])
                for i, doc in enumerate(st.session_state.latest_sources):
                    is_expanded = (i == 0)
                    with st.expander(f"출처 {i+1} {'(가장 관련 높음)' if i == 0 else ''}", expanded=is_expanded):
                        highlighted_content = highlight_text(doc.page_content, keywords)
                        st.markdown(highlighted_content, unsafe_allow_html=True)
            else:
                st.info("질문을 입력하면 관련 출처가 여기에 표시됩니다.")
    else:
        st.info("위에서 검색할 소설을 선택하고 '선택 완료' 버튼을 눌러주세요.")

if __name__ == '__main__':
    main()
