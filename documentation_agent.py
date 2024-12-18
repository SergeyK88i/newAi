from text_retriever import TextRetriever
from GigaClass import GigaChatAPI

class DocumentationAgent:    
    def __init__(self, file_path: str, auth_token: str):
        self.retriever = TextRetriever()
        self.retriever.create_embeddings(file_path)
        self.giga_chat = GigaChatAPI()
        response = self.giga_chat.get_token(auth_token)
        if not response or response.status_code != 200:
            raise Exception("Не удалось получить токен для GigaChat")

    def ask(self, query: str, max_chunks: int = 7) -> str:
        if query.lower() == 'clear':
            return self.clear_conversation()

        # Получаем релевантные чанки с учётом улучшенного поиска
        relevant_chunks = self.retriever.retrieve(query, k=max_chunks)

        if not relevant_chunks:
            return "В предоставленной документации нет информации по этому вопросу."

        # Объединяем связанные чанки
        context = "\n".join([chunk for chunk, _ in relevant_chunks])
        
        system_message = """Вы - ассистент по документации. 
        Отвечайте ТОЛЬКО на основе предоставленного контекста из документации.
        Старайтесь давать структурированные ответы.
        Если информации недостаточно - сообщите об этом.
        """

        user_message = f"Контекст:\n{context}\n\nВопрос: {query}\n\nОтвет:"
        
        chat_response = self.giga_chat.get_chat_completion(system_message, user_message)

        if chat_response and chat_response.status_code == 200:
            return chat_response.json()['choices'][0]['message']['content']
        else:
            return "Извините, не удалось получить ответ. Попробуйте переформулировать вопрос."
