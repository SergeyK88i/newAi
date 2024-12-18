from documentation_agent import DocumentationAgent

def main():
    file_path = 'file.txt'
    auth_token = 'MmMzZDA5OGMtODIyNS00MGJlLWJhOGItMzRhOTgyY2M0YjBhOjk3NGQ0ZTA3LWQ3MDUtNDhhNC1iYjFlLTQ0N2Y2ZmJkMWM4Mg=='

    # Создаем экземпляр агента
    agent = DocumentationAgent(file_path=file_path, auth_token=auth_token)
    
    print("Добро пожаловать в систему консультации по документации!")
    print("Для выхода введите 'exit', для очистки истории введите 'clear'")
    
    conversation_history = []  # Список для хранения истории диалога

    while True:
        # Показываем историю диалога
        if conversation_history:
            print("\nИстория диалога:")
            for i, (q, a) in enumerate(conversation_history, 1):
                print(f"\n{i}. Вопрос: {q}")
                print(f"   Ответ: {a}")
        
        query = input("\nВаш вопрос: ")
        
        if query.lower() == 'exit':
            print("До свидания!")
            break
        elif query.lower() == 'clear':
            conversation_history = []
            agent.clear_conversation()
            print("История диалога очищена")
            continue
            
        response = agent.ask(query)
        # Сохраняем вопрос и ответ в историю
        conversation_history.append((query, response))
        print("\nОтвет:", response)
        
    # while True:
    #     query = input("\nВаш вопрос: ")
    #     if query.lower() == 'exit':
    #         print("До свидания!")
    #         break
    #     response = agent.ask(query)
    #     print("\nОтвет:", response)

if __name__ == "__main__":
    main()