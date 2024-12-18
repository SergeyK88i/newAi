from sentence_transformers import SentenceTransformer
import faiss
from typing import List, Tuple

# Импортируем ранее созданный класс GigaChatAPI
from GigaClass import GigaChatAPI
class TextRetriever:
    def __init__(self, model_name: str = 'distiluse-base-multilingual-cased-v1'):
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.texts = []

    def create_embeddings(self, file_path: str, chunk_size: int = 50):
        """Создает эмбеддинги с учетом заголовков"""
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()

        # Проверяем, что текст не пустой
        if not text:
            raise ValueError("Файл пустой или не содержит текста")

        # Разбиваем текст на секции по заголовкам
        sections = []
        current_header = ""
        current_content = []
    
        for line in text.split('\n'):
            # Определяем заголовки (например, по # или по другим признакам)
            if line.startswith('#') or line.isupper():
                if current_header and current_content:
                    section_text = f"{current_header}\n{''.join(current_content)}"
                    sections.append(section_text)
                current_header = line
                current_content = []
            else:
                current_content.append(line + '\n')
    
        # Добавляем последнюю секцию
        if current_header and current_content:
            section_text = f"{current_header}\n{''.join(current_content)}"
            sections.append(section_text)

        # Проверяем наличие секций
        if not sections:
            raise ValueError("Не удалось выделить секции из текста")

        # Разбиваем каждую секцию на чанки с сохранением заголовка
        self.texts = []
        for section in sections:
            header = section.split('\n')[0]
            content = section[len(header):]
            # Разбиваем контент на чанки, добавляя заголовок к каждому
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i+chunk_size]
                self.texts.append(f"{header}\n{chunk}")
    
        # Проверяем наличие текстов для эмбеддингов
        if not self.texts:
            raise ValueError("Не удалось создать текстовые фрагменты")

        # Создаем эмбеддинги
        embeddings = self.model.encode(self.texts)

        # Проверяем размерность эмбеддингов
        if embeddings.shape[0] == 0:
            raise ValueError("Не удалось создать эмбеддинги")

        # Создаем FAISS индекс
        self.index = faiss.IndexFlatL2(embeddings.shape[1])
        self.index.add(embeddings.astype('float32'))

    # В методе retrieve добавить проверку
    def retrieve(self, query: str, k: int = 3) -> List[Tuple[str, float]]:
        """Ищет k наиболее релевантных фрагментов для запроса"""
        if not self.index or not self.texts:
            return []
        query_vector = self.model.encode([query])
        distances, indices = self.index.search(query_vector.astype('float32'), k)
        
        # Уменьшаем порог релевантности для более строгой фильтрации
        RELEVANCE_THRESHOLD = 2.5
        results = []
        if len(indices) > 0 and len(indices[0]) > 0:
            for i, idx in enumerate(indices[0]):
                if distances[0][i] < RELEVANCE_THRESHOLD:  # Проверяем релевантность
                    results.append((self.texts[idx], distances[0][i]))
        
        return results