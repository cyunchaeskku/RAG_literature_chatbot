"""
LangGraph를 사용하여 RAG 파이프라인을 그래프로 구성하고 실행하는 파일입니다.

입력 질문 번역, 질문 라우팅, 문서 검색, 품질 평가, 답변 생성, 최종 답변 번역의
과정을 체계적으로 관리하는 다국어 처리 RAG 워크플로우를 정의합니다.
"""
from typing import List, TypedDict
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser, PydanticOutputParser
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END

# --- 1. Graph State 정의 ---
class GraphState(TypedDict):
    question: str
    original_language: str
    question_type: str
    documents: List[Document]
    generation: str
    keywords: List[str]
    retries: int

# --- 2. Node 함수 정의 ---
def translate_question(state: GraphState):
    """입력된 질문의 언어를 감지하고, 한국어일 경우 영어로 번역하는 노드"""
    print("---노드: 질문 번역---")
    question = state["question"]
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    prompt = ChatPromptTemplate.from_template(
        """You are an expert language identifier and translator.
        Identify the language of the user's question (either 'ko' for Korean or 'en' for English).
        If the language is Korean, translate the question to English.
        If the language is English, return the original question.
        Return a JSON object with two keys: 'language' and 'translated_question'.
        Question: {question}"""
    )
    chain = prompt | llm | JsonOutputParser()
    result = chain.invoke({"question": question})
    print(f"원본 언어: [{result['language']}], 번역된 질문: [{result['translated_question']}]")
    return {"question": result['translated_question'], "original_language": result['language']}

def route_question(state: GraphState):
    """질문 라우팅 노드"""
    print("---노드: 질문 라우팅---")
    question = state["question"]
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    prompt = ChatPromptTemplate.from_template(
        """You are an expert at routing a user question.
        Use 'novel_related' for questions about a novel's content.
        Use 'general' for all other questions.
        Return a JSON with a single key 'question_type'.
        Question: {question}"""
    )
    chain = prompt | llm | JsonOutputParser()
    result = chain.invoke({"question": question})
    print(f"질문 유형: [{result['question_type']}]")
    return {"question_type": result['question_type'], "retries": 0}

def retrieve(state: GraphState, vector_store):
    """문서 검색 노드"""
    print(f"---노드: 문서 검색 (시도: {state.get('retries', 0) + 1})---")
    question = state["question"]
    retriever = vector_store.as_retriever()
    documents = retriever.invoke(question)
    return {"documents": documents}

def grade_documents(state: GraphState):
    """검색된 문서 품질 평가 노드"""
    print("---노드: 문서 품질 평가---")
    question = state["question"]
    documents = state["documents"]
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    prompt = ChatPromptTemplate.from_template(
        """You are a grader assessing relevance of a retrieved document to a user question.
        Give a binary score 'yes' or 'no'.
        Provide the binary score as a JSON with a single key 'score'.
        Document: {document}
        Question: {question}"""
    )
    chain = prompt | llm | JsonOutputParser()
    filtered_docs = [d for d in documents if chain.invoke({"question": question, "document": d.page_content}).get("score", "no").lower() == "yes"]
    if not filtered_docs:
        return {"documents": [], "retries": state.get('retries', 0) + 1}
    return {"documents": filtered_docs}

def generate(state: GraphState):
    """답변 생성 노드 (Pydantic Parser 사용)"""
    print("---노드: 답변 생성 (Pydantic Parser)---")
    question = state["question"]
    documents = state.get("documents", [])
    question_type = state["question_type"]
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # Pydantic 모델 정의
    class AnswerWithKeywords(BaseModel):
        answer: str = Field(description="The answer to the user's question.")
        keywords: List[str] = Field(description="Exact keywords from the context used for the answer.")

    if question_type == 'novel_related' and documents:
        parser = PydanticOutputParser(pydantic_object=AnswerWithKeywords)
        
        prompt_template = """You are an assistant for question-answering tasks.
            Use the following context to answer the question in English.
            You must follow the format instructions below.
            
            {format_instructions}

            Context: {context}
            Question: {question}"""
        
        prompt = ChatPromptTemplate.from_template(
            prompt_template,
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )
        
        chain = prompt | llm | parser
        
        try:
            result = chain.invoke({
                "context": "\n\n".join(doc.page_content for doc in documents),
                "question": question
            })
            generation = result.answer
            keywords = result.keywords
        except Exception as e:
            print(f"Pydantic 파싱 실패: {e}. 답변만 생성하도록 재시도합니다.")
            prompt_template_fallback = "Answer the following question in English based on the context.\nContext: {context}\nQuestion: {question}"
            chain_fallback = ChatPromptTemplate.from_template(prompt_template_fallback) | llm | StrOutputParser()
            generation = chain_fallback.invoke({"context": "\n\n".join(doc.page_content for doc in documents), "question": question})
            keywords = []

    else:
        if question_type == 'novel_related':
             generation = "I couldn't find relevant information in the novel."
        else:
            prompt_template = "You are a friendly chatbot named 'Novel Bot'. Answer the user's question in English.\nQuestion: {question}"
            chain = ChatPromptTemplate.from_template(prompt_template) | llm | StrOutputParser()
            generation = chain.invoke({"question": question})
        keywords = []

    return {"generation": generation, "keywords": keywords, "documents": documents}


def translate_generation(state: GraphState):
    """생성된 답변을 원본 언어로 번역하는 노드"""
    print("---노드: 최종 답변 번역---")
    generation = state["generation"]
    original_language = state["original_language"]

    if original_language == 'ko' and generation:
        print("답변을 한국어로 번역합니다.")
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        prompt = ChatPromptTemplate.from_template("Translate the following English text to Korean: {text}")
        chain = prompt | llm | StrOutputParser()
        translated_generation = chain.invoke({"text": generation})
        return {"generation": translated_generation}
    
    print("번역이 필요 없습니다.")
    return {"generation": generation}

# --- 3. Conditional Edge 로직 ---
def decide_route(state: GraphState):
    return state["question_type"]

def decide_after_grade(state: GraphState):
    if not state["documents"]:
        return "retry" if state.get('retries', 0) < 2 else "failure"
    return "success"

# --- 4. Graph 생성 함수 ---
def create_graph(vector_store):
    workflow = StateGraph(GraphState)

    workflow.add_node("translate_question", translate_question)
    workflow.add_node("route_question", route_question)
    workflow.add_node("retrieve", lambda state: retrieve(state, vector_store))
    workflow.add_node("grade_documents", grade_documents)
    workflow.add_node("generate", generate)
    workflow.add_node("translate_generation", translate_generation)

    workflow.set_entry_point("translate_question")
    workflow.add_edge("translate_question", "route_question")
    workflow.add_conditional_edges(
        "route_question",
        decide_route,
        {"novel_related": "retrieve", "general": "generate"},
    )
    workflow.add_edge("retrieve", "grade_documents")
    workflow.add_conditional_edges(
        "grade_documents",
        decide_after_grade,
        {"success": "generate", "retry": "retrieve", "failure": "generate"},
    )
    workflow.add_edge("generate", "translate_generation")
    workflow.add_edge("translate_generation", END)
    
    app = workflow.compile()
    print("LangGraph 앱이 성공적으로 컴파일되었습니다. (최종 번역 노드 포함)")
    return app