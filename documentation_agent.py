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
        if 'история' in query or 'когда' in query:
            return 'history'
        if 'применение' in query or 'как используется' in query or 'для чего' in query:
            return 'usage'
        return 'full'

    def _get_system_prompt(self, query_type: str) -> str:
        """Получение специализированного промпта в зависимости от типа запроса"""
        prompts = {
            'definition': """Вы - точный ассистент по документации.
                           Предоставьте ТОЛЬКО определение термина из документации.
                           Используйте ТОЛЬКО текст после символов '—' или ':' до конца строки.""",
            
            'history': """Вы - точный ассистент по документации.
                         Предоставьте ТОЛЬКО информацию об истории разработки.
                         Ищите факты о датах создания, разработчиках и этапах развития.""",
            
            'usage': """Вы - точный ассистент по документации.
                       Предоставьте ТОЛЬКО информацию о применении и возможностях.
                       Опишите как используется и для чего предназначен термин.""",
            
            'full': """Вы - точный ассистент по документации.
                      Предоставьте полную информацию из документации.
                      Включите определение, историю и применение."""
        }
        return prompts.get(query_type, prompts['full'])

    def validate_response(self, response: str, context: str) -> str:
        """Валидация ответа на соответствие контексту"""
        if not response:
            return "Не удалось получить ответ из документации"

        #Строгое сравнение?
        if not any(chunk in response for chunk in context.split('\n')):
            return "Информация отсутствует в документации"
            
        if not response.startswith("Согласно документации:"):
            response = "Согласно документации: " + response
            
        return response

    def ask(self, query: str, max_chunks: int = 7) -> str:
        """Обработка запроса с учетом его типа"""
        if query.lower() == 'clear':
            return self.clear_conversation()

        # Сначала ищем похожие вопросы
        similar_questions = self.question_matcher.find_similar(query)
        if similar_questions:
            best_match = similar_questions[0]
            if best_match['similarity'] > 0.9:
                return f"Найден похожий вопрос:\nВопрос: {best_match['question']}\nОтвет: {best_match['answer']}"

        # Определяем тип запроса
        query_type = self._get_query_type(query)
        
        # Получаем релевантные чанки
        relevant_chunks = self.retriever.retrieve(query, k=max_chunks)
        if not relevant_chunks:
            return "В предоставленной документации нет информации по этому вопросу."

        # Расширяем контекст
        expanded_context = self.context_expander.expand_context(relevant_chunks, query)
        context = "\n".join(expanded_context)
        
        # Получаем специализированный промпт
        system_message = self._get_system_prompt(query_type)
        
        # Формируем сообщение для модели
        user_message = f"Контекст:\n{context}\n\nВопрос: {query}\n\nОтвет:"
        
        # Получаем ответ от модели
        chat_response = self.giga_chat.get_chat_completion(system_message, user_message)

        if chat_response and chat_response.status_code == 200:
            response = chat_response.json()['choices'][0]['message']['content']

            # Добавляем логирование
            print("\nОтвет от GigaChat до валидации:")
            print("-" * 50)
            print(response)
            print("-" * 50)

            validated_response = self.validate_response(response, context)
            # Сохраняем вопрос и ответ для будущего использования
            self.question_matcher.add_question(query, validated_response)
            return validated_response
        
        return "Не удалось получить ответ. Попробуйте переформулировать вопрос."

    def clear_conversation(self):
        """Очистка истории диалога"""
        self.giga_chat.clear_history()
        return "История диалога очищена"
