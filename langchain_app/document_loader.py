from langchain.schema import Document

def load_parsed_markdown(md_file_path):
    with open(md_file_path, "r", encoding="utf-8") as f:
        text = f.read()
    return [Document(page_content=text, metadata={"source": md_file_path})]
