import streamlit as st
import json

st.set_page_config(layout="wide")

def load_chunks(jsonl_path):
    chunks = []
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            chunks.append(obj)
    return chunks

default_jsonl_name = "2026연세수시_chunks.jsonl"
jsonl_path = st.sidebar.text_input("청크 JSONL 파일 경로", value=f"outputs/{default_jsonl_name}")

# 중앙 구분선 CSS (vh/px 등으로 확실하게)
st.markdown("""
    <style>
    .vline {
        border-left: 3px solid #ffffffcc;
        height: 88vh;
        margin: 0 auto;
        display: block;
        opacity: 0.9;
    }
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100vw !important;
    }
    textarea {
        font-size: 16px !important;
        font-family: "Fira Mono", monospace !important;
    }
    </style>
""", unsafe_allow_html=True)

if st.sidebar.button("파일 불러오기"):
    chunks = load_chunks(jsonl_path)
    st.session_state['chunks'] = chunks
    st.session_state['idx'] = 0
    st.session_state['md_buffer'] = chunks[0]["page_content"] if chunks else ""

if 'chunks' in st.session_state and st.session_state['chunks']:
    idx = st.session_state.get('idx', 0)
    chunks = st.session_state['chunks']
    chunk = chunks[idx]
    meta = chunk.get("metadata", {})
    meta_txt = '\n'.join([f"{k}: {v}" for k, v in meta.items()])

    # buffer for edit
    if "md_buffer" not in st.session_state:
        st.session_state['md_buffer'] = chunk["page_content"]

    col1, col_mid, col2 = st.columns([1,0.025,1], gap="small")
    with col1:
        st.markdown("### [원본/수정용 Markdown]")
        md_new = st.text_area(
            "Markdown 내용 (수정 가능)",
            value=st.session_state['md_buffer'],
            height=760,
            key=f"md_{idx}"
        )
        st.markdown("**[Metadata 정보]**")
        st.text(meta_txt)
        # 저장 버튼
        if st.button("수정 내용 저장"):
            st.session_state['chunks'][idx]["page_content"] = md_new
            st.session_state['md_buffer'] = md_new
            st.success("저장되었습니다!")
    with col_mid:
        st.markdown('<div class="vline"></div>', unsafe_allow_html=True)
    with col2:
        st.markdown("### [Markdown 렌더링 미리보기]")
        st.markdown(st.session_state['chunks'][idx]["page_content"], unsafe_allow_html=True)

    # 네비게이션
    nav1, nav2, nav3 = st.columns([1, 3, 1])
    with nav1:
        if st.button("이전"):
            new_idx = max(0, idx-1)
            st.session_state['idx'] = new_idx
            st.session_state['md_buffer'] = st.session_state['chunks'][new_idx]["page_content"]
    with nav2:
        st.markdown(f"**{idx+1} / {len(chunks)}**")
    with nav3:
        if st.button("다음"):
            new_idx = min(len(chunks)-1, idx+1)
            st.session_state['idx'] = new_idx
            st.session_state['md_buffer'] = st.session_state['chunks'][new_idx]["page_content"]

    if st.button("전체 결과 저장", type="primary"):
        save_path = st.text_input("저장 경로", jsonl_path.replace(".jsonl", "_reviewed.jsonl"))
        if save_path:
            with open(save_path, "w", encoding="utf-8") as f:
                for obj in st.session_state['chunks']:
                    f.write(json.dumps(obj, ensure_ascii=False) + "\n")
            st.success(f"검수본이 '{save_path}'로 저장되었습니다.")

else:
    st.info("좌측 메뉴에서 파일을 불러와 주세요.")
