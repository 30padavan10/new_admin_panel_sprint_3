import time
import logging
from functools import wraps
from typing import Tuple

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level="INFO")
logger = logging.getLogger(__name__)


def backoff(exceptions: Tuple, service: str, start_sleep_time=0.1, factor=2, border_sleep_time=10):
    """
    Функция для повторного выполнения функции через некоторое время, если возникла ошибка. Использует наивный
     экспоненциальный рост времени повтора (factor) до граничного времени ожидания (border_sleep_time)
    :param exceptions: перехватываемые исключения
    :param service: сервис для которого будет применяться функция
    :param start_sleep_time: начальное время ожидания
    :param factor: во сколько раз нужно увеличивать время ожидания на каждой итерации
    :param border_sleep_time: максимальное время ожидания
    :return: результат выполнения функции
    """

    def func_wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            sleep_time = start_sleep_time
            while True:
                logger.info(f'[INFO] Try connect to {service} (interval {sleep_time} sec)')
                try:
                    if sleep_time * factor < border_sleep_time:
                        sleep_time *= factor
                    else:
                        sleep_time = border_sleep_time
                    time.sleep(sleep_time)
                    res = func(*args, **kwargs)
                except exceptions:
                    logger.error(f'[ERROR] {service} is not availlable.')
                else:
                    break
            return res
        return inner
    return func_wrapper
