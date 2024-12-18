import numpy as np



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

        while True:
            query = input("Введите ваш вопрос (или 'exit' для выхода, 'clear' для очистки истории): ")
            
            if query.lower() == 'exit':
                break
            elif query.lower() == 'clear':
                giga_chat.clear_history()
                print("История диалога очищена")
                continue

            # Пример запроса
            # query = "что такое javascript?"


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