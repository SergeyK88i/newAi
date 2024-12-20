from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

class QuestionMatcher:
    def __init__(self, model):
        self.model = model
        self.questions_db = []
        self.question_vectors = None
        
    def add_question(self, question: str, answer: str):
        self.questions_db.append({
            'question': question,
            'answer': answer
        })
        # Обновляем векторы вопросов
        vectors = self.model.encode([q['question'] for q in self.questions_db])
        self.question_vectors = vectors
        
    def find_similar(self, query: str, top_k=3):
        # Правильная проверка базы вопросов
        if len(self.questions_db) == 0 or self.question_vectors is None:
            return []
            
        query_vector = self.model.encode([query])
        # Ищем похожие вопросы
        scores = cosine_similarity(query_vector, self.question_vectors)[0]
        similar_idx = scores.argsort()[-top_k:][::-1]
        
        return [
            {
                'question': self.questions_db[idx]['question'],
                'answer': self.questions_db[idx]['answer'],
                'similarity': scores[idx]
            }
            for idx in similar_idx if scores[idx] > 0.7
        ]
