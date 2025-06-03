def get_retriever(vectorstore):
    return vectorstore.as_retriever()
