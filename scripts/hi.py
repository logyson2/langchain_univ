from PyPDF2 import PdfReader

PDF_PATH = "data/2026연세수시.PDF"  # 실제 파일명으로 맞추세요!

print("PDF 테스트 시작")
try:
    reader = PdfReader(PDF_PATH)
    print(f"페이지 수: {len(reader.pages)}")
    for i, page in enumerate(reader.pages[:3]):
        text = page.extract_text()
        print(f"{i+1}쪽 일부: {text[:40] if text else '[없음]'}")
except Exception as e:
    print("PDF 열기 에러:", e)
print("테스트 종료")
