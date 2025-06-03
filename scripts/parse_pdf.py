import os
from scripts.parse_pdf_core import parse_pdf_in_batches

DATA_DIR = "./data"
OUTPUTS_DIR = "./outputs"
os.makedirs(OUTPUTS_DIR, exist_ok=True)

PDF_FILE = os.path.join(DATA_DIR, "2026연세수시.pdf")
OUTPUT_FILE = os.path.join(OUTPUTS_DIR, "2026연세수시_parsed.md")

# PDF 전처리 실행
docs = parse_pdf_in_batches(
    PDF_FILE,
    pages_per_batch=5,
    table_size_threshold=100   # 필요에 따라 조정
)

# 결과 저장
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(docs[0].page_content)

print(f"파싱 결과가 {OUTPUT_FILE}에 저장되었습니다.")
