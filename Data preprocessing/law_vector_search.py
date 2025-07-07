import json
import faiss
import os
import re
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict

# 参数设置
INPUT_JSON = "law_output.json"
OUTPUT_CHUNKS_JSON = "chunks.json"
OUTPUT_INDEX_FILE = "faiss.index"
CHUNK_SIZE = 300  # 每段最多多少字符
CHUNK_OVERLAP = 30  # 重叠字符数

# 初始化模型
print("正在加载模型 SentenceTransformer...")
model = SentenceTransformer('hf_models/text2vec-base-chinese')
embedding_dim = model.get_sentence_embedding_dimension()
print(f"模型加载完成，输出维度为：{embedding_dim} 维\n")


# 分段函数
def split_text_with_overlap(text: str, max_len: int, overlap: int) -> List[str]:
    # 1. 按句号分割
    sentences = re.split(r'(?<=[。！？])', text)  # 包括：。、！？
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        # 如果还未超长，加到分段里
        if len(current_chunk) + len(sentence) <= max_len:
            current_chunk += sentence
        else:
            if current_chunk:
                chunks.append(current_chunk)

            if overlap > 0 and chunks:
                overlap_text = chunks[-1][-overlap:]
                current_chunk = overlap_text + sentence
            else:
                current_chunk = sentence

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


# 读取法条数据
print(f"正在读取法条数据：{INPUT_JSON}")
with open(INPUT_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)
print(f"读取成功，共 {len(data)} 条法条\n")


# 构造分段与元数据
print("正在进行智能重叠分段处理...")
chunks = []
metadatas = []

for entry in data:
    full_text = entry["content"].replace("\n", "").strip()
    chunk_list = split_text_with_overlap(full_text, CHUNK_SIZE, CHUNK_OVERLAP)

    for chunk in chunk_list:
        full_chunk_text = f"{entry['category']} {entry['title']} {chunk}"
        chunks.append(full_chunk_text)
        metadatas.append({
            "id": entry["id"],
            "category": entry["category"],
            "article": entry["title"],
            "chunk": chunk
        })

print(f"分段完成，共生成 {len(chunks)} 段文本\n")


# 文本向量化
print("正在进行文本向量化（embedding）...")
embeddings = model.encode(chunks, show_progress_bar=True, normalize_embeddings=True)
print(f"向量化完成，向量形状为：{embeddings.shape}\n")


# 构建 FAISS 索引
print("正在构建 FAISS 索引...")
index = faiss.IndexFlatIP(embedding_dim)  # IP = inner product 代表 cosine 相似度
index.add(embeddings)
faiss.write_index(index, OUTPUT_INDEX_FILE)
print(f"索引已保存至：{OUTPUT_INDEX_FILE}\n")


# 保存 chunks 元数据 
print("正在保存段落元数据至 JSON 文件...")
with open(OUTPUT_CHUNKS_JSON, "w", encoding="utf-8") as f:
    json.dump(metadatas, f, ensure_ascii=False, indent=2)
print(f"段落信息已保存至：{OUTPUT_CHUNKS_JSON}\n")

print("所有步骤执行完毕！法条数据已经准备好用于向量检索。")
