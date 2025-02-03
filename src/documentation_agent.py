from text_retriever import TextRetriever
from GigaClass import GigaChatAPI
from features import QuestionMatcher, ContextExpander, KnowledgeBase
from typing import List
import re

class DocumentationAgent:    
    def __init__(self, file_path: str, auth_token: str):
        self.retriever = TextRetriever()
        self.retriever.create_embeddings(file_path)
        self.retriever.print_all_chunks()
        self.question_matcher = QuestionMatcher(model=self.retriever.model)
        self.context_expander = ContextExpander(self.retriever)
        self.giga_chat = GigaChatAPI()
        self.request_counter = 0  # добавляем счетчик
        self.knowledge_base = KnowledgeBase()
        response = self.giga_chat.get_token(auth_token)
        if not response or response.status_code != 200:
            raise Exception("Не удалось получить токен для GigaChat")

    def ask_with_chunks(self, query: str, chunks: List[str]):
        query_type = self._get_query_type(query)
        system_message = self._get_system_prompt(query_type)
        print(f"Всего чанков для обработки: {len(chunks)}")
        # Объединяем близкие по смыслу чанки
        merged_chunks = []
        current_chunk = []
        
        for chunk in chunks:
            if len('\n'.join(current_chunk)) + len(chunk) < 5000:  # Лимит токенов
                current_chunk.append(chunk)
            else:
                merged_chunks.append('\n'.join(current_chunk))
                current_chunk = [chunk]
                
        if current_chunk:
            merged_chunks.append('\n'.join(current_chunk))
        print(f"\nСгруппированные чанки ({len(merged_chunks)} групп):")
        for i, merged_chunk in enumerate(merged_chunks):
            print(f"\n=== Группа чанков {i+1} ===\n{merged_chunk}\n{'='*50}")

        # Передаем объединенные чанки
        for i, merged_chunk in enumerate(merged_chunks[:-1]):
            message = f"Часть {i+1}: {merged_chunk}"
            response = self.giga_chat.get_chat_completion(system_message, message)
            # if response is None or response.status_code != 200:
            #     return "Ошибка при передаче информации"
            if response and response.status_code == 200:
                response_text = response.json()['choices'][0]['message']['content']
                print(f"Ответ на чанк {i+1}: {response_text}")
                if "OK" not in response_text:
                    print(f"Предупреждение: GigaChat не ответил OK на чанк {i+1}")

        print(f"Отправка финального чанка с вопросом")
        # Отправляем последний чанк с вопросом
        final_message = f"""
        Последняя часть информации: {merged_chunks[-1]}
        
        Вопрос: {query}
        """
        final_response = self.giga_chat.get_chat_completion(system_message, final_message)
        
        if final_response is None or final_response.status_code != 200:
            return "Ошибка при получении финального ответа"
            
        return final_response.json()['choices'][0]['message']['content']

    def clarify_query(self, query: str) -> str:
        # Проверяем специальные термины из базы знаний
        for term in self.knowledge_base.terms_mapping:
            if term in query.lower():
                context = self.knowledge_base.context_mapping.get(term)
                if context:
                    # Добавляем контекстную информацию из базы знаний
                    query = context['full_name']

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
        # Если есть специальные термины, добавляем связанные термины из базы знаний
        for term in self.knowledge_base.terms_mapping:
            if term in query.lower():
                context = self.knowledge_base.context_mapping.get(term)
                if context:
                    available_options.append(f"узнать о связанных терминах: {', '.join(context['related_terms'])}")

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
        base_prompt = """Ты - точный ассистент по документации.
        Твоя задача - отвечать ИСКЛЮЧИТЕЛЬНО на основе предоставленного контекста.
        Ты получишь информацию частями. После каждой части отвечай "OK" если готов получить следующую.
        Когда получишь часть с вопросом - дай полный ответ.
        Если информации нет в контексте - ответь "В предоставленной документации нет информации по этому вопросу".
        Категорически запрещено использовать внешние знания или придумывать ответы."""
        
        type_prompts = {
            'definition': "Предоставь определение термина, используя ТОЛЬКО текст после символов '—' или ':' из контекста.",
            'setup': "Составь пошаговую инструкцию на основе информации из контекста.",
            'example': "Приведи только те примеры, которые есть в контексте.",
            'troubleshooting': "Опиши только те проблемы и решения, которые указаны в контексте.",
            'full': "Если информации в контексте недостаточно, укажи это."
        }
        
        return f"{base_prompt}\n{type_prompts.get(query_type, type_prompts['full'])}"


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
        
        # Проверяем телефоны
        phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phones_in_response = set(re.findall(phone_pattern, response))
        phones_in_context = set(re.findall(phone_pattern, context))
        
        # Проверяем email
        email_pattern = r'[\w\.-]+@[\w\.-]+'
        emails_in_response = set(re.findall(email_pattern, response))
        emails_in_context = set(re.findall(email_pattern, context))
        
        # Если найдены контакты, которых нет в контексте
        if phones_in_response - phones_in_context:
            response = re.sub(phone_pattern, '[ТЕЛЕФОН УДАЛЕН]', response)
            
        if emails_in_response - emails_in_context:
            response = re.sub(email_pattern, '[EMAIL УДАЛЕН]', response)

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

            # Анализ типа запроса
            query_type = self._get_query_type(next_prompt)
            system_message = self._get_system_prompt(query_type)
            print(f"\nСистемный промпт:\n{system_message}")
            thought = f"Тип запроса: {query_type}. Ищем информацию в документации."

            # Поиск информации
            relevant_chunks = self.retriever.retrieve(next_prompt, k=5)
            if not relevant_chunks:
                return "В предоставленной документации нет информации по этому вопросу."

            # Расширяем контекст
            expanded_context = self.context_expander.expand_context(relevant_chunks, next_prompt)
            
            # Порционная передача контекста и получение ответа
            self.request_counter += 1
            first_response = self.ask_with_chunks(next_prompt, expanded_context)
            print(f"Запрос #{self.request_counter} к GigaChat выполнен")
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
                
                if "VALID" in validation_result:
                    validated_response = self.validate_response(first_response, "\n".join(expanded_context))
                    self.question_matcher.add_question(query, validated_response)
                    print(f"Всего запросов к GigaChat: {self.request_counter}")
                    return validated_response

                if "PAUSE" in validation_result:
                    try:
                        pause_reason = validation_result.split("PAUSE:")[1].strip()
                    except IndexError:
                        pause_reason = "Не удалось определить причину паузы"

                    clarification_options = self.clarify_query(query)
                    if clarification_options:
                        giga_question = f"\nУточняющий вопрос от ассистента: {pause_reason}"
                        return clarification_options + giga_question

                    additional_chunks = self.retriever.retrieve(pause_reason, k=5)
                    if additional_chunks:
                        additional_context = self.context_expander.expand_context(additional_chunks, pause_reason)
                        next_prompt = f"""Observation: Требуется уточнение: {pause_reason}
                        Предыдущий ответ: {first_response}
                        Дополнительный контекст:{' '.join(additional_context)}
                        Вопрос: {query}
                        Пожалуйста, предоставьте более полный ответ."""
                        continue

                    giga_question = f"Для предоставления точного ответа мне нужно уточнить: {pause_reason}"
                    return giga_question

        return "Не удалось получить ответ. Попробуйте переформулировать вопрос."

    def clear_conversation(self):
        """Очистка истории диалога"""
        self.giga_chat.clear_history()
        self.question_matcher.questions_db = []  # Очищаем базу вопросов
        self.question_matcher.question_vectors = None
        return "История диалога и база вопросов очищены"
