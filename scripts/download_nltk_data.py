"""
NLTK 데이터(stopwords, punkt)를 다운로드하기 위한 일회성 스크립트입니다.

이 스크립트는 프로젝트 루트의 'nltk_data' 폴더에 데이터를 다운로드하여,
프로젝트가 시스템에 설치된 NLTK 데이터에 의존하지 않도록 합니다.
'streamlit run'을 실행하기 전에 한 번 실행해야 합니다.
"""
import nltk
import ssl
from pathlib import Path

def download_data():
    # SSL 인증서 검증 문제 해결을 위한 임시 조치
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context

    # 프로젝트 루트에 'nltk_data' 폴더 경로 지정
    NLTK_DATA_PATH = Path(__file__).parent.parent / "nltk_data"
    NLTK_DATA_PATH.mkdir(exist_ok=True)
    
    print(f"NLTK 데이터를 다음 경로에 다운로드합니다: {NLTK_DATA_PATH}")
    
    # 데이터 다운로드
    try:
        nltk.download('stopwords', download_dir=str(NLTK_DATA_PATH))
        nltk.download('punkt', download_dir=str(NLTK_DATA_PATH))
        nltk.download('punkt_tab', download_dir=str(NLTK_DATA_PATH))
        print("\nNLTK 데이터 다운로드 완료.")
        print(f"이제 '{NLTK_DATA_PATH}' 폴더에서 데이터를 사용할 수 있습니다.")
    except Exception as e:
        print(f"\nNLTK 데이터 다운로드 중 오류 발생: {e}")
        print("인터넷 연결을 확인하거나, NLTK 서버에 일시적인 문제가 있을 수 있습니다.")

if __name__ == "__main__":
    download_data()

