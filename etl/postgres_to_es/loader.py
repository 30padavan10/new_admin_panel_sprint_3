import requests
import logging
import json
import os

from http import HTTPStatus
from postgres_to_es.backoff import backoff

exceptions = (requests.exceptions.ConnectionError, )
logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level="INFO")
logger = logging.getLogger(__name__)


class ElasticsearchLoader:
    headers = {'Content-Type': 'application/json'}
    host = os.environ.get('ES_HOST', '127.0.0.1')
    port = os.environ.get('ES_PORT', '9200')

    @backoff(exceptions, 'ES', start_sleep_time=0.1, factor=2, border_sleep_time=10)
    def create_index(self) -> None:
        """Создание индекса в Elastic"""
        with open('postgres_to_es/index.json') as json_data:
            data = json.load(json_data)
        url = f'http://{self.host}:{self.port}/movies'
        req = requests.put(url, verify=False, headers=self.headers, json=data)
        if req.status_code == HTTPStatus.OK:
            logger.info('[INFO] Index ES created.')
        else:
            logger.info('[INFO] Index ES exist.')

    @backoff(exceptions, 'ES', start_sleep_time=0.1, factor=2, border_sleep_time=10)
    def load(self, data: str) -> None:
        """Загрузка пачки данных в Elastic"""
        url = f'http://{self.host}:{self.port}/movies/_bulk'
        req = requests.post(url, verify=False, headers=self.headers, data=data.encode('utf-8'))
        if req.status_code == HTTPStatus.OK:
            logger.info('[INFO] Data loaded to ES.')
        else:
            logger.error('[ERROR] Data not loaded to ES.')
