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

    def clarify_query(self, query: str) -> str:
        # Находим релевантные чанки для термина
        relevant_chunks = self.retriever.retrieve(query, k=5)
        
        # Категории уточнений
        categories = {
            'definition': ['что это', 'определение', 'описание'],
            'setup': ['установка', 'настройка', 'конфигурация'],
            'usage': ['использование', 'применение', 'работа'],
            'examples': ['пример', 'код', 'демонстрация'],
            'troubleshooting': ['ошибка', 'проблема', 'решение']
        }
        
        found_categories = []
        
        # Анализируем найденные чанки
        for chunk, _ in relevant_chunks:
            chunk_lower = chunk.lower()
            for category, keywords in categories.items():
                if any(keyword in chunk_lower for keyword in keywords):
                    found_categories.append(category)
        
        # Формируем варианты уточнений
        clarifications = {
            'definition': f"узнать определение {query}",
            'setup': f"получить инструкцию по установке/настройке {query}",
            'usage': f"узнать как использовать {query}",
            'examples': f"посмотреть примеры использования {query}",
            'troubleshooting': f"решить проблему с {query}"
        }
        
        # Собираем доступные уточнения
        available_options = [clarifications[cat] for cat in set(found_categories)]
        
        return f"Уточните, что вы хотите узнать о {query}:\n" + \
               "\n".join([f"- {option}" for option in available_options])

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
            thought = f"Тип запроса: {query_type}. Ищем информацию в документации."
            
            # Действие - поиск информации через TextRetriever
            relevant_chunks = self.retriever.retrieve(next_prompt, k=15)
            if not relevant_chunks:
                return "В предоставленной документации нет информации по этому вопросу."

            # Расширяем контекст через ContextExpander
            expanded_context = self.context_expander.expand_context(relevant_chunks, next_prompt)
            context = "\n".join(expanded_context)
            
            # Формируем сообщение для модели
            user_message = f"""Thought: {thought}
            Action: Найдены релевантные фрагменты документации
            Context: {context}

            Important: Используйте ТОЛЬКО информацию из предоставленного контекста.
            Question: {next_prompt}"""            
            # Получаем ответ от модели
            self.request_counter += 1  # увеличиваем счетчик
            chat_response = self.giga_chat.get_chat_completion(system_message, user_message)
            print(f"Запрос #{self.request_counter} к GigaChat выполнен")
            
            # Добавляем проверку успешности первого запроса
            if not chat_response or chat_response.status_code != 200:
                return "Не удалось получить ответ от сервиса"

            if chat_response and chat_response.status_code == 200:
                first_response = chat_response.json()['choices'][0]['message']['content']  # Сохраняем ответ
                print(f"Получен ответ на первый запрос: {first_response}")

                # Проверяем релевантность ответа
                system_message_validate = """Вы - эксперт по оценке качества ответов.
                Проанализируйте ответ и определите:
                1. Отвечает ли он на поставленный вопрос
                2. Содержит ли всю необходимую информацию
                3. Нужны ли уточнения
                
                Если ответ неполный или нерелевантный - укажите "PAUSE" и опишите что нужно уточнить.
                Если ответ полный - укажите "VALID"."""

                user_message_validate = f"""Вопрос: {query}
                Ответ: {first_response}
                Оцените релевантность ответа."""

                self.request_counter += 1
                validation_response = self.giga_chat.get_chat_completion(system_message_validate, user_message_validate)
                print(f"Запрос #{self.request_counter} к GigaChat выполнен")
            
                if validation_response and validation_response.status_code == 200:
                    validation_result = validation_response.json()['choices'][0]['message']['content']
                    
                    # Если ответ валидный - сразу возвращаем
                    if "VALID" in validation_result:
                        validated_response = self.validate_response(first_response, context)
                        self.question_matcher.add_question(query, validated_response)
                        print(f"Всего запросов к GigaChat: {self.request_counter}")
                        return validated_response

                    # Продолжаем только если нужна дополнительная информация   
                    if "PAUSE" in validation_result:
                        # Извлекаем причину паузы: для понимания что именно нужно уточнить
                        try:
                            pause_reason = validation_result.split("PAUSE:")[1].strip()
                        except IndexError:
                            pause_reason = "Не удалось определить причину паузы"
                            
                        # 1. Сначала проверяем автоматические уточнения
                        clarification_options = self.clarify_query(query)

                        if clarification_options:
                            # Добавляем вопрос от GigaChat к вариантам уточнений
                            giga_question = f"\nУточняющий вопрос от ассистента: {pause_reason}"
                            return clarification_options + giga_question

                        
                        # 2. Пробуем найти дополнительную информацию
                        # Если уточнения не найдены, используем существующую логику
                        # Новое действие - поиск дополнительной информации
                        # Ищем дополнительные чанки по причине паузы
                        additional_chunks = self.retriever.retrieve(pause_reason, k=5)
                        
                        if additional_chunks:
                            
                            additional_context = self.context_expander.expand_context(additional_chunks, pause_reason)
                            # Формируем новый промпт:
                            next_prompt = f"""Observation: Требуется уточнение: {pause_reason}
                            Предыдущий ответ: {first_response}
                            Дополнительный контекст:{' '.join(additional_context)}
                            Вопрос: {query}
                            Пожалуйста, предоставьте более полный ответ."""
                            continue

                        # 3. Если автоматические уточнения не найдены, 
                        # возвращаем только вопрос от GigaChat
                        giga_question = f"Для предоставления точного ответа мне нужно уточнить: {pause_reason}"
                        return giga_question

        return "Не удалось получить ответ. Попробуйте переформулировать вопрос."
        print(f"Всего запросов к GigaChat: {self.request_counter}")
    def clear_conversation(self):
        """Очистка истории диалога"""
        self.giga_chat.clear_history()
        return "История диалога очищена"
