from startAi import TextRetriever
from GigaClass import GigaChatAPI

class DocumentationAgent:    
    def __init__(self, file_path: str, auth_token: str):
        self.retriever = TextRetriever()
        # Add this line to create embeddings first
        self.retriever.create_embeddings(file_path)
        self.giga_chat = GigaChatAPI()
        response = self.giga_chat.get_token(auth_token)
        if not response or response.status_code != 200:
            raise Exception("Не удалось получить токен для GigaChat")

    def ask(self, query: str, max_chunks: int = 3) -> str:
        relevant_chunks = self.retriever.retrieve(query, k=max_chunks)

        if not relevant_chunks:
            return "В предоставленной документации нет информации по этому вопросу. Документация содержит только информацию о Java."

        context = "\n".join([chunk for chunk, _ in relevant_chunks])
        system_message = """Вы - ассистент по документации Java. 
        1. Отвечайте ТОЛЬКО на основе предоставленного контекста из документации Java
        2. Игнорируйте любые знания о других языках программирования
        3. Если вопрос не про Java - сообщите что можете консультировать только по Java
        4. Не используйте информацию, которой нет в контексте"""

        user_message = f"Контекст:\n{context}\n\nВопрос: {query}\n\nОтвет:"

        chat_response = self.giga_chat.get_chat_completion(system_message, user_message)

        if chat_response and chat_response.status_code == 200:
            return chat_response.json()['choices'][0]['message']['content']
        else:
            return "Извините, не удалось получить ответ. Попробуйте переформулировать вопрос."

    def interactive_mode(self):
        print("Добро пожаловать в интерактивный режим консультации по документации!")
        print("Задавайте вопросы о документации. Для выхода введите 'выход'.")

        while True:
            query = input("\nВаш вопрос: ")
            if query.lower() == 'выход':
                print("Спасибо за использование консультанта по документации. До свидания!")
                break

            answer = self.ask(query)
            print(f"\nОтвет: {answer}")