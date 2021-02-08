# -*- coding: utf-8 -*-
#########################################################
# python
import os
import time
import traceback
from threading import Thread

# third-party

# sjva 공용

# 패키지
from .plugin import package_name, logger
from .model import ModelScheduler, ModelQueue
from .logic_normal import LogicNormal
from .api_youtube_dl import APIYoutubeDL
#########################################################

class LogicQueue(object):
    __thread = None

    @staticmethod
    def queue_load():
        Thread(target=LogicQueue.queue_start).start()

    @staticmethod
    def queue_start():
        try:
            time.sleep(10)  # youtube-dl 플러그인이 언제 로드될지 모르니 일단 10초 대기
            for i in ModelQueue.get_list():
                logger.debug('queue add %s', i.url)
                if i.archive:
                    scheduler_id = os.path.splitext(os.path.basename(i.archive))[0]
                    LogicNormal.download_list[scheduler_id] = None
                ret = APIYoutubeDL.download(package_name, i.key, i.url, filename=i.filename, save_path=i.save_path,
                                            archive=i.archive, start=False)
                if ret['errorCode'] == 0:
                    i.set_index(ret['index'])
                else:
                    logger.debug('queue add fail %s', ret['errorCode'])
                    i.delete()

            LogicQueue.__thread = Thread(target=LogicQueue.thread_function)
            LogicQueue.__thread.daemon = True
            LogicQueue.__thread.start()
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    @staticmethod
    def thread_function():
        try:
            while not ModelQueue.is_empty():
                entity = ModelQueue.peek()
                logger.debug('queue download %s', entity.url)
                ret = APIYoutubeDL.start(package_name, entity.index, entity.key)
                if ret['errorCode'] == 0:
                    while True:
                        time.sleep(10)  # 10초 대기
                        ret = APIYoutubeDL.status(package_name, entity.index, entity.key)
                        if ret['status'] == 'COMPLETED':
                            if entity.archive:
                                scheduler_id = os.path.splitext(os.path.basename(entity.archive))[0]
                                ModelScheduler.find(scheduler_id).update()
                            break
                        elif ret['status'] in ('ERROR', 'STOP'):
                            break
                else:
                    logger.debug('queue download fail %s', ret['errorCode'])
                if entity.archive:
                    scheduler_id = os.path.splitext(os.path.basename(entity.archive))[0]
                    del LogicNormal.download_list[scheduler_id]
                entity.delete()
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    @staticmethod
    def add_queue(url, options):
        try:
            options['webpage_url'] = url
            entity = ModelQueue.create(options)
            if entity.archive:
                scheduler_id = os.path.splitext(os.path.basename(entity.archive))[0]
                LogicNormal.download_list[scheduler_id] = None
            ret = APIYoutubeDL.download(package_name, entity.key, url, filename=entity.filename,
                                        save_path=entity.save_path, archive=entity.archive, start=False)
            if ret['errorCode'] == 0:
                entity.set_index(ret['index'])
            else:
                logger.debug('queue add fail %d', ret['errorCode'])
                entity.delete()
                return None

            if not LogicQueue.__thread.is_alive():
                LogicQueue.__thread = Thread(target=LogicQueue.thread_function)
                LogicQueue.__thread.daemon = True
                LogicQueue.__thread.start()
            return entity
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            return None
