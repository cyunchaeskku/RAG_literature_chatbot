"""
텍스트 하이라이팅 관련 유틸리티 함수를 모아놓은 파일입니다.

주어진 텍스트에서 키워드 목록에 해당하는 단어들을 찾아
HTML <mark> 태그로 감싸는 기능을 수행합니다.
"""
import re

def highlight_text(text: str, keywords: list[str]) -> str:
    """
    주어진 텍스트에서 키워드 목록에 해당하는 단어들을 <mark> 태그로 감쌉니다.
    대소문자를 구분하지 않고, 단어 전체가 일치하는 경우에만 하이라이트합니다.
    """
    if not keywords:
        return text

    # 키워드들을 OR(|)로 묶어 하나의 정규표현식 패턴 생성
    # \b는 단어 경계를 의미하여 'his'가 'this'의 일부로 매칭되는 것을 방지
    pattern = r"\b(" + "|".join(re.escape(key) for key in keywords) + r")\b"
    
    # re.sub의 repl 인자로 함수를 사용하여 원본의 대소문자를 유지
    def mark_tag(match):
        return f"<mark>{match.group(0)}</mark>"

    highlighted_text = re.sub(pattern, mark_tag, text, flags=re.IGNORECASE)
    
    return highlighted_text