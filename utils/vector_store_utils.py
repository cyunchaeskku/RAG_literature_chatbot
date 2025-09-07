"""
벡터 저장소(Vector Store) 관련 유틸리티 함수를 모아놓은 파일입니다.

분할된 텍스트 조각(chunk)들을 임베딩하여 벡터로 변환하고,
이를 FAISS 벡터 저장소에 저장하거나 이미 저장된 인덱스를 불러오는
기능을 수행합니다.
"""
from pathlib import Path
from langchain_community.vectorstores import FAISS

def get_or_create_vector_store(chunks, path: Path, embeddings):
    """
    Checks if a vector store exists at the given path for the given embeddings.
    If it exists, loads it. Otherwise, creates a new one and saves it.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path_str = str(path)

    if path.exists():
        print(f"Loading existing vector store from {path_str}...")
        vector_store = FAISS.load_local(
            path_str, 
            embeddings, 
            allow_dangerous_deserialization=True
        )
        print("Vector store loaded successfully.")
    else:
        print(f"Creating new vector store and saving to {path_str}...")
        vector_store = FAISS.from_documents(chunks, embedding=embeddings)
        vector_store.save_local(path_str)
        print("Vector store created and saved successfully.")
    
    return vector_store
