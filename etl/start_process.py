import time
import logging
import redis
import os
import django
from django.db.utils import OperationalError

from postgres_to_es.extractor import PostgresProducer
from postgres_to_es.state import RedisStorage, State
from postgres_to_es.transform import DataTransform
from postgres_to_es.loader import ElasticsearchLoader

exceptions = (django.db.utils.OperationalError, django.db.utils.InterfaceError)
logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level="INFO")
logger = logging.getLogger(__name__)


def main_process(chunk, start_datetime, timeout):
    host = os.environ.get('REDIS_HOST', '127.0.0.1')
    port = os.environ.get('REDIS_PORT', '6379')
    r = redis.Redis(host=host, port=port, db=0)
    storage = RedisStorage(r)
    state = State(storage)
    state.set_state(key='datetime_extract', value=start_datetime)
    while True:
        logger.info('[INFO] Start ETL process.')
        etl_process(state, chunk, component='filmwork')
        etl_process(state, chunk, component='person')
        etl_process(state, chunk, component='genre')
        logger.info(f'[INFO] Timeout {timeout} sec.')
        time.sleep(timeout)


def etl_process(state, chunk, component='filmwork'):
    producer = PostgresProducer(state)
    elastic = ElasticsearchLoader()
    while True:
        movies = producer.extract(chunk, component)
        if not movies:
            break
        transform = DataTransform(movies)
        last_extract = transform.get_last_extract()
        data = transform.get_bulk()
        elastic.create_index()
        elastic.load(data)
        state.set_state(key='datetime_extract', value=str(last_extract))


if __name__ == '__main__':
    chunk = 100
    timeout = 60
    start_datetime = '2000-01-01 00:00:01'
    main_process(chunk, start_datetime, timeout)
