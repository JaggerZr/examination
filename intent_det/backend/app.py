# import os
# import tiktoken
# from llama_index.core import Settings
# from llama_index.embeddings.huggingface import HuggingFaceEmbedding
# from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
# from llama_index.llms.openai import OpenAI
# from llama_index.core.node_parser import SentenceSplitter
# from llama_index.core.schema import TextNode, NodeWithScore
# from llama_index.core.retrievers import BaseRetriever
# from tqdm import tqdm
# from typing import Any, List
# from llama_index.core import (
#     QueryBundle,
#     PromptTemplate,
#     VectorStoreIndex,
#     StorageContext,
#     load_index_from_storage,
# )

# # loads BAAI/bge-small-en-v1.5
# embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-base-en-v1.5")
# # 分词器
# tokenizer = tiktoken.get_encoding("cl100k_base")

# # 全局设
# Settings.embed_model = embed_model
# Settings.tokenizer = tokenizer
# Settings.llm = None

# # check if storage already exists
# PERSIST_DIR = "./baseline_index"
# # load the existing index
# storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
# index = load_index_from_storage(storage_context)

# query = "I don't have enough credits. Can you help me find out which courses in the school are worth 3 credits?"
# vector_retriever = index.as_retriever(similarity_top_k=5)
# nodes = vector_retriever.retrieve(query)

# # 用于累加每个 class 的 score
# class_scores = {}

# # 累加每个 class 的 score
# for node in nodes:
#     class_name = node.metadata['class']  # 获取 class 信息
#     score = node.score  # 获取该节点的 score
    
#     # 如果该 class 已存在于字典中，累加 score，否则初始化
#     if class_name in class_scores:
#         class_scores[class_name] += score
#     else:
#         class_scores[class_name] = score

# # 找到总分最高的 class
# max_class = max(class_scores, key=class_scores.get)
# max_score = class_scores[max_class]

# # 输出总分最高的 class 及其得分
# print(f"得分最高的 class: {max_class}，总得分: {max_score}")

import os
import tiktoken
from flask import Flask, request, jsonify
from llama_index.core import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.core.retrievers import BaseRetriever
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # 允许所有来源的跨域请求

# 加载嵌入模型和分词器
embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-base-en-v1.5")
tokenizer = tiktoken.get_encoding("cl100k_base")

# 全局设置
Settings.embed_model = embed_model
Settings.tokenizer = tokenizer
Settings.llm = None

# 加载存储的索引
PERSIST_DIR = "./baseline_index"
storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
index = load_index_from_storage(storage_context)

@app.route('/classify', methods=['POST'])
def classify():
    # 获取请求中的用户输入
    data = request.get_json()
    user_query = data.get('text')
    
    if not user_query:
        return jsonify({"error": "No text provided"}), 400

    # 使用索引查询文本
    vector_retriever = index.as_retriever(similarity_top_k=5)
    nodes = vector_retriever.retrieve(user_query)

    # 用于累加每个 class 的 score
    class_scores = {}

    # 累加每个 class 的 score
    for node in nodes:
        class_name = node.metadata['class']  # 获取 class 信息
        score = node.score  # 获取该节点的 score
        
        # 如果该 class 已存在于字典中，累加 score，否则初始化
        if class_name in class_scores:
            class_scores[class_name] += score
        else:
            class_scores[class_name] = score

    # 找到总分最高的 class
    if class_scores:
        max_class = max(class_scores, key=class_scores.get)
        max_score = class_scores[max_class]
    else:
        return jsonify({"error": "No relevant class found"}), 404

    # 返回最高得分的 class 和得分
    return jsonify({
        "max_class": max_class,
        "max_score": max_score
    })

# 启动 Flask 应用
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
