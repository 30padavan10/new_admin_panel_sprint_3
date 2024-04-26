import uuid
import logging
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Union
from django.db.models import QuerySet
from movies.models import Filmwork

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level="INFO")
logger = logging.getLogger(__name__)


class Person(BaseModel):
    id: uuid.UUID
    name: str


class Movie(BaseModel):
    id: uuid.UUID
    imdb_rating: Optional[float] = Field(alias='rating')
    genres: list[Union[str, None]]
    title: str
    description: Optional[str]
    directors_names: list[str]
    actors_names: list[str]
    writers_names: list[str]
    directors: list[Person]
    actors: list[Person]
    writers: list[Person]
    updated_at: datetime


class DataTransform:
    """Класс преобразует QuerySet в json для записи в ES"""
    def __init__(self, movies: QuerySet[Filmwork]):
        self.movies = [Movie.parse_obj(movie) for movie in movies]

    def get_bulk(self) -> str:
        count = self._count()
        logger.info(f'[INFO] {count} entities transformed from Postgres to ES')
        bulk = []
        for movie in self.movies:
            bulk.append('{"index": {"_index": "movies", "_id": "%s"}}' % (movie.id))
            bulk.append(movie.json(exclude={'updated_at'}))
        return '\n'.join(bulk) + '\n'

    def get_last_extract(self) -> datetime:
        if self.movies:
            return self.movies[-1].updated_at

    def _count(self) -> int:
        if self.movies:
            return len(self.movies)
