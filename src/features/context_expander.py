import re


class ContextExpander:
    def __init__(self, retriever):
        self.retriever = retriever

    def expand_context(self, initial_chunks, query):
        expanded_context = []
        
        for chunk, score in initial_chunks:
            expanded_context.append(chunk)
            
            # Получаем метаданные текущего чанка
            chunk_metadata = self.retriever.chunks_metadata[self.retriever.texts.index(chunk)]
            
            # Ищем все чанки из того же раздела
            for idx, metadata in enumerate(self.retriever.chunks_metadata):
                if metadata['parent_title'] == chunk_metadata['parent_title'] and \
                   metadata['section_path'] == chunk_metadata['section_path'] and \
                   self.retriever.texts[idx] not in expanded_context:
                    expanded_context.append(self.retriever.texts[idx])
                    
            # Ищем связанные подразделы
            if chunk_metadata['section_path']:
                parent_section = chunk_metadata['section_path'][0]
                for idx, metadata in enumerate(self.retriever.chunks_metadata):
                    if metadata['section_path'] and metadata['section_path'][0] == parent_section:
                        if self.retriever.texts[idx] not in expanded_context:
                            expanded_context.append(self.retriever.texts[idx])

            # Добавляем инструкции если нужно
            if any(marker in query.lower() for marker in ["как", "настройка", "установка"]):
                related_instructions = self.retriever.retrieve(f"инструкция {query}", k=2)
                expanded_context.extend([c for c, _ in related_instructions])

            # Добавляем примеры если нужно
            if "пример" in query.lower():
                code_samples = self.retriever.retrieve(f"пример {query}", k=2)
                expanded_context.extend([c for c, _ in code_samples])


        return expanded_context