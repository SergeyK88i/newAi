import requests
import uuid
import json
import os
os.environ['token']='MmMzZDA5OGMtODIyNS00MGJlLWJhOGItMzRhOTgyY2M0YjBhOjk3NGQ0ZTA3LWQ3MDUtNDhhNC1iYjFlLTQ0N2Y2ZmJkMWM4Mg=='

class GigaChatAPI:
    def __init__(self):
        self.access_token = None
        self.conversation_history = []
        
    def get_token(self, auth_token, scope='GIGACHAT_API_PERS'):
        rq_uid = str(uuid.uuid4())
        url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'RqUID': rq_uid,
            'Authorization': f'Basic {auth_token}'
        }
        payload = {
            'scope': scope
        }

        try:
            response = requests.post(url, headers=headers, data=payload, verify=False)
            if response.status_code == 200:
                self.access_token = response.json()['access_token']
            return response
        except requests.RequestException as e:
            print(f"Ошибка: {str(e)}")
            return None

    def get_chat_completion(self, system_message, user_message):
        if not self.access_token:
            print("Ошибка: Токен доступа не получен. Сначала вызовите метод get_token().")
            return None

        # Формируем сообщения с учетом истории
        messages = [
            {"role": "system", "content": system_message}
        ]
        
        # Добавляем историю предыдущих сообщений
        messages.extend(self.conversation_history)

        # Добавляем текущий вопрос
        messages.append({"role": "user", "content": user_message})

        url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
        payload = json.dumps({
            "model": "GigaChat",
            "messages": messages,
            "temperature": 1,
            "top_p": 0.1,
            "n": 1,
            "stream": False,
            "max_tokens": 512,
            "repetition_penalty": 1,
            "update_interval": 0
        })
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.access_token}'
        }

        try:
            response = requests.post(url, headers=headers, data=payload, verify=False)
            if response.status_code == 200:
                # Сохраняем вопрос и ответ в историю
                self.conversation_history.append({"role": "user", "content": user_message})
                assistant_response = response.json()['choices'][0]['message']['content']
                self.conversation_history.append({"role": "assistant", "content": assistant_response})
            return response
        except requests.RequestException as e:
            print(f"Произошла ошибка: {str(e)}")
            return None
    def clear_history(self):
        """Очистка истории диалога"""
        self.conversation_history = []