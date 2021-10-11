import traceback
import time
from threading import Thread

from .plugin import P
from .model import ModelQueue
from .api_youtube_dl import APIYoutubeDL

logger = P.logger
package_name = P.package_name
ModelSetting = P.ModelSetting


class LogicQueue(object):
    _thread = None

    @staticmethod
    def queue_load():
        Thread(target=LogicQueue.queue_start).start()

    @staticmethod
    def queue_start():
        try:
            time.sleep(10)  # youtube-dl 플러그인이 언제 로드될지 모르니 일단 10초 대기
            for i in ModelQueue.get_list():
                logger.debug('queue add %s', i.url)
                download = APIYoutubeDL.download(package_name, i.key, i.url, filename=i.filename, save_path=i.save_path,
                                                 start=False, cookiefile=ModelSetting.get('cookiefile_path'))
                if download['errorCode'] == 0:
                    i.set_index(download['index'])
                else:
                    logger.debug('queue add fail %s', download['errorCode'])
                    i.delete()

            LogicQueue._thread = Thread(target=LogicQueue.thread_function)
            LogicQueue._thread.daemon = True
            LogicQueue._thread.start()
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    @staticmethod
    def thread_function():
        try:
            while not ModelQueue.is_empty():
                entity = ModelQueue.peek()
                logger.debug('queue download %s', entity.url)
                start = APIYoutubeDL.start(package_name, entity.index, entity.key)
                if start['errorCode'] == 0:
                    while True:
                        time.sleep(10)  # 10초 대기
                        status = APIYoutubeDL.status(package_name, entity.index, entity.key)
                        if status['status'] in ('COMPLETED', 'ERROR', 'STOP'):
                            break
                else:
                    logger.debug('queue download fail %s', start['errorCode'])
                entity.delete()
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    @staticmethod
    def add_queue(url: str, options: dict):
        try:
            options['webpage_url'] = url
            entity = ModelQueue.create(options)
            download = APIYoutubeDL.download(package_name, entity.key, url, filename=entity.filename,
                                             save_path=entity.save_path, start=False,
                                             cookiefile=ModelSetting.get('cookiefile_path'))
            if download['errorCode'] == 0:
                entity.set_index(download['index'])
            else:
                logger.debug('queue add fail %s', download['errorCode'])
                entity.delete()
                return None

            if not LogicQueue._thread.is_alive():
                LogicQueue._thread = Thread(target=LogicQueue.thread_function)
                LogicQueue._thread.daemon = True
                LogicQueue._thread.start()
            return entity
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            return None
