from langchain.chains import RetrievalQA
from langchain.llms import OpenAI

def get_qa_chain(retriever):
    return RetrievalQA.from_chain_type(
        llm=OpenAI(),
        chain_type="stuff",
        retriever=retriever
    )
