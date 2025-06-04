import os
import re
import json
from PyPDF2 import PdfReader
from unstructured.partition.pdf import partition_pdf
from tabulate import tabulate

# ===== 파일 경로(수정!) =====
PDF_PATH = "data/2026연세수시.PDF"
CHUNKS_PATH = "outputs/example_chunks_reviewed.jsonl"
TABLES_PATH = "outputs/example_tables.jsonl"

os.makedirs("outputs", exist_ok=True)

# ====== 1. 목차 페이지 사용자 지정 및 추출 ======
def get_toc_page(pdf_path):
    reader = PdfReader(pdf_path)
    while True:
        toc_page = input("목차가 있는 PDF 페이지 번호(1-base)를 입력하세요: ").strip()
        if not toc_page.isdigit():
            print("[경고] 숫자를 입력하세요.")
            continue
        toc_idx = int(toc_page) - 1
        text = reader.pages[toc_idx].extract_text()
        print(f"\n[확인] 입력한 페이지 첫 줄: {text.splitlines()[0] if text else '[텍스트 없음]'}")
        yn = input("이 페이지가 목차가 맞습니까? (y/n): ").strip().lower()
        if yn == "y":
            return toc_idx, text
        else:
            print("[알림] 다시 입력하세요.")

def parse_toc_lines(toc_text):
    toc_lines = []
    for line in toc_text.split('\n'):
        # ...10, ·······10 등 다양한 목차 패턴 허용
        if re.search(r'[\.\·]{2,}\s*\d+$', line):
            toc_lines.append(line.strip())
    return toc_lines

def get_section_mappings(pdf_path, toc_lines):
    reader = PdfReader(pdf_path)
    mappings = []
    for toc in toc_lines:
        m = re.match(r"(.+?)[\.\·]{2,}\s*(\d+)$", toc)
        if not m:
            continue
        section, logical_page = m.group(1).strip(), int(m.group(2))
        print(f"\n[STEP] '{section}' (목차상 {logical_page}쪽)")
        while True:
            page_input = input(f"이 단원이 실제 PDF상 어디에 있나요? (PDF 페이지 번호, 0=자동탐색): ").strip()
            if page_input == "0":
                # 실제 위치 자동탐색
                found = False
                for idx, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text and section[:6] in text:
                        print(f"[자동탐색] {idx+1}쪽: '{text.splitlines()[0]}'")
                        yn = input("이 페이지가 맞습니까? (y/n): ").strip().lower()
                        if yn == "y":
                            mappings.append((section, idx))
                            found = True
                            break
                if found:
                    break
                else:
                    print("[경고] 자동탐색 실패, 직접 입력해 주세요.")
            elif page_input.isdigit():
                idx = int(page_input) - 1
                text = reader.pages[idx].extract_text()
                print(f"[확인] {idx+1}쪽 첫 줄: '{text.splitlines()[0] if text else '[텍스트 없음]'}'")
                yn = input("이 페이지가 맞습니까? (y/n): ").strip().lower()
                if yn == "y":
                    mappings.append((section, idx))
                    break
            else:
                print("[경고] 잘못된 입력. 숫자 또는 0을 입력하세요.")
    return mappings

# ====== 2. 단원별 슬라이스, Element 추출 ======
def extract_elements(pdf_path, section_ranges):
    reader = PdfReader(pdf_path)
    elements_by_section = []
    for i, (title, start_idx) in enumerate(section_ranges):
        end_idx = section_ranges[i+1][1] if i+1 < len(section_ranges) else len(reader.pages)
        print(f"\n[슬라이스] '{title}': PDF {start_idx+1} ~ {end_idx}페이지")
        elements = partition_pdf(
            filename=pdf_path,
            strategy="hi_res",
            infer_table_structure=True,
            page_numbers=list(range(start_idx+1, end_idx+1))
        )
        elements_by_section.append((title, start_idx, elements))
    return elements_by_section

# ====== 3. 계층 추정 및 검수 ======
def guess_level(text, font_size=None):
    # 폰트 크기(추후 확장), 네모, 점, 번호 등
    if re.match(r"^(제?\d+장|[Ⅰ-Ⅹ]+\.?)", text):    # 대제목
        return "main_title"
    elif re.match(r"^\d+\.", text):                 # 중제목
        return "mid_title"
    elif re.match(r"^[가-힣]\.|^[A-Za-z]\.", text): # 소제목
        return "sub_title"
    elif re.match(r"^[■●▪]", text):                 # 네모/점 기호
        return "sub_title"
    else:
        return ""

def confirm_level(text, auto_level):
    print(f"\n[제목 후보] '{text.strip()}' (자동추정: {auto_level or '없음'})")
    level = input("main/mid/sub/없음 중 하나를 입력 (엔터=자동추정): ").strip()
    if level in ["main", "mid", "sub"]:
        return {"main": "main_title", "mid": "mid_title", "sub": "sub_title"}[level]
    elif level == "없음":
        return ""
    else:
        return auto_level

# ====== 4. 표 처리 (크기 기준 DB로 분리/치환) ======
def handle_table(e, section_title, pdf_name, table_count, table_db, page_num):
    table_text = e.text.strip()
    row_count = table_text.count("\n") + 1
    table_id = f"{pdf_name}_table_{table_count:04d}"
    threshold = 30   # 예: 30행 초과시 분리
    if row_count > threshold:
        print(f"\n[표 DB] [표-{table_id}]이 너무 큽니다. 'db를 확인하세요'로 본문에 치환합니다.")
        print(f"   - 위치: '{section_title}', PDF {page_num+1}페이지")
        print(f"   - 표 행 수: {row_count}")
        msg = f"[표-{table_id}] db를 확인하세요."
        table_db.append({"table_id": table_id, "text": table_text, "section": section_title, "page": page_num+1})
        return msg, table_id
    else:
        rows = [r.strip().split() for r in table_text.split("\n") if r.strip()]
        if rows:
            markdown_table = tabulate(rows, headers="firstrow", tablefmt="github")
            table_db.append({"table_id": table_id, "markdown": markdown_table, "section": section_title, "page": page_num+1})
            return f"\n\n{markdown_table}\n\n", table_id
        else:
            return "[표-오류]", table_id

# ====== 5. Document(청크) 생성 ======
def build_chunks(elements_by_section, pdf_name):
    chunks = []
    tables = []
    table_count = 0
    for section_title, start_idx, elements in elements_by_section:
        cur_main, cur_mid, cur_sub = section_title, "", ""
        chunk_text = ""
        table_ids = []
        for e in elements:
            if not hasattr(e, "text"):
                continue
            txt = e.text.strip()
            # 계층 추정 및 검수
            level = guess_level(txt)
            level = confirm_level(txt, level)
            if level == "main_title":
                cur_main, cur_mid, cur_sub = txt, "", ""
            elif level == "mid_title":
                cur_mid, cur_sub = txt, ""
            elif level == "sub_title":
                cur_sub = txt
            elif e.category == "Table":
                table_count += 1
                tbl_txt, table_id = handle_table(e, section_title, pdf_name, table_count, tables, start_idx)
                chunk_text += f"\n\n{tbl_txt}\n\n"
                table_ids.append(table_id)
            else:
                chunk_text += f"\n\n{txt}\n\n"
        # 모든 청크에 계층정보 포함(필수)
        meta = {
            "main_title": cur_main or section_title,
            "mid_title": cur_mid,
            "sub_title": cur_sub,
            "page": start_idx + 1,
            "source": pdf_name,
            "table_id": table_ids
        }
        chunks.append({"page_content": chunk_text.strip(), "metadata": meta})
        print(f"[청크생성] {meta}")
    return chunks, tables

# ====== 6. 저장 ======
def save_jsonl(data, path, what=""):
    with open(path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"[저장] {what} {len(data)}개 → {path}")
    
def test():
    print("ㅋㅋㅋ")

# ====== MAIN ======
def start():
    print("프로그램이 시작되었습니다.", flush=True)
    try:
        reader = PdfReader(PDF_PATH)
        print(f"페이지 수: {len(reader.pages)}", flush=True)
    except Exception as e:
        print(f"PDF 에러: {e}")
    print(f"========== PDF 전처리 파이프라인 시작 ==========\nPDF: {PDF_PATH}\n")
    toc_idx, toc_text = get_toc_page(PDF_PATH)
    toc_lines = parse_toc_lines(toc_text)
    print(f"[목차 추출] {len(toc_lines)}개 단원")
    section_ranges = get_section_mappings(PDF_PATH, toc_lines)
    elements_by_section = extract_elements(PDF_PATH, section_ranges)
    pdf_name = os.path.splitext(os.path.basename(PDF_PATH))[0]
    chunks, tables = build_chunks(elements_by_section, pdf_name)
    save_jsonl(chunks, CHUNKS_PATH, "청크")
    save_jsonl(tables, TABLES_PATH, "표")
    print("\n========== 완료 ==========")