import requests
from typing import Optional, List, Dict


class OutlineAPI:
    """
    Класс для работы с Outline Server API.
    """

    def __init__(self, api_url: str):
        # Убираем лишний слэш в конце
        self.api_url = api_url.rstrip('/')

    def _request(self, method: str, endpoint: str, data: Optional[dict] = None) -> Dict:
        """
        Вспомогательная функция для запросов к API Outline.
        """
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        headers = {'Content-Type': 'application/json'}
        response = requests.request(method, url, json=data, headers=headers, timeout=10)
        response.raise_for_status()  # выбросит исключение, если ошибка HTTP
        return response.json()

    # -------------------- Основные методы --------------------

    def list_keys(self) -> List[dict]:
        """
        Получить список всех ключей на сервере.
        """
        return self._request("GET", "access-keys")

    def create_key(self, name: str = "VPN User") -> dict:
        """
        Создать новый VPN ключ. Возвращает JSON с данными ключа.
        """
        data = {"name": name}
        return self._request("POST", "access-keys", data)

    def delete_key(self, key_id: str) -> dict:
        """
        Удалить ключ по ID.
        """
        return self._request("DELETE", f"access-keys/{key_id}")

    def update_key(self, key_id: str, name: Optional[str] = None) -> dict:
        """
        Обновить имя ключа.
        """
        data = {}
        if name:
            data["name"] = name
        return self._request("PUT", f"access-keys/{key_id}", data)
