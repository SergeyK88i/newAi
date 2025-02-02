from sentence_transformers import SentenceTransformer
import faiss
from typing import List, Tuple
import re
from features.knowledge_base import KnowledgeBase
import json
import numpy as np
class MetadataAdapter:
    def __init__(self, base_model):
        self.model = base_model
        self.terms_weight = 0.2
        self.concepts_weight = 0.3
        self.code_weight = 0.15
        
    def adapt_embedding(self, base_embedding, metadata):
        adapted = base_embedding.copy()
        
        # Добавляем эмбеддинги терминов
        if metadata['terms']:
            terms_text = ' '.join(metadata['terms'])
            terms_embedding = self.model.encode([terms_text])[0]
            adapted += self.terms_weight * terms_embedding
            
        # Добавляем эмбеддинги концепций    
        if metadata['concepts']:
            concepts_text = ' '.join(metadata['concepts'])
            concepts_embedding = self.model.encode([concepts_text])[0]
            adapted += self.concepts_weight * concepts_embedding
            
        # Добавляем эмбеддинги кода
        if metadata['code_samples']:
            code_text = ' '.join(metadata['code_samples'])
            code_embedding = self.model.encode([code_text])[0]
            adapted += self.code_weight * code_embedding
            
        # Нормализуем результат
        adapted = adapted / np.linalg.norm(adapted)
        
        return adapted
class TextRetriever:
    def __init__(self, model_name: str = 'distiluse-base-multilingual-cased-v1'):
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.texts = []
        self.chunks_metadata = []
        self.knowledge_base = KnowledgeBase()
        self.adapter = MetadataAdapter(self.model)

    def semantic_chunk(self, text: str) -> List[str]:
        """Семантическая разбивка текста с учетом связанных частей"""
        chunks = []
        current_chunk = []
        code_block = False
        
        lines = text.split('\n')
        for line in lines:
            # Определяем начало/конец блока кода
            if line.strip().startswith('```'):
                code_block = not code_block

            # Новый чанк начинается при:
            if (line.startswith('# ') or  # Заголовок
                line.startswith('## ') or  # Нумерованный список
                line.startswith('### ') or   # Маркированный список
                'ПРИМЕР:' in line or       # Примеры
                'Шаг ' in line):          # Инструкции
            
                if current_chunk:
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = []
                
            current_chunk.append(line)
        
            # Сохраняем блоки кода вместе с контекстом
            if code_block:
                continue
            
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
    
        return [chunk.strip() for chunk in chunks if chunk.strip()]

    def extract_metadata(self, text: str) -> dict:
        """Извлечение расширенных метаданных из текста"""
        # Находим основной заголовок документа (# Заголовок)
        main_title_match = re.search(r'^#\s+(.+)$', text, re.MULTILINE)
        parent_title = ""
        
        if main_title_match:
            # Если это основной заголовок, он становится parent_title
            parent_title = main_title_match.group(1).strip()
        else:
            # Если это не основной заголовок, ищем последний основной заголовок
            for chunk in reversed(self.texts):
                main_title_match = re.search(r'^#\s+(.+)$', chunk, re.MULTILINE)
                if main_title_match:
                    parent_title = main_title_match.group(1).strip()
                    break
        
        metadata = {
            'content': text,
            'title': text.split('\n')[0] if text else '',
            'parent_title': parent_title,
            'section_path': self._get_section_path(text),
            'terms': self._extract_terms(text),
            'concepts': self._extract_concepts(text),
            'is_code': bool(re.search(r'```.*```', text, re.DOTALL)),
            'is_instruction': any(marker in text.lower() for marker in 
                ['шаг', 'инструкция', 'настройка', 'установка']),
            'code_samples': re.findall(r'```.*?```', text, re.DOTALL)
        }
        return metadata

    def _get_section_path(self, text: str) -> list:
        """Получение полного пути секции в иерархии документа"""
        headers = []
        hierarchy = []
        
        # Ищем основной заголовок в предыдущих чанках
        for chunk in reversed(self.texts):
            main_title_match = re.search(r'^#\s+(.+)', chunk, re.MULTILINE)
            if main_title_match:
                hierarchy.append(main_title_match.group(1).strip())
                break
                
        # Обрабатываем текущий чанк
        for line in text.split('\n'):
            if line.startswith('#'):
                level = len(re.match(r'^#+', line).group())
                title = line.lstrip('#').strip()
                
                # Обновляем иерархию согласно уровню
                hierarchy = hierarchy[:level-1]
                hierarchy.append(title)
                
        return hierarchy


    def _extract_terms(self, text: str) -> List[str]:
        """Извлечение терминов и их вариаций"""
        terms = []
        # Ищем термины в скобках (часто содержат синонимы)
        bracket_terms = re.findall(r'\((.*?)\)', text)
        for term in bracket_terms:
            terms.extend(term.split(','))
        # Добавляем основные термины из заголовка
        header_match = re.search(r'#\s*([\w\s-]+)', text)
        if header_match:
            terms.extend(header_match.group(1).split())
        return [term.strip().lower() for term in terms if term.strip()]

    def _extract_concepts(self, text: str) -> List[str]:
        """Извлечение ключевых концепций из текста"""
        # Ищем определения после тире или двоеточия
        concepts = re.findall(r'[—:]\s*(.*?)(?=\n|$)', text)
        return [concept.strip() for concept in concepts if concept.strip()]

    def create_embeddings(self, file_path: str):
        """Создание векторных представлений текста"""
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
            print(f"Исходный текст: {len(text)} символов")
        if not text:
            raise ValueError("Файл пустой или не содержит текста")

        chunks = self.semantic_chunk(text)
        self.texts = chunks
        print('созданные чанки',len(self.texts))
        
        # Создаём расширенные метаданные
        self.chunks_metadata = [self.extract_metadata(chunk) for chunk in chunks]

        # Создаем адаптированные эмбеддинги с учетом метаданных
        text_embeddings = []
        for chunk, metadata in zip(chunks, self.chunks_metadata):
            # Базовый эмбеддинг текста
            base_embedding = self.model.encode([chunk])[0]
            # Обогащаем метаданными через адаптер
            adapted_embedding = self.adapter.adapt_embedding(base_embedding, metadata)
            text_embeddings.append(adapted_embedding)

        text_embeddings = np.vstack(text_embeddings)

        if text_embeddings.shape[0] == 0:
            raise ValueError("Не удалось создать эмбеддинги")

        dimension = text_embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(text_embeddings.astype('float32'))
        print('self.index',self.index.ntotal)

    def expand_query(self, query: str) -> str:
        expanded_terms = []
        for term, mappings in self.knowledge_base.terms_mapping.items():
            if term in query.lower():
                expanded_terms.extend(mappings)
                
                if term in self.knowledge_base.context_mapping:
                    context = self.knowledge_base.context_mapping[term]
                    expanded_terms.extend([
                        context['process'],
                        context['area'],
                        context['full_name']
                    ])
                    expanded_terms.extend(context['related_terms'])
        
        return ' '.join([query] + expanded_terms)

    def retrieve(self, query: str, k: int = 5) -> List[Tuple[str, float]]:
        """Семантический поиск по смыслу"""
        if not self.index or not self.texts:
            return []

        expanded_query = self.expand_query(query)
        # Векторное представление запроса
        query_vector = self.model.encode([expanded_query])
        
        # Поиск ближайших векторов через FAISS
        distances, indices = self.index.search(query_vector.astype('float32'), k)
        
        # Формируем результаты с учетом семантической близости
        results = []
        for i, idx in enumerate(indices[0]):
            # Нормализуем score для оценки близости
            semantic_score = 1 / (1 + distances[0][i])
            results.append((self.texts[idx], semantic_score))
        
        return sorted(results, key=lambda x: x[1], reverse=True)

    def print_all_chunks(self):
        print(f"Всего чанков: {len(self.texts)}\n")
        for i, chunk in enumerate(self.texts):
            print(f"=== Чанк {i+1} ===")
            print(f"Содержание:\n{chunk}")
            print("\nМетаданные:")
            print(json.dumps(self.chunks_metadata[i], indent=2, ensure_ascii=False))
            print("\n" + "="*50 + "\n")

