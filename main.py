from documentation_agent import DocumentationAgent

def main():
    file_path = 'file.txt'
    auth_token = 'MmMzZDA5OGMtODIyNS00MGJlLWJhOGItMzRhOTgyY2M0YjBhOjk3NGQ0ZTA3LWQ3MDUtNDhhNC1iYjFlLTQ0N2Y2ZmJkMWM4Mg=='

    try:
        agent = DocumentationAgent(file_path, auth_token)
        agent.interactive_mode()
    except Exception as e:
        print(f"Произошла ошибка при инициализации агента: {str(e)}")

if __name__ == "__main__":
    main()