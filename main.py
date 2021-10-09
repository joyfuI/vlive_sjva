from typing import Optional
import traceback
import os
import sqlite3
import time
import re
from threading import Thread

from flask import render_template, jsonify
import requests

from framework import path_data, scheduler, app, db, celery
from framework.common.plugin import LogicModuleBase, default_route_socketio

from .plugin import P
from .logic_queue import LogicQueue
from .model import ModelScheduler
from .api_youtube_dl import APIYoutubeDL

logger = P.logger
package_name = P.package_name
ModelSetting = P.ModelSetting


class LogicMain(LogicModuleBase):
    db_default = {
        'db_version': '2',
        f'{package_name}_interval': '* * * * *',
        f'{package_name}_auto_start': 'False',
        'default_save_path': os.path.join(path_data, 'download', package_name),
        'default_filename': '%(title)s.%(id)s.%(ext)s',
        'cookiefile_path': ''
    }

    def __init__(self, p):
        super(LogicMain, self).__init__(p, None, scheduler_desc='V LIVE 새로운 영상 다운로드')
        self.name = package_name  # 모듈명
        default_route_socketio(p, self)

    def plugin_load(self):
        try:
            LogicQueue.queue_load()
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    def process_menu(self, sub, req):
        try:
            arg = {
                'package_name': package_name,
                'sub': package_name,
                'template_name': f'{package_name}_{sub}'
            }

            if sub == 'setting':
                arg.update(ModelSetting.to_dict())
                job_id = f'{self.P.package_name}_{self.name}'
                arg['scheduler'] = str(scheduler.is_include(job_id))
                arg['is_running'] = str(scheduler.is_running(job_id))
                arg['path_data'] = path_data

            elif sub == 'recent':
                arg['url'] = req.args.get('url', '')
                arg['recent_html'] = LogicMain.get_recent_html()
                arg['save_path'] = ModelSetting.get('default_save_path')
                arg['filename'] = ModelSetting.get('default_filename')

            elif sub == 'scheduler':
                arg['save_path'] = ModelSetting.get('default_save_path')
                arg['filename'] = ModelSetting.get('default_filename')

            return render_template(f'{package_name}_{sub}.html', arg=arg)
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            return render_template('sample.html', title=f'{package_name} - {sub}')

    def process_ajax(self, sub, req):
        try:
            logger.debug('AJAX: %s, %s', sub, req.values)
            ret = {'ret': 'success'}

            if sub == 'add_download':
                ret['msg'] = f'{LogicMain.download(req.form)}개를 큐에 추가하였습니다.'

            elif sub == 'list_scheduler':
                ret['data'] = LogicMain.get_scheduler()

            elif sub == 'add_scheduler':
                if LogicMain.add_scheduler(req.form):
                    ret['msg'] = '스케줄을 저장하였습니다.'
                else:
                    ret['ret'] = 'warning'
                    ret['msg'] = 'V LIVE 채널을 분석하지 못했습니다.'

            elif sub == 'del_scheduler':
                LogicMain.del_scheduler(req.form['id'])
                ret['msg'] = '삭제하였습니다.'

            return jsonify(ret)
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            return jsonify({'ret': 'danger', 'msg': str(e)})

    def scheduler_function(self):
        if app.config['config']['use_celery']:
            result = LogicMain.task.apply_async()
            result.get()
        else:
            LogicMain.task()

    def migration(self):
        try:
            db_version = ModelSetting.get_int('db_version')
            connect = sqlite3.connect(os.path.join(path_data, 'db', f'{package_name}.db'))

            if db_version < 2:
                cursor = connect.cursor()
                cursor.execute(f"SELECT * FROM {package_name}_setting WHERE key = 'interval'")
                interval = cursor.fetchone()[2]
                cursor.execute(f"UPDATE {package_name}_setting SET value = ? WHERE key = '{package_name}_interval'",
                               (interval,))
                cursor.execute(f"DELETE FROM {package_name}_setting WHERE key = 'interval'")
                cursor.execute(f"SELECT * FROM {package_name}_setting WHERE key = 'auto_start'")
                auto_start = cursor.fetchone()[2]
                cursor.execute(f"UPDATE {package_name}_setting SET value = ? WHERE key = '{package_name}_auto_start'",
                               (auto_start,))
                cursor.execute(f"DELETE FROM {package_name}_setting WHERE key = 'auto_start'")

            connect.commit()
            connect.close()
            ModelSetting.set('db_version', LogicMain.db_default['db_version'])
            db.session.flush()
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    @staticmethod
    @celery.task
    def task():
        try:
            for entity in ModelScheduler.get_list():
                if not entity.is_live:
                    continue
                logger.debug('scheduler download %s', entity.url)
                video_url = LogicMain.get_first_live_video(entity.url)  # 첫번째 영상
                if video_url is None or video_url in LogicMain.download_list:
                    continue
                download = APIYoutubeDL.download(package_name, entity.key, video_url, filename=entity.filename,
                                                 save_path=entity.save_path, start=True,
                                                 cookiefile=ModelSetting.get('cookiefile_path'))
                entity.update(LogicMain.get_count_video(entity.url))  # 임시
                if download['errorCode'] == 0:
                    LogicMain.download_list.add(video_url)
                    Thread(target=LogicMain.download_check_function,
                           args=(video_url, download['index'], entity.key)).start()
                    entity.update()
                else:
                    logger.debug('scheduler download fail %s', download['errorCode'])
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    download_list = set()

    @staticmethod
    def download_check_function(url: str, index: int, key: str):
        time.sleep(10)  # 10초 대기
        status = APIYoutubeDL.status(package_name, index, key)
        if status['status'] == 'ERROR':
            LogicMain.download_list.remove(url)

    @staticmethod
    def download(form) -> int:
        options = {
            'save_path': form['save_path'],
            'filename': form['filename'],
        }
        for i in form.getlist('download[]'):
            LogicQueue.add_queue(i, options)
        return len(form.getlist('download[]'))

    @staticmethod
    def get_scheduler() -> list[dict]:
        scheduler_list = []
        for i in ModelScheduler.get_list(True):
            i['last_time'] = i['last_time'].strftime('%m-%d %H:%M:%S')
            i['path'] = os.path.join(i['save_path'], i['filename'])
            scheduler_list.append(i)
        return scheduler_list

    @staticmethod
    def add_scheduler(form) -> bool:
        if form['db_id']:
            data = {
                'save_path': form['save_path'],
                'filename': form['filename'],
                'is_live': True
                # 'is_live': bool(form['is_live']) if str(form['is_live']).lower() != 'false' else False
            }
            ModelScheduler.find(form['db_id']).update(data)
        else:
            info_dict = LogicMain.get_channel_info(form['url'])
            if info_dict is None:
                return False
            data = {
                'webpage_url': info_dict['webpage_url'],
                'title': info_dict['title'],
                'count': info_dict['count'],
                'save_path': form['save_path'],
                'filename': form['filename'],
                'is_live': True
                # 'is_live': bool(form['is_live']) if str(form['is_live']).lower() != 'false' else False
            }
            ModelScheduler.create(data)
        return True

    @staticmethod
    def del_scheduler(db_id: int):
        logger.debug('del_scheduler %s', db_id)
        ModelScheduler.find(db_id).delete()

    @staticmethod
    def get_channel_info(channel_url: str) -> Optional[dict]:
        channel_id = channel_url.split('/')[-1]
        url = f'https://www.vlive.tv/globalv-web/vam-web/member/v1.0/channel-{channel_id}/officialProfiles'
        params = {
            'appId': '8c6cc7b45d2568fb668be6e05b6e5a3b',
            'fields': 'officialName',
            'types': 'STAR',
            'gcc': 'KR',
            'locale': 'ko_KR'
        }
        headers = {
            'Referer': 'https://www.vlive.tv/'
        }
        try:
            json = requests.get(url, params=params, headers=headers).json()[0]
        except (IndexError, KeyError):
            # 잘못된 channel_id 등의 이유로 엉뚱한 값이 반환되면
            return None
        channel_info = {
            'webpage_url': f'https://www.vlive.tv/channel/{channel_id}',
            'title': json['officialName'],
            'count': LogicMain.get_count_video(channel_url),
        }
        return channel_info

    @staticmethod
    def get_first_live_video(channel_url: str) -> Optional[str]:
        channel_id = channel_url.split('/')[-1]
        url = f'https://www.vlive.tv/globalv-web/vam-web/post/v1.0/channel-{channel_id}/starPosts'
        params = {
            'appId': '8c6cc7b45d2568fb668be6e05b6e5a3b',
            'fields': 'contentType,officialVideo,title,url',
            'gcc': 'KR',
            'locale': 'ko_KR',
            'pageSize': 5
        }
        headers = {
            'Referer': 'https://www.vlive.tv/'
        }
        json = requests.get(url, params=params, headers=headers).json()
        video_url = None
        for data in json['data']:
            if data['contentType'] == 'VIDEO':
                if data['officialVideo']['type'] == 'LIVE':
                    video_url = data['url']
                    break
        return video_url

    @staticmethod
    def get_count_video(channel_url: str) -> int:
        html = requests.get(channel_url).text
        pattern = re.compile(r'"videoCountOfStar":(\d+)')
        return int(pattern.findall(html)[0])

    @staticmethod
    def get_recent_html() -> str:
        url = 'https://www.vlive.tv/home/video/more'
        params = {
            'viewType': 'recent',
            'pageSize': 20,
            'pageNo': 1,
        }
        headers = {
            'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3'
        }
        html = requests.get(url, params=params, headers=headers).text
        html = re.sub(r'href="(.+?)"', r'href="https://www.vlive.tv\1"', html)
        html = re.sub(r'onclick="vlive.tv.common.videoGa\(this\);"', r'onclick="link_click(this); return false;"', html)
        html = re.sub(r'onclick="vlive.tv.common.chGa\(this\);"|onerror="(.+?)"', '', html)
        return html
