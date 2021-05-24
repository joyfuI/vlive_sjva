import os
import re
import time
from threading import Thread

import requests

from framework.logger import get_logger

from .model import ModelSetting, ModelScheduler
from .logic_queue import LogicQueue
from .api_youtube_dl import APIYoutubeDL

package_name = __name__.split('.')[0]
logger = get_logger(package_name)


class LogicNormal(object):
    download_list = set()

    @staticmethod
    def scheduler_function():
        for scheduler in ModelScheduler.get_list():
            if not scheduler.is_live:
                continue
            logger.debug('scheduler download %s', scheduler.url)
            video_url = LogicNormal.get_first_live_video(scheduler.url)  # 첫번째 영상
            if video_url is None or video_url in LogicNormal.download_list:
                continue
            download = APIYoutubeDL.download(package_name, scheduler.key, video_url, filename=scheduler.filename,
                                             save_path=scheduler.save_path, start=True,
                                             cookiefile=ModelSetting.get('cookiefile_path'))
            scheduler.update(LogicNormal.get_count_video(scheduler.url))  # 임시
            if download['errorCode'] == 0:
                LogicNormal.download_list.add(video_url)
                Thread(target=LogicNormal.download_check_function,
                       args=(video_url, download['index'], scheduler.key)).start()
                scheduler.update()
            else:
                logger.debug('scheduler download fail %s', download['errorCode'])

    @staticmethod
    def download_check_function(url, index, key):
        time.sleep(10)  # 10초 대기
        status = APIYoutubeDL.status(package_name, index, key)
        if status['status'] == 'ERROR':
            LogicNormal.download_list.remove(url)

    @staticmethod
    def download(form):
        options = {
            'save_path': form['save_path'],
            'filename': form['filename'],
        }
        for i in form.getlist('download[]'):
            LogicQueue.add_queue(i, options)
        return len(form.getlist('download[]'))

    @staticmethod
    def get_scheduler():
        scheduler_list = []
        for i in ModelScheduler.get_list(True):
            i['last_time'] = i['last_time'].strftime('%m-%d %H:%M:%S')
            i['path'] = os.path.join(i['save_path'], i['filename'])
            scheduler_list.append(i)
        return scheduler_list

    @staticmethod
    def add_scheduler(form):
        if form['db_id']:
            data = {
                'save_path': form['save_path'],
                'filename': form['filename'],
                'is_live': True
                # 'is_live': bool(form['is_live']) if str(form['is_live']).lower() != 'false' else False
            }
            ModelScheduler.find(form['db_id']).update(data)
        else:
            info_dict = APIYoutubeDL.info_dict(package_name, form['url'])['info_dict']
            if info_dict is None or info_dict.get('extractor_key') != 'VLiveChannel':
                return None
            data = {
                'webpage_url': info_dict['webpage_url'],
                'title': info_dict['title'],
                'count': len(info_dict['entries']),
                'save_path': form['save_path'],
                'filename': form['filename'],
                'is_live': True
                # 'is_live': bool(form['is_live']) if str(form['is_live']).lower() != 'false' else False
            }
            ModelScheduler.create(data)
        return LogicNormal.get_scheduler()

    @staticmethod
    def del_scheduler(db_id):
        logger.debug('del_scheduler %s', db_id)
        ModelScheduler.find(db_id).delete()
        return LogicNormal.get_scheduler()

    @staticmethod
    def get_first_live_video(channel_url):
        channel_id = channel_url.split('/')[-1]
        url = 'https://www.vlive.tv/globalv-web/vam-web/post/v1.0/channel-%s/starPosts' % channel_id
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
    def get_count_video(channel_url):
        html = requests.get(channel_url).text
        pattern = re.compile(r'"videoCountOfStar":(\d+)')
        return int(pattern.findall(html)[0])

    @staticmethod
    def get_recent_html():
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
