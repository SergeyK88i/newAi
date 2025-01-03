import re

class ContextExpander:
    def __init__(self, retriever):
        self.retriever = retriever
        
    def expand_context(self, initial_chunks, query):
        expanded_context = []
        
        # Добавляем исходные чанки
        for chunk, score in initial_chunks:
            expanded_context.append(chunk)
            
            # Ищем связанные инструкции
            if any(marker in query.lower() for marker in ['как', 'настройка', 'установка']):
                related_instructions = self.retriever.retrieve(
                    f"инструкция {query}", k=2)
                expanded_context.extend([c for c, _ in related_instructions])
                
            # Ищем примеры кода
            if 'пример' in query.lower():
                code_samples = self.retriever.retrieve(
                    f"пример {query}", k=2)
                expanded_context.extend([c for c, _ in code_samples])
                
            # Извлекаем ключевые термины из чанка
            terms = self.extract_terms(chunk)
            
            # Ищем связанные чанки для каждого термина
            for term in terms:
                related_chunks = self.retriever.retrieve(term, k=2)
                for related_chunk, related_score in related_chunks:
                    if related_chunk not in expanded_context:
                        expanded_context.append(related_chunk)
        
        return expanded_context
        
    def extract_terms(self, text):
        # Извлекаем технические термины и аббревиатуры
        terms = []
        # Ищем слова в верхнем регистре (аббревиатуры)
        abbr_pattern = r'\b[A-ZА-Я]{2,}\b'
        terms.extend(re.findall(abbr_pattern, text))
        
        # Ищем определения
        def_pattern = r'([A-ZА-Я][a-zа-я]+)\s+-\s+это'
        terms.extend(re.findall(def_pattern, text))
        
        return terms
