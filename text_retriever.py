from sentence_transformers import SentenceTransformer
import faiss
from typing import List, Tuple
import re

# Импортируем ранее созданный класс GigaChatAPI
from GigaClass import GigaChatAPI
class TextRetriever:
    def __init__(self, model_name: str = 'distiluse-base-multilingual-cased-v1'):
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.texts = []
        self.chunks_metadata = []  # Добавляем хранение метаданных

    def semantic_chunk(self, text: str) -> List[str]:
        """Семантическая разбивка текста по заголовкам"""
        chunks = re.split(r'(?=# )', text)
        return [chunk.strip() for chunk in chunks if chunk.strip()]

    def extract_keywords(self, text: str) -> List[str]:
        """Извлечение ключевых слов из заголовков"""
        header_match = re.search(r'#\s*([\w\s-]+)', text)
        if header_match:
            # Извлекаем слова из заголовка и очищаем их
            words = header_match.group(1).split()
            # Обрабатываем аббревиатуры и специальные термины
            keywords = []
            for word in words:
                # Сохраняем аббревиатуры в верхнем регистре
                if word.isupper():
                    keywords.append(word)
                else:
                    keywords.append(word.lower())
            return keywords
        return []

    def create_embeddings(self, file_path: str):
        """Улучшенное создание эмбеддингов с метаданными"""
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()

        # Проверяем, что текст не пустой
        if not text:
            raise ValueError("Файл пустой или не содержит текста")

        # Разбиваем на семантические чанки
        chunks = self.semantic_chunk(text)
        self.texts = chunks

         # Создаём расширенные метаданные для каждого чанка
        self.chunks_metadata = []
        for chunk in chunks:
            metadata = {
                'content': chunk,
                'keywords': self.extract_keywords(chunk),
                'title': chunk.split('\n')[0] if chunk else '',
                'is_definition': bool(re.search(r'это|является|представляет собой', chunk.lower()))
            }
            self.chunks_metadata.append(metadata)

        # Создаем эмбеддинги
        embeddings = self.model.encode(self.texts)

        if embeddings.shape[0] == 0:
            raise ValueError("Не удалось создать эмбеддинги")

        # Создаем и наполняем FAISS индекс
        dimension = embeddings.shape[1]  # Получаем размерность эмбеддингов
        self.index = faiss.IndexFlatL2(dimension)  # Создаем индекс
        self.index.add(embeddings.astype('float32')) 
        

    # В методе retrieve добавить проверку
    def retrieve(self, query: str, k: int = 3) -> List[Tuple[str, float]]:
        """Улучшенный поиск с учётом метаданных"""
        if not self.index or not self.texts:
            return []

        # Очищаем запрос от стоп-слов
        stop_words = {'что', 'такое', 'это', 'как', 'где', 'когда'}
        clean_query = ' '.join([word for word in query.lower().split() if word not in stop_words])
        
        query_vector = self.model.encode([clean_query])
        distances, indices = self.index.search(query_vector.astype('float32'), k)
        
        RELEVANCE_THRESHOLD = 2.5
        results = []
        
        if len(indices) > 0 and len(indices[0]) > 0:
            for i, idx in enumerate(indices[0]):
                if distances[0][i] < RELEVANCE_THRESHOLD:
                    # Добавляем проверку на ключевые слова
                    chunk_metadata = self.chunks_metadata[idx]
                    if any(keyword.lower() in clean_query for keyword in chunk_metadata['keywords']):
                        results.append((self.texts[idx], distances[0][i]))
        
        return results