from unstructured.partition.pdf import partition_pdf
from langchain.schema import Document
from tabulate import tabulate

def parse_pdf_in_batches(pdf_path: str, pages_per_batch: int = 5, table_size_threshold: int = 100):
    """
    PDF를 pages_per_batch 단위로 나누어 처리.
    큰 표는 [표 제목: ...][표-n]로 대체, 작은 표는 Markdown.
    최종적으로 LangChain Document 객체 반환.
    """
    from PyPDF2 import PdfReader
    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)

    final_text = ""
    table_count = 0

    for start_page in range(1, total_pages + 1, pages_per_batch):
        end_page = min(start_page + pages_per_batch - 1, total_pages)
        page_numbers = list(range(start_page, end_page + 1))
        print(f"Processing pages {page_numbers}...")

        elements = partition_pdf(
            filename=pdf_path,
            strategy="hi_res",
            infer_table_structure=True,
            page_numbers=page_numbers
        )

        for e in elements:
            if e.category == "Table":
                table_count += 1
                table_text = e.text.strip()
                row_count = table_text.count("\n")
                if row_count > table_size_threshold:
                    final_text += f"\n\n[표 제목: 표 {table_count} (크기: {row_count}행)]\n[표-{table_count}]\n\n"
                else:
                    rows = [r.strip().split() for r in table_text.strip().split("\n") if r.strip()]
                    if rows:
                        markdown_table = tabulate(rows, headers="firstrow", tablefmt="github")
                        final_text += f"\n\n{markdown_table}\n\n"
            else:
                final_text += f"\n\n{e.text.strip()}\n\n"

    document = Document(page_content=final_text, metadata={"source": pdf_path})
    return [document]
