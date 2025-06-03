from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS

def get_vectorstore(split_docs):
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(split_docs, embeddings)
    return vectorstore
