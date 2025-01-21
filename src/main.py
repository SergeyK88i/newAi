from fastapi import FastAPI, HTTPException
from documentation_agent import DocumentationAgent
from typing import List, Dict
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Documentation Assistant API")
# Добавляем CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем все источники
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем все методы
    allow_headers=["*"],  # Разрешаем все заголовки
)
# Инициализация агента при старте
file_path = '../file.txt'
auth_token = 'MmMzZDA5OGMtODIyNS00MGJlLWJhOGItMzRhOTgyY2M0YjBhOjk3NGQ0ZTA3LWQ3MDUtNDhhNC1iYjFlLTQ0N2Y2ZmJkMWM4Mg=='
agent = DocumentationAgent(file_path, auth_token)

class Message(BaseModel):
    role: str
    content: str

class Query(BaseModel):
    text: str
    history: List[Message]

class RelevantChunk(BaseModel):
    text: str
    score: float

class Response(BaseModel):
    answer: str
    relevant_chunks: List[RelevantChunk]

@app.post("/api/v1/ask", response_model=Response)
def ask_question(query: Query):
    # Обновляем историю в агенте
    agent.giga_chat.conversation_history = [
        {"role": msg.role, "content": msg.content} 
        for msg in query.history
    ]
    
    # Получаем релевантные чанки
    relevant_chunks = agent.retriever.retrieve(query.text)
    chunks_data = [
        RelevantChunk(text=chunk, score=score) 
        for chunk, score in relevant_chunks
    ]
    
    # Получаем ответ от агента с учетом истории
    response = agent.ask(query.text)
    
    return Response(
        answer=response,
        relevant_chunks=chunks_data
    )
    
@app.post("/api/v1/clear")
def clear_history():
    result = agent.clear_conversation()
    print(f"Результат очистки: {result}")
    return {"status": "success", "message": "История диалога очищена"}

@app.get("/api/v1/health")
def health_check():
    return {"status": "ok"}
