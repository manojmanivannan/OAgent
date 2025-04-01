from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
import os
from config import config
from uuid import uuid4
import chromadb
from langchain_chroma import Chroma


class ChromaClient:
    def __init__(self):
        self.embeddings = config.embeddings  # use shared embeddings from config
        etc_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "./etc"))
        chromadb_path = os.path.join(etc_path, "chroma_langchain_db")

        if os.path.exists(chromadb_path):
            persistent_client = chromadb.PersistentClient(path=chromadb_path)
            self.vector_store = Chroma(
                client=persistent_client,
                collection_name="example_collection",
                embedding_function=self.embeddings,
            )
        else:
            loader = DirectoryLoader(etc_path, glob="**/*.txt")
            docs = loader.load()
            headers_to_split_on = [
                ("#", "Header 1"),
                ("##", "Header 2"),
            ]
            markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
            md_header_splits = markdown_splitter.split_text(docs[0].page_content)
            # Char-level splits
            chunk_size = 500
            chunk_overlap = 30
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            splits = text_splitter.split_documents(md_header_splits)
            self.vector_store = Chroma(
                collection_name="example_collection",
                embedding_function=self.embeddings,
                persist_directory=chromadb_path,
            )
            uuids = [str(uuid4()) for _ in range(len(splits))]
            self.vector_store.add_documents(documents=splits, ids=uuids)

    def similarity_search(self, query: str, k: int = 2):
        results = self.vector_store.similarity_search(query, k=k)
        return "\n".join([res.page_content for res in results])


client = ChromaClient()
