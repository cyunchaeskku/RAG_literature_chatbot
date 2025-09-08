# LangGraph 기반의 다기능 RAG 챗봇

## 📖 프로젝트 개요

이 프로젝트는 여러 소설 텍스트를 데이터베이스에 저장하고, LangGraph를 사용하여 지능적인 RAG(Retrieval-Augmented Generation) 파이프라인을 구축한 대화형 챗봇입니다. 사용자는 Streamlit으로 구현된 웹 인터페이스를 통해 특정 소설의 내용에 대해 질문하거나 일반적인 대화를 나눌 수 있습니다.

---

## ✨ 주요 기능

- **데이터베이스 연동**: 소설 원문을 파일 시스템이 아닌 SQLite 데이터베이스에 저장하여 체계적으로 관리합니다.
- **다중 문서 선택**: 사용자가 UI에서 검색하고 싶은 여러 소설을 동시에 선택할 수 있습니다.
- **지능형 워크플로우 (LangGraph)**:
    - **질문 번역**: 한국어 질문을 영어로 자동 번역하여 내부 처리에 사용합니다.
    - **질문 라우팅**: 사용자의 질문이 소설 내용과 관련 있는지, 아니면 일반 대화인지 스스로 판단하여 처리 흐름을 분기합니다.
    - **품질 기반 재시도**: 벡터 저장소에서 검색한 문서의 품질이 낮다고 판단되면, 최대 2회까지 검색을 재시도하는 루프를 수행합니다.
    - **최종 답변 번역**: 내부적으로 영어로 생성된 답변을 사용자의 원본 질문 언어(한국어)로 다시 번역하여 제공합니다.
- **신뢰성 있는 답변**:
    - **출처 표시**: 챗봇 답변의 근거가 된 원문(출처)을 UI 우측에 함께 표시합니다.
    - **키워드 하이라이팅**: LLM이 답변 생성에 직접 사용했다고 명시한 키워드를 출처 본문에 노란색 형광펜으로 강조하여 신뢰도를 높입니다.
- **어드민 페이지**: Streamlit의 Multi-page 기능을 활용하여 현재 활성화된 LangGraph의 전체 워크플로우를 Mermaid 다이어그램으로 시각화하여 보여줍니다.

---

## 📂 프로젝트 구조

```
.
├── 📄 .env              # API 키 등 환경 변수 설정 파일
├── 📄 .gitignore        # Git 버전 관리 제외 목록
├── 📄 README.md         # 프로젝트 설명서
├── 📄 app.py            # 메인 Streamlit 애플리케이션
├── 📂 data/
│   └── 📄 literature.db # 소설 원문이 저장되는 SQLite DB
├── 📂 pages/
│   └── 📄 1_Admin_View.py # LangGraph 시각화를 위한 어드민 페이지
├── 📄 requirements.txt  # Python 의존성 패키지 목록
├── 📂 scripts/
│   ├── 📄 download_nltk_data.py # NLTK 데이터 다운로드 스크립트
│   └── 📄 setup_database.py     # DB 테이블 생성 및 데이터 삽입 스크립트
└── 📂 utils/
    ├── 📄 db_utils.py             # 데이터베이스 연결 및 쿼리 유틸리티
    ├── 📄 google_search_utils.py  # (현재 비활성화됨) Google 웹 검색 유틸리티
    ├── 📄 graph_utils.py          # LangGraph 워크플로우(노드, 엣지) 정의
    ├── 📄 highlight_utils.py      # 출처 텍스트 하이라이팅 유틸리티
    └── 📄 load_and_split_text_utils.py # LangChain 문서 분할 유틸리티
```

### 디렉토리 및 파일 상세 설명

-   **`app.py`**: Streamlit UI를 렌더링하고 사용자 입력을 처리하는 메인 파일입니다. `st.session_state`를 통해 상태를 관리하고, `graph_utils.py`에 정의된 LangGraph 앱을 호출하여 챗봇 로직을 실행합니다.
-   **`pages/1_Admin_View.py`**: Streamlit의 Multi-page 기능으로 구현된 어드민 페이지입니다. 메인 앱의 세션에 저장된 LangGraph 객체의 구조를 가져와 Mermaid 차트로 시각화합니다.
-   **`data/literature.db`**: `setup_database.py` 스크립트에 의해 생성되며, `literature` 테이블에 소설의 제목, 저자, 본문, 언어 등의 정보를 저장합니다.
-   **`scripts/`**: 일회성 실행이 필요한 스크립트를 모아놓은 디렉토리입니다.
    -   `setup_database.py`: `data` 폴더의 `.txt` 파일을 읽어 `literature.db`를 생성하고 데이터를 삽입합니다.
    -   `download_nltk_data.py`: `highlight_utils.py`에서 사용할 NLTK의 `stopwords`와 `punkt` 데이터를 프로젝트 내부에 다운로드합니다.
-   **`utils/`**: 재사용 가능한 로직을 모듈화한 디렉토리입니다.
    -   `graph_utils.py`: **프로젝트의 핵심 로직**이 담긴 파일입니다. LangGraph를 사용하여 질문 번역, 라우팅, 검색, 평가, 생성, 답변 번역에 이르는 전체 RAG 워크플로우를 상태 그래프(StateGraph)로 정의합니다.
    -   `db_utils.py`: SQLite DB와의 연결 및 데이터 CRUD(생성, 읽기, 수정, 삭제)를 담당하는 함수들을 포함합니다.
    -   `highlight_utils.py`: LLM이 반환한 키워드를 기반으로 원본 텍스트에 `<mark>` 태그를 추가하는 하이라이팅 기능을 제공합니다.
    -   `load_and_split_text_utils.py`: LangChain의 `TextSplitter`를 사용하여 긴 소설 본문을 검색에 용이한 작은 조각(chunk)으로 분할합니다.
    -   `vector_store_utils.py`: 텍스트 조각을 임베딩하고 FAISS 벡터 저장소를 생성하거나 로컬에서 불러오는 기능을 담당합니다.

---

## ⚙️ 아키텍처 및 워크플로우

본 챗봇은 LangGraph를 기반으로 한 상태 머신(State Machine)으로 동작합니다. 각 단계는 '노드'로 정의되며, 특정 조건에 따라 '엣지'를 통해 다음 노드로 이동합니다.

![Workflow Diagram](https://i.imgur.com/your-diagram-image.png)  <!-- 이 부분은 실제 이미지 링크로 대체해야 합니다. -->

### LangGraph 워크플로우 상세

1.  **`translate_question` (노드)**: 사용자 질문의 언어를 감지합니다.
    -   한국어일 경우: 영어로 번역 후 `original_language`를 'ko'로 기록하고 다음 노드로 전달합니다.
    -   영어일 경우: 원문 그대로 `original_language`를 'en'으로 기록하고 다음 노드로 전달합니다.
2.  **`route_question` (노드)**: 번역된 영어 질문을 LLM으로 분석하여 'novel_related'(소설 관련) 또는 'general'(일반 대화)로 분류합니다.
3.  **(조건부 엣지)**:
    -   'general' -> `generate` 노드로 바로 이동합니다.
    -   'novel_related' -> `retrieve` 노드로 이동합니다.
4.  **`retrieve` (노드)**: FAISS 벡터 저장소에서 질문과 관련된 문서 조각을 검색합니다.
5.  **`grade_documents` (노드)**: 검색된 각 문서가 질문과 정말 관련이 있는지 LLM으로 평가하여 관련 없는 문서를 필터링합니다.
6.  **(조건부 엣지)**:
    -   **성공 (`success`)**: 남은 문서가 있으면 `generate` 노드로 이동합니다.
    -   **재시도 (`retry`)**: 남은 문서가 없고, 재시도 횟수(최대 2회)가 남았으면 `retrieve` 노드로 돌아가 다시 검색합니다.
    -   **실패 (`failure`)**: 재시도 횟수를 초과하면 `generate` 노드로 이동하여 실패 메시지를 생성합니다.
7.  **`generate` (노드)**:
    -   **소설 관련**: 필터링된 문서를 바탕으로 **영어** 답변과 하이라이팅에 사용할 **영어 키워드**를 JSON 형식으로 생성합니다.
    -   **일반 대화**: 일반 대화용 프롬프트를 사용하여 **영어**로 답변을 생성합니다.
8.  **`translate_generation` (노드)**:
    -   `original_language`가 'ko'이면, 생성된 영어 답변을 한국어로 번역합니다.
    -   'en'이면 그대로 둡니다.
9.  **`END`**: 최종 답변을 사용자에게 반환합니다.

---

## 🚀 시작하기

### 1. 환경 설정

```bash
# 1. 프로젝트 클론
git clone https://github.com/your-username/rag_chatbot_practice.git
cd rag_chatbot_practice

# 2. 가상 환경 생성 및 활성화
python3 -m venv .venv
source .venv/bin/activate

# 3. 의존성 패키지 설치
pip install -r requirements.txt

# 4. .env 파일 설정
# .env.example 파일을 복사하여 .env 파일을 생성합니다.
# (이 프로젝트에서는 .env 파일을 직접 생성합니다)
# 아래 내용을 .env 파일에 작성하고 YOUR_API_KEY 부분을 실제 키로 교체하세요.
# OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
# GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY" # (현재 비활성화됨)
# GOOGLE_CSE_ID="YOUR_GOOGLE_CSE_ID"   # (현재 비활성화됨)

# 5. 데이터베이스 설정
# data 폴더의 txt 파일을 읽어 literature.db를 생성합니다.
python3 scripts/setup_database.py

# 6. NLTK 데이터 다운로드
# 하이라이팅 기능에 필요한 nltk 데이터를 로컬에 다운로드합니다.
python3 scripts/download_nltk_data.py
```

### 2. 애플리케이션 실행

```bash
streamlit run app.py
```

이제 브라우저에서 Streamlit 앱이 실행됩니다. 좌측 사이드바를 통해 메인 챗봇 페이지와 어드민 그래프 뷰 페이지를 오갈 수 있습니다. 다.