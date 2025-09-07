"""
LangChain의 Google Search API Wrapper를 사용하는 웹 검색 도구입니다.

이 도구를 사용하려면 .env 파일에 GOOGLE_API_KEY와 GOOGLE_CSE_ID가
올바르게 설정되어 있어야 합니다.
"""
from langchain_community.utilities import GoogleSearchAPIWrapper
from langchain_core.documents import Document

def run_google_search(query: str, num_results: int = 5) -> list[Document]:
    """
    Google 검색을 수행하고 결과를 LangChain Document 객체 리스트로 반환합니다.
    """
    try:
        search_wrapper = GoogleSearchAPIWrapper()
        results = search_wrapper.results(query, num_results=num_results)
        
        # 검색 결과를 Document 객체 형식으로 변환
        documents = []
        for res in results:
            doc = Document(
                page_content=res.get("snippet", "No snippet available."),
                metadata={
                    "title": res.get("title", "No title available."),
                    "source": res.get("link", "No link available.")
                }
            )
            documents.append(doc)
        return documents

    except Exception as e:
        print(f"Google 검색 중 오류가 발생했습니다: {e}")
        # 오류 발생 시 사용자에게 보여줄 메시지를 담은 Document 반환
        error_doc = Document(
            page_content=f"웹 검색에 실패했습니다. API 키가 올바른지 확인해주세요. (오류: {e})",
            metadata={"title": "Search Error", "source": ""}
        )
        return [error_doc]
