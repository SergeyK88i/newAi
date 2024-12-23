from text_retriever import TextRetriever
from GigaClass import GigaChatAPI
from features import QuestionMatcher, ContextExpander

class DocumentationAgent:    
    def __init__(self, file_path: str, auth_token: str):
        self.retriever = TextRetriever()
        self.retriever.create_embeddings(file_path)
        self.question_matcher = QuestionMatcher(model=self.retriever.model)
        self.context_expander = ContextExpander(self.retriever)
        self.giga_chat = GigaChatAPI()
        self.request_counter = 0  # добавляем счетчик
        response = self.giga_chat.get_token(auth_token)
        if not response or response.status_code != 200:
            raise Exception("Не удалось получить токен для GigaChat")

    def _get_query_type(self, query: str) -> str:
        """Определение типа запроса на основе ключевых слов"""
        query = query.lower()
        if 'определение' in query or 'что такое' in query:
            return 'definition'
        if 'как настроить' in query or 'как установить' in query or 'инструкция' in query:
            return 'setup'
        if 'пример' in query or 'как использовать' in query:
            return 'example'
        if 'ошибка' in query or 'проблема' in query:
            return 'troubleshooting'
        return 'full'

    def _get_system_prompt(self, query_type: str) -> str:
        """Получение специализированного промпта в зависимости от типа запроса"""
        prompts = {
            'definition': """Вы - точный ассистент по документации.
                       Используйте ТОЛЬКО предоставленный контекст.
                       Не добавляйте информацию из других источников.
                       Предоставьте определение термина, используя ТОЛЬКО текст после символов '—' или ':' из контекста.""",
        
            'setup': """Вы - технический специалист.
                    Используйте ТОЛЬКО предоставленный контекст.
                    Составьте инструкцию, опираясь ТОЛЬКО на информацию из контекста.
                    Не добавляйте шаги или параметры, которых нет в контексте.""",

            'example': """Вы - технический специалист.
                        Используйте ТОЛЬКО предоставленный контекст.
                        Приводите ТОЛЬКО те примеры, которые есть в контексте.
                        Не добавляйте свои примеры.""",

            'troubleshooting': """Вы - технический специалист.
                        Используйте ТОЛЬКО предоставленный контекст.
                        Описывайте ТОЛЬКО те проблемы и решения, которые указаны в контексте.""",
        
            'full': """Вы - точный ассистент по документации.
                    Используйте ТОЛЬКО предоставленный контекст.
                    Не добавляйте внешнюю информацию.
                    Если информации в контексте недостаточно, укажите это."""
        }
        return prompts.get(query_type, prompts['full'])

    def validate_response(self, response: str, context: str) -> str:
        # validate_response() проверяет качество ответа
        # Проверяет наличие ответа
        # Проверяет соответствие контексту
        # Добавляет префикс "Согласно документации"
        """Валидация ответа на соответствие контексту"""
        if not response:
            return "Не удалось получить ответ из документации"

        #Строгое сравнение?
        # if not any(chunk in response for chunk in context.split('\n')):
        #     return "Информация отсутствует в документации"
            
        if not response.startswith("Согласно документации:"):
            response = "Согласно документации: " + response
            
        return response

    def ask(self, query: str, max_iterations: int = 3) -> str:
        """Обработка запроса с учетом его типа"""
        if query.lower() == 'clear':
            return self.clear_conversation()

        next_prompt = query
        
        for i in range(max_iterations):
            # Сначала ищем похожие вопросы
            similar_questions = self.question_matcher.find_similar(next_prompt)
            if similar_questions:
                best_match = similar_questions[0]
                if best_match['similarity'] > 0.9:
                    return f"Найден похожий вопрос:\nВопрос: {best_match['question']}\nОтвет: {best_match['answer']}"

            # Мысль - анализ типа запроса
            query_type = self._get_query_type(next_prompt)
            # Выбираем специальный промпт для типа запроса
            system_message = self._get_system_prompt(query_type)
            
            # Действие - поиск информации через TextRetriever
            relevant_chunks = self.retriever.retrieve(next_prompt, k=15)
            if not relevant_chunks:
                return "В предоставленной документации нет информации по этому вопросу."

            # Расширяем контекст через ContextExpander
            expanded_context = self.context_expander.expand_context(relevant_chunks, next_prompt)
            context = "\n".join(expanded_context)
            
            # Формируем сообщение для модели
            user_message = f"Контекст:\n{context}\n\nВажно: Используйте ТОЛЬКО информацию из предоставленного контекста выше.Вопрос: {next_prompt}\n\nОтвет:"
            
            # Получаем ответ от модели
            self.request_counter += 1  # увеличиваем счетчик
            chat_response = self.giga_chat.get_chat_completion(system_message, user_message)
            print(f"Запрос #{self.request_counter} к GigaChat выполнен")

            if chat_response and chat_response.status_code == 200:
                response = chat_response.json()['choices'][0]['message']['content']

                # Если получен валидный ответ - сразу возвращаем его
                if "Answer" in response or not "PAUSE" in response:
                    validated_response = self.validate_response(response, context)
                    self.question_matcher.add_question(query, validated_response)
                    print(f"Всего запросов к GigaChat: {self.request_counter}")
                    return validated_response

                # Продолжаем только если нужно дополнительное наблюдение
                if "PAUSE" in response:
                    if not relevant_chunks: # проверка тех же чанков
                        next_prompt = "Observation: Информация не найдена"
                        continue
                    expanded_context = self.context_expander.expand_context(relevant_chunks, next_prompt)
                    next_prompt = f"Observation: Найдена информация: {expanded_context}"
                    continue

        return "Не удалось получить ответ. Попробуйте переформулировать вопрос."
        print(f"Всего запросов к GigaChat: {self.request_counter}")
    def clear_conversation(self):
        """Очистка истории диалога"""
        self.giga_chat.clear_history()
        return "История диалога очищена"
