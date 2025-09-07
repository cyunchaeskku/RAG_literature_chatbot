"""
텍스트 문서(본문)를 로드하고 분할하는 유틸리티 함수를 모아놓은 파일입니다.

LangChain의 Document Loader와 Text Splitter를 사용하여 긴 텍스트를
RAG 모델이 처리하기 용이한 작은 조각(chunk)으로 만드는 기능을 수행합니다.
"""
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

def load_document(file_path):
    """Loads a text document from a given file path."""
    loader = TextLoader(file_path)
    documents = loader.load()
    return documents

def split_documents(documents):
    """Splits documents into smaller chunks for processing."""
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)
    return chunks
