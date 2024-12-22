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
                           Предоставьте ТОЛЬКО определение термина из документации.
                           Используйте ТОЛЬКО текст после символов '—' или ':' до конца строки.""",
            
            'setup': """Вы - технический специалист. Предоставьте подробную пошаговую инструкцию по настройке/установке.
                        Разбейте ответ на четкие шаги. Укажите все необходимые параметры и зависимости.""",

            'example': """Вы - технический специалист. Предоставьте практические примеры использования.
                        Покажите конкретные сценарии применения с пояснениями.""",

            'troubleshooting': """Вы - технический специалист. Опишите решение проблемы пошагово.
                        Укажите возможные причины и способы их устранения.""",
            
            'full': """Вы - точный ассистент по документации.
                      Предоставьте полную информацию из документации.
                      Включите определение и применение."""
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

            # Мысль - анализ запроса
            query_type = self._get_query_type(next_prompt)
            system_message = self._get_system_prompt(query_type)
            
            # Действие - поиск информации
            relevant_chunks = self.retriever.retrieve(next_prompt, k=7)
            if not relevant_chunks:
                return "В предоставленной документации нет информации по этому вопросу."

            # Расширяем контекст
            expanded_context = self.context_expander.expand_context(relevant_chunks, next_prompt)
            context = "\n".join(expanded_context)
            
            # Формируем сообщение для модели
            user_message = f"Контекст:\n{context}\n\nВопрос: {next_prompt}\n\nОтвет:"
            
            # Получаем ответ от модели
            chat_response = self.giga_chat.get_chat_completion(system_message, user_message)

            if chat_response and chat_response.status_code == 200:
                response = chat_response.json()['choices'][0]['message']['content']

                if "PAUSE" in response:
                    # Наблюдение - проверка результатов
                    if not relevant_chunks:
                        next_prompt = "Observation: Информация не найдена"
                        continue
                        
                    expanded_context = self.context_expander.expand_context(relevant_chunks, next_prompt)
                    next_prompt = f"Observation: Найдена информация: {expanded_context}"
                    continue

                # Финальный ответ
                if "Answer" in response or i == max_iterations - 1:
                    validated_response = self.validate_response(response, context)
                    self.question_matcher.add_question(query, validated_response)
                    return validated_response

        return "Не удалось получить ответ. Попробуйте переформулировать вопрос."
    def clear_conversation(self):
        """Очистка истории диалога"""
        self.giga_chat.clear_history()
        return "История диалога очищена"
