from llama_index import SimpleDirectoryReader, VectorStoreIndex
from llama_index.query_engine import RetrieverQueryEngine

# Load in documents
documents = SimpleDirectoryReader('./data').load_data()

# Construct Index
index = VectorStoreIndex.from_documents(documents)

# Query the index with a summary request
query_engine = index.as_query_engine()
summary_response = query_engine.query("Summarise the article")

# Print the summary
print(summary_response)
