import json
from langchain.schema import Document
from unstructured.partition.pdf import partition_pdf
from PyPDF2 import PdfReader
from tabulate import tabulate
import re

def extract_toc_lines(pdf_path, max_search_pages=5):
    reader = PdfReader(pdf_path)
    toc_lines = []
    for i in range(min(max_search_pages, len(reader.pages))):
        text = reader.pages[i].extract_text()
        if text and ("목차" in text or "CONTENTS" in text.upper()):
            for line in text.split('\n'):
                if "..." in line or "·" in line:
                    toc_lines.append(line.strip())
    return toc_lines

def parse_toc_lines(toc_lines):
    toc = []
    for line in toc_lines:
        m = None
        # ...8 또는 ········8
        m = re.match(r"(.+?)[\.\·]+ ?(\d+)$", line)
        if m:
            toc.append((m.group(1).strip(), int(m.group(2))))
    return toc

def find_real_pdf_page(pdf_path, keyword, approx_page):
    reader = PdfReader(pdf_path)
    for idx, page in enumerate(reader.pages):
        text = page.extract_text()
        if not text:
            continue
        if keyword[:6] in text:  # 일부만 매칭
            return idx
    # fallback: approx_page가 실제 PDF 상에서 어디쯤인지 직접 지정할 수 있도록
    return approx_page - 1

def chunk_pdf(pdf_path, toc_mapping):
    docs = []
    reader = PdfReader(pdf_path)
    toc_items = list(toc_mapping.items())
    for idx, (title, start_idx) in enumerate(toc_items):
        if idx+1 < len(toc_items):
            end_idx = toc_items[idx+1][1]
        else:
            end_idx = len(reader.pages)
        page_numbers = list(range(start_idx+1, end_idx+1))
        elements = partition_pdf(
            filename=pdf_path,
            strategy="hi_res",
            infer_table_structure=True,
            page_numbers=page_numbers
        )
        chunk_text = ""
        for e in elements:
            if e.category == "Table":
                table_text = e.text.strip()
                rows = [r.strip().split() for r in table_text.strip().split("\n") if r.strip()]
                if rows:
                    markdown_table = tabulate(rows, headers="firstrow", tablefmt="github")
                    chunk_text += f"\n\n{markdown_table}\n\n"
            else:
                chunk_text += f"\n\n{e.text.strip()}\n\n"
        metadata = {
            "main_title": title,
            "page": start_idx + 1,
            "source": pdf_path
        }
        doc = Document(page_content=chunk_text, metadata=metadata)
        docs.append(doc)
    return docs

def export_docs_jsonl(docs, filename):
    with open(filename, "w", encoding="utf-8") as f:
        for doc in docs:
            obj = {
                "page_content": doc.page_content,
                "metadata": doc.metadata
            }
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
    print(f"[INFO] {len(docs)}개 청크가 {filename} 파일로 저장됨.")

def main(pdf_path):
    toc_lines = extract_toc_lines(pdf_path)
    toc_list = parse_toc_lines(toc_lines)
    print(f"목차 추출: {toc_list}")
    toc_mapping = {}
    for title, logical_page in toc_list:
        real_idx = find_real_pdf_page(pdf_path, title, logical_page)
        toc_mapping[title] = real_idx
    docs = chunk_pdf(pdf_path, toc_mapping)
    export_docs_jsonl(docs, pdf_path + "_chunks.jsonl")

if __name__ == "__main__":
    main("2026학년도연세대학교수시모집요강.PDF")
