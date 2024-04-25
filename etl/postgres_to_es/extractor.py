import datetime
import logging
import os
import django

from django.db import close_old_connections, connections
from django.contrib.postgres.aggregates import ArrayAgg, JSONBAgg
from django.db.models import Q, Func, Value, CharField, Max, QuerySet

from typing import Literal

from postgres_to_es.backoff import backoff
from postgres_to_es.state import State

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Не переносить наверх, исполняется только после инициализации django
from movies.models import Filmwork, FilmworkPersonRoleType

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level="INFO")
logger = logging.getLogger(__name__)
exceptions = (django.db.utils.OperationalError, django.db.utils.InterfaceError,)


class PostgresProducer:
    """Класс извлекающий записи из Postgres"""
    filter_actors = Q(personfilmwork__role=FilmworkPersonRoleType.ACTOR)
    filter_directors = Q(personfilmwork__role=FilmworkPersonRoleType.DIRECTOR)
    filter_writers = Q(personfilmwork__role=FilmworkPersonRoleType.WRITER)
    func_persons = Func(
        Value("id"),
        "persons",
        Value("name"),
        "persons__full_name",
        function="jsonb_build_object",
        output_field=CharField,
    )
    annotate_fields = {
        'genres': ArrayAgg('genres__name', distinct=True),
        'actors_names': ArrayAgg('persons__full_name', distinct=True, filter=filter_actors),
        'directors_names': ArrayAgg('persons__full_name', distinct=True, filter=filter_directors),
        'writers_names': ArrayAgg('persons__full_name', distinct=True, filter=filter_writers),
        'actors': JSONBAgg(func_persons, distinct=True, filter=filter_actors),
        'directors': JSONBAgg(func_persons, distinct=True, filter=filter_directors),
        'writers': JSONBAgg(func_persons, distinct=True, filter=filter_writers),
    }

    def __init__(self, state: State) -> None:
        self.state = state

    @backoff(exceptions, 'Postgres', start_sleep_time=0.1, factor=2, border_sleep_time=10)
    def __connection(self) -> None:
        close_old_connections()
        with connections['default'].cursor():
            logger.info('[INFO] Connected to Postgres.')

    def extract(self, bulk: int, component: Literal['filmwork', 'person', 'genre']) -> QuerySet[Filmwork]:
        """Общий метод извлечения данных"""
        films = None
        self.__connection()
        last_updated_at = self.state.get_state('datetime_extract')
        logger.info(f'[INFO] Extract last updates from {component}.')
        if component == 'filmwork':
            films = self.__extract_change_fimwork(bulk, last_updated_at)
        elif component == 'person':
            films = self.__extract_change_person(bulk, last_updated_at)
        elif component == 'genre':
            films = self.__extract_change_genre(bulk, last_updated_at)
        return films

    def __extract_change_fimwork(self, bulk: int, last_updated_at: datetime.datetime) -> QuerySet[Filmwork]:
        return Filmwork.objects.filter(updated_at__gt=last_updated_at).values(
            'id', 'rating', 'title', 'description', 'updated_at'
        ).annotate(**self.annotate_fields).order_by('updated_at')[:bulk]

    def __extract_change_person(self, bulk: int, last_updated_at: datetime.datetime) -> QuerySet[Filmwork]:
        return Filmwork.objects.filter(
            personfilmwork__person__updated_at__gt=last_updated_at).values(
            'id', 'rating', 'title', 'description',
        ).annotate(**self.annotate_fields).annotate(
            updated_at=Max('persons__updated_at'),
        ).order_by('updated_at')[:bulk]

    def __extract_change_genre(self, bulk: int, last_updated_at: datetime.datetime) -> QuerySet[Filmwork]:
        return Filmwork.objects.filter(genrefilmwork__genre__updated_at__gt=last_updated_at).values(
            'id', 'rating', 'title', 'description',
        ).annotate(**self.annotate_fields).annotate(
            updated_at=Max('genrefilmwork__genre__updated_at'),
        ).order_by('updated_at')[:bulk]
