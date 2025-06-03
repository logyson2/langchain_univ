from langchain.text_splitter import RecursiveCharacterTextSplitter
from document_loader import load_parsed_markdown
from embedding import get_vectorstore
from retriever import get_retriever
from qa_chain import get_qa_chain

OUTPUT_FILE = "./outputs/2026연세수시_parsed.md"

# 1. 문서 로드
docs = load_parsed_markdown(OUTPUT_FILE)

# 2. 청크화
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
split_docs = splitter.split_documents(docs)

# 3. 임베딩 & 벡터DB
vectorstore = get_vectorstore(split_docs)

# 4. Retriever
retriever = get_retriever(vectorstore)

# 5. QA Chain
qa_chain = get_qa_chain(retriever)

# 6. 질의
query = "수시 모집 주요 변경사항을 알려줘."
result = qa_chain.run(query)
print(result)
