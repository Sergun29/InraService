import requests
import os
from base64 import b64encode
from dotenv import load_dotenv

# Базовый URL API ИнтраСервис
BASE_URL = "http://ap1711.intraservice.ru/api"

def get_user_id_by_email(email: str) -> int:
    """
    Возвращает ID пользователя по его email.
    """
    url = f"{BASE_URL}/user"
    
    # Загружаем логин и пароль из файла .env
    load_dotenv()
    username = os.getenv('INTRASERVICE_LOGIN')
    password = os.getenv('INTRASERVICE_PASSWORD')
    
    if not username or not password:
        print("Ошибка: Не заданы INTRASERVICE_LOGIN или INTRASERVICE_PASSWORD в .env")
        return None
        
    # Формируем заголовок авторизации
    auth_b64 = b64encode(f"{username}:{password}".encode()).decode()
    headers = {
        'Authorization': f'Basic {auth_b64}',
        'Accept': 'application/json'
    }
    
    # Формируем параметры запроса:
    # Ищем по email и просим вернуть только поле Id
    params = {
        'email': email,
        'fields': 'Id'
    }
    
    try:
        # Отправляем GET-запрос
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        users = data.get('Users', [])
        
        if not users:
            print(f"Пользователь с email {email} не найден.")
            return None
            
        # Возвращаем ID первого найденного пользователя
        return users[0].get('Id')
        
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при обращении к API: {e}")
        return None

if __name__ == "__main__":
    # Пример использования:
    user_id = get_user_id_by_email("it.chieforv@aptekaf.ru")
    if user_id:
        print(f"ID пользователя: {user_id}")