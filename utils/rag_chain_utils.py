"""
(사용 중단됨) RAG 체인(Chain)을 생성하고 관리하는 유틸리티 파일입니다.

이 파일은 LangChain Expression Language (LCEL)을 사용하여 기본적인 대화형 RAG 체인을
구성합니다. 현재 프로젝트에서는 더 복잡한 로직 처리가 가능한 LangGraph 기반의
'graph_utils.py'로 대체되었습니다. 기록을 위해 보존됩니다.
"""
from langchain_openai import ChatOpenAI
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

def create_conversational_rag_chain(vector_store):
    """
    주어진 Vector Store를 기반으로 대화형 RAG 체인을 생성합니다.

    Args:
        vector_store: 검색을 수행할 FAISS Vector Store 객체.

    Returns:
        Runnable: 실행 가능한 대화형 RAG 체인 객체.
    """
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
    retriever = vector_store.as_retriever()

    # 1. 질문 재구성(Query Rewriting)을 위한 프롬프트
    # 이 프롬프트는 후속 질문을 독립적인 질문으로 바꾸는 역할을 합니다.
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "Given a chat history and the latest user question "
             "which might reference context in the chat history, "
             "formulate a standalone question which can be understood "
             "without the chat history. Do NOT answer the question, "
             "just reformulate it if needed and otherwise return it as is."),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    
    # 2. 질문 재구성 체인 생성
    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_q_prompt
    )

    # 3. 최종 답변 생성을 위한 프롬프트
    # 검색된 문서(context)를 바탕으로 질문에 답변하도록 지시합니다.
    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are an assistant for question-answering tasks. "
             "Use the following pieces of retrieved context to answer the question. "
             "**Always answer in the same language as the provided context.** "
             "If you don't know the answer, just say that you don't know. "
             "Use three sentences maximum and keep the answer concise.\n\n"
             "{context}"),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )

    # 4. 검색된 문서를 답변 생성 체인으로 묶는 체인 생성
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    
    # 5. 위 두 체인을 결합하여 최종적인 대화형 RAG 체인 완성
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    return rag_chain
