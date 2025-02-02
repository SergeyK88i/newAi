from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np
from sklearn.cluster import KMeans
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class Document:
    chapter: str
    section: str
    text: str
    cluster: int = 0

@dataclass
class DocumentEmbedding:
    chapter: str
    section: str
    text: str
    cluster: int
    embedding: np.ndarray

def parse_text_file(filepath: str) -> List[Document]:
    documents = []
    current_chapter = ""
    current_section = ""
    
    with open(filepath, 'r', encoding='utf-8') as file:
        text_buffer = []
        
        for line in file:
            line = line.strip()
            
            # Определяем главу (по # в начале строки)
            if line.startswith('# '):
                if text_buffer:
                    # Создаем документ из накопленного текста
                    documents.append(Document(
                        chapter=current_chapter,
                        section=current_section,
                        text=' '.join(text_buffer)
                    ))
                    text_buffer = []
                current_chapter = line[2:]
                
            # Определяем секцию (по ## в начале строки)
            elif line.startswith('## '):
                if text_buffer:
                    documents.append(Document(
                        chapter=current_chapter,
                        section=current_section,
                        text=' '.join(text_buffer)
                    ))
                    text_buffer = []
                current_section = line[3:]
                
            # Собираем текст
            elif line and not line.startswith('#'):
                text_buffer.append(line)
                
            # Пустая строка - создаем новый документ
            elif text_buffer:
                documents.append(Document(
                    chapter=current_chapter,
                    section=current_section,
                    text=' '.join(text_buffer)
                ))
                text_buffer = []
    
    # Добавляем последний документ если остался
    if text_buffer:
        documents.append(Document(
            chapter=current_chapter,
            section=current_section,
            text=' '.join(text_buffer)
        ))
    
    return documents

# Использование:
documents = parse_text_file('../file.txt')



# Загружаем модель и токенизатор
tokenizer = AutoTokenizer.from_pretrained('ai-forever/sbert_large_nlu_ru')
model = AutoModel.from_pretrained('ai-forever/sbert_large_nlu_ru')
def split_text(text, max_length=512):
    parts = text.split('\n\n')
    current_chunk = []
    chunks = []
    
    for part in parts:
        tokens = tokenizer.encode(part)
        if len(tokens) + len(current_chunk) < max_length:
            current_chunk.extend(tokens)
        else:
            chunks.append(tokenizer.decode(current_chunk))
            current_chunk = tokens
    
    if current_chunk:
        chunks.append(tokenizer.decode(current_chunk))
    
    return chunks
    
def get_embeddings(text):
    encoded = tokenizer(text, padding=True, truncation=True, return_tensors='pt')
    with torch.no_grad():
        model_output = model(**encoded)
    return model_output.last_hidden_state.mean(dim=1)



# # Пример структурированной документации
# documents = [
#     # Глава 1: Установка
#     Document(
#         chapter="Chapter 1: Installation",
#         section="System Requirements",
#         text="Для установки OpenShift требуется минимум 16GB RAM на мастер-ноде"
#     ),
#     Document(
#         chapter="Chapter 1: Installation", 
#         section="System Requirements",
#         text="Мастер-нода должна иметь не менее 4 CPU cores для стабильной работы"
#     ),
#     Document(
#         chapter="Chapter 1: Installation",
#         section="Prerequisites",
#         text="Необходимо установить Docker версии не ниже 1.13"
#     ),
#     # Глава 2: Сеть
#     Document(
#         chapter="Chapter 2: Networking",
#         section="Network Policies",
#         text="Настройка сетевых политик в OpenShift производится через NetworkPolicy"
#     ),
#     Document(
#         chapter="Chapter 2: Networking",
#         section="Network Policies",
#         text="Для ограничения доступа между подами используются network policies"
#     ),
#     Document(
#         chapter="Chapter 2: Networking",
#         section="Service Mesh",
#         text="Service Mesh предоставляет возможности маршрутизации и балансировки"
#     )
# ]

def cluster_documents_by_chapter(documents: List[Document], n_clusters: int = 2) -> Dict[str, List[Document]]:
    chapters = {}
    for doc in documents:
        if doc.chapter not in chapters:
            chapters[doc.chapter] = []
        chapters[doc.chapter].append(doc)
    
    for chapter, docs in chapters.items():
        texts = [doc.text for doc in docs]
        embeddings = [get_embeddings(text).numpy() for text in texts]
        embeddings = np.vstack(embeddings)
        
        kmeans = KMeans(n_clusters=n_clusters)
        clusters = kmeans.fit_predict(embeddings)
        
        for doc, cluster_num in zip(docs, clusters):
            doc.cluster = cluster_num
            
    return chapters

def create_embeddings_database(clustered_docs):
    embedded_docs = []
    for chapter, docs in clustered_docs.items():
        for doc in docs:
            embedding = get_embeddings(doc.text).numpy()
            embedded_doc = DocumentEmbedding(
                chapter=doc.chapter,
                section=doc.section,
                text=doc.text,
                cluster=doc.cluster,
                embedding=embedding
            )
            embedded_docs.append(embedded_doc)
    return embedded_docs

def find_similar_documents(query: str, embedded_docs: List[DocumentEmbedding], top_k: int = 3):
    query_embedding = get_embeddings(query).numpy()
    
    # Вычисляем косинусное сходство между запросом и всеми документами
    similarities = []
    for doc in embedded_docs:
        similarity = np.dot(query_embedding, doc.embedding.T) / (
            np.linalg.norm(query_embedding) * np.linalg.norm(doc.embedding)
        )
        similarities.append((doc, float(similarity)))
    
    # Сортируем по убыванию сходства и берем top_k результатов
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:top_k]

# Применяем кластеризацию
clustered_docs = cluster_documents_by_chapter(documents)

# Создаем базу эмбеддингов
embedded_docs = create_embeddings_database(clustered_docs)

# Выводим результаты кластеризации
print("Результаты кластеризации:")
for chapter, docs in clustered_docs.items():
    print(f"\n{chapter}")
    for cluster_id in set(doc.cluster for doc in docs):
        print(f"\nCluster {cluster_id}:")
        cluster_docs = [doc for doc in docs if doc.cluster == cluster_id]
        for doc in cluster_docs:
            print(f"- Section: {doc.section}")
            print(f"  Text: {doc.text}")

# Пример поиска по запросу
query = "Как настроить сетевые политики?"
print("\nПоиск по запросу:", query)
similar_docs = find_similar_documents(query, embedded_docs)
print("\nНайденные документы:")
for doc, similarity in similar_docs:
    print(f"\nСходство: {similarity:.4f}")
    print(f"Глава: {doc.chapter}")
    print(f"Раздел: {doc.section}")
    print(f"Текст: {doc.text}")
