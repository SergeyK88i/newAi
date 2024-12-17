import numpy as np
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

    def create_embeddings(self, file_path: str, chunk_size: int = 500):
        """Создает эмбеддинги из текстового файла"""
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        
        # Разбиваем текст на чанки
        self.texts = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        
        # Создаем эмбеддинги
        embeddings = self.model.encode(self.texts)
        
        # Создаем FAISS индекс
        self.index = faiss.IndexFlatL2(embeddings.shape[1])
        self.index.add(embeddings.astype('float32'))

    # В методе retrieve добавить проверку

    def retrieve(self, query: str, k: int = 3) -> List[Tuple[str, float]]:
        """Ищет k наиболее релевантных фрагментов для запроса"""
        query_vector = self.model.encode([query])
        distances, indices = self.index.search(query_vector.astype('float32'), k)
        
        # Уменьшаем порог релевантности для более строгой фильтрации
        RELEVANCE_THRESHOLD = 1.1
        results = []
        for i, idx in enumerate(indices[0]):
            if distances[0][i] < RELEVANCE_THRESHOLD:  # Проверяем релевантность
                results.append((self.texts[idx], distances[0][i]))
        
        return results


# Пример использования
if __name__ == "__main__":
    # Инициализация TextRetriever
    retriever = TextRetriever()

    # Создание эмбеддингов из файла
    retriever.create_embeddings('file.txt')

    # Инициализация GigaChatAPI
    giga_chat = GigaChatAPI()

    # Получение токена (замените на ваш реальный ключ)
    response = giga_chat.get_token("MmMzZDA5OGMtODIyNS00MGJlLWJhOGItMzRhOTgyY2M0YjBhOjk3NGQ0ZTA3LWQ3MDUtNDhhNC1iYjFlLTQ0N2Y2ZmJkMWM4Mg==")

    if response and response.status_code == 200:
        print("Токен успешно получен")

        # Пример запроса
        query = "что такое javascript?"


        relevant_chunks = retriever.retrieve(query)
        print("Релевантный ответ",relevant_chunks)
        # Формирование контекста из релевантных чанков
        context = "\n".join([chunk for chunk, _ in relevant_chunks])

        #Системное сообщение
        system_message = "Вы - ассистент, который отвечает на вопросы, используя только предоставленный контекст. Если в контексте нет информации для ответа на вопрос, скажите, что не можете ответить на основе имеющейся информации."
        # Формирование запроса к GigaChat с контекстом
        user_message = f"Контекст: {context}\n\nВопрос: {query}\n\nОтвет:"

        # Получение ответа от GigaChat
        chat_response = giga_chat.get_chat_completion(system_message, user_message)

        if chat_response and chat_response.status_code == 200:
            print("Ответ модели:", chat_response.json()['choices'][0]['message']['content'])
        else:
            print("Не удалось получить ответ от модели")
    else:
        print("Не удалось получить токен")