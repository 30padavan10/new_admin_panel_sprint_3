import abc
import json
import redis
from typing import Any, Dict


class BaseStorage(abc.ABC):
    """Абстрактное хранилище состояния.

    Позволяет сохранять и получать состояние.
    Способ хранения состояния может варьироваться в зависимости
    от итоговой реализации. Например, можно хранить информацию
    в базе данных или в распределённом файловом хранилище.
    """

    @abc.abstractmethod
    def save_state(self, state: Dict[str, Any]) -> None:
        """Сохранить состояние в хранилище."""

    @abc.abstractmethod
    def retrieve_state(self) -> Dict[str, Any]:
        """Получить состояние из хранилища."""


class RedisStorage(BaseStorage):
    """хранилище состояния в Redis"""
    def __init__(self, redis_adapter: redis.Redis):
        self.redis_adapter = redis_adapter

    def save_state(self, state: Dict[str, Any]) -> None:
        """Сохранить состояние в хранилище."""
        self.redis_adapter.mset(state)

    def retrieve_state(self) -> Dict[str, Any]:
        """Получить состояние из хранилища."""
        try:
            state = {i.decode("utf-8"): self.redis_adapter.get(i).decode("utf-8") for i in self.redis_adapter.keys()}
            return state
        except redis.exceptions.ConnectionError:
            return {}


class State:
    """Класс для работы с состояниями."""

    def __init__(self, storage: BaseStorage) -> None:
        self.storage = storage
        self.local_storage = storage.retrieve_state()

    def set_state(self, key: str, value: Any) -> None:
        """Установить состояние для определённого ключа."""
        self.local_storage.update({key: value})
        self.storage.save_state(self.local_storage)

    def get_state(self, key: str) -> Any:
        """Получить состояние по определённому ключу."""
        return self.local_storage.get(key)
