from sentence_transformers import SentenceTransformer
import faiss
from typing import List, Tuple
import re

class TextRetriever:
    def __init__(self, model_name: str = 'distiluse-base-multilingual-cased-v1'):
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.texts = []
        self.chunks_metadata = []

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
                line.startswith('1. ') or  # Нумерованный список
                line.startswith('- ') or   # Маркированный список
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
        metadata = {
            'content': text,
            'title': text.split('\n')[0] if text else '',
            'terms': self._extract_terms(text),
            'concepts': self._extract_concepts(text),
            'is_code': bool(re.search(r'```.*```', text, re.DOTALL)),
            'is_instruction': any(marker in text.lower() for marker in 
                ['шаг', 'инструкция', 'настройка', 'установка']),
            'code_samples': re.findall(r'```.*?```', text, re.DOTALL)
        }
        return metadata

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

        if not text:
            raise ValueError("Файл пустой или не содержит текста")

        chunks = self.semantic_chunk(text)
        self.texts = chunks

        # Создаём расширенные метаданные
        self.chunks_metadata = [self.extract_metadata(chunk) for chunk in chunks]

        # Создаем эмбеддинги для текстов и концепций
        text_embeddings = self.model.encode([chunk['content'] for chunk in self.chunks_metadata])
        
        if text_embeddings.shape[0] == 0:
            raise ValueError("Не удалось создать эмбеддинги")

        dimension = text_embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(text_embeddings.astype('float32'))

    def retrieve(self, query: str, k: int = 5) -> List[Tuple[str, float]]:
        """Семантический поиск по смыслу"""
        if not self.index or not self.texts:
            return []

        # Векторное представление запроса
        query_vector = self.model.encode([query])
        
        # Поиск ближайших векторов через FAISS
        distances, indices = self.index.search(query_vector.astype('float32'), k)
        
        # Формируем результаты с учетом семантической близости
        results = []
        for i, idx in enumerate(indices[0]):
            # Нормализуем score для оценки близости
            semantic_score = 1 / (1 + distances[0][i])
            results.append((self.texts[idx], semantic_score))
        
        return sorted(results, key=lambda x: x[1], reverse=True)
