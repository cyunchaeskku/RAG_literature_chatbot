"""
SQLite 데이터베이스('literature.db')를 설정하기 위한 일회성 스크립트입니다.

이 스크립트는 'literature' 테이블을 생성하고, 'data' 디렉토리에 있는
.txt 파일의 내용으로 테이블을 채웁니다. 이 스크립트는 한 번만 실행하거나,
'data' 폴더에 새로운 책을 추가했을 때 실행하도록 설계되었습니다.
"""
import sqlite3
from pathlib import Path

def ensure_literature_table(conn: sqlite3.Connection):
    """
    Ensures the 'literature' table and its unique index exist.
    Adds the 'language' column if it doesn't exist.
    """
    cursor = conn.cursor()
    
    # Create the table if it doesn't exist
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS literature (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT,
        publish_year INTEGER,
        body TEXT NOT NULL,
        language TEXT NOT NULL DEFAULT 'en'
    )
    """
    cursor.execute(create_table_sql)
    print("Table 'literature' ensured.")

    # Add 'language' column if it doesn't exist (for backward compatibility)
    try:
        cursor.execute("ALTER TABLE literature ADD COLUMN language TEXT NOT NULL DEFAULT 'en'")
        print("Column 'language' added to the table.")
    except sqlite3.OperationalError:
        # This error occurs if the column already exists, which is fine.
        print("Column 'language' already exists.")

    # Create a unique index on the 'title' column
    create_index_sql = "CREATE UNIQUE INDEX IF NOT EXISTS idx_literature_title ON literature(title)"
    cursor.execute(create_index_sql)
    print("Unique index on 'title' ensured.")
    
    conn.commit()

def setup_database():
    """
    Connects to the database, ensures table structure, and populates it with
    literature from .txt files in the data directory.
    """
    # Define paths
    CWD = Path(__file__).parent.parent
    DB_PATH = CWD / "data" / "literature.db"
    DATA_PATH = CWD / "data"

    try:
        # Ensure the parent directory for the database exists
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(DB_PATH) as conn:
            print(f"Successfully connected to the database at {DB_PATH}")
            ensure_literature_table(conn)
            cursor = conn.cursor()

            txt_files = list(DATA_PATH.glob("*.txt"))
            if not txt_files:
                print(f"No .txt files found in {DATA_PATH}.")
                return

            print(f"Found {len(txt_files)} .txt file(s) to process.")

            for book_path in txt_files:
                try:
                    book_title = book_path.stem.replace("_", " ").title()
                    
                    # Default metadata
                    author, publish_year, language = "Unknown", None, "en"

                    if book_path.stem == "iliad":
                        author, publish_year = "Homer", -800
                    # Example for a Korean book if you add one later
                    # elif book_path.stem == "some_korean_book":
                    #     author, language = "Some Author", "ko"

                    print(f"Processing '{book_title}'...")
                    
                    with open(book_path, 'r', encoding='utf-8') as f:
                        book_body = f.read()
                    
                    cursor.execute("""
                    INSERT INTO literature (title, author, publish_year, body, language)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(title) DO UPDATE SET
                        author=excluded.author,
                        publish_year=excluded.publish_year,
                        body=excluded.body,
                        language=excluded.language
                    """, (book_title, author, publish_year, book_body, language))
                    
                    if cursor.rowcount > 0:
                        print(f" -> Successfully inserted or updated '{book_title}'.")
                    else:
                        print(f" -> No changes for '{book_title}'.")

                except Exception as e:
                    print(f"Error processing {book_path}: {e}")

        print(f"\nDatabase setup complete.")

    except sqlite3.Error as e:
        print(f"A database error occurred: {e}")

if __name__ == "__main__":
    setup_database()
