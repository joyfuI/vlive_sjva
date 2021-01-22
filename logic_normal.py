# -*- coding: utf-8 -*-
#########################################################
# python
import os
import re

# third-party
import requests

# sjva 공용
from framework import path_data

# 패키지
from .plugin import logger, package_name
from .model import ModelScheduler
from .api_youtube_dl import APIYoutubeDL
#########################################################

class LogicNormal(object):
    download_list = {}

    @staticmethod
    def scheduler_function():
        for i in ModelScheduler.get_list():
            if not i.is_live:
                continue
            logger.debug('scheduler download %s', i.url)
            video_url = LogicNormal.get_first_video(i.url)  # 첫번째 영상
            if video_url is None:
                continue
            ModelScheduler.find(i.id).update(LogicNormal.get_count_video(i.url))  # 임시
            info_dict = APIYoutubeDL.info_dict(package_name, video_url)['info_dict']
            if info_dict is None or info_dict['id'] in LogicNormal.download_list:
                continue
            if info_dict.get('is_live'):
                LogicNormal.download_list[info_dict['id']] = None
                APIYoutubeDL.download(package_name, i.key, video_url, i.filename, i.save_path, None, None, None, None,
                                      None, None, True)

    @staticmethod
    def scheduler_function2():
        from .logic_queue import LogicQueue

        for i in ModelScheduler.get_list():
            if i.is_live:
                continue
            logger.debug('scheduler download %s', i.url)
            info_dict = APIYoutubeDL.info_dict(package_name, i.url)['info_dict']
            if info_dict is None or info_dict.get('extractor_key') != 'VLiveChannel':
                continue
            ModelScheduler.find(i.id).update(len(info_dict['entries']))
            options = {
                'save_path': i.save_path,
                'filename': i.filename,
                'archive': os.path.join(path_data, 'db', package_name, '%d.txt' % i.id)
            }
            LogicQueue.add_queue(i.url, options)

    @staticmethod
    def analysis(url):
        return APIYoutubeDL.info_dict(package_name, url)

    @staticmethod
    def download(form):
        from .logic_queue import LogicQueue

        options = {
            'save_path': form['save_path'],
            'filename': form['filename'],
            'archive': None
        }
        for i in form.getlist('download[]'):
            LogicQueue.add_queue(i, options)
        return len(form.getlist('download[]'))

    @staticmethod
    def get_scheduler():
        ret = []
        for i in ModelScheduler.get_list(True):
            i['last_time'] = i['last_time'].strftime('%m-%d %H:%M:%S')
            i['path'] = os.path.join(i['save_path'], i['filename'])
            ret.append(i)
        return ret

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
            ret = APIYoutubeDL.info_dict(package_name, form['url'])['info_dict']
            if ret is None or ret.get('extractor_key') != 'VLiveChannel':
                return None
            data = {
                'webpage_url': ret['webpage_url'],
                'title': ret['title'],
                'count': len(ret['entries']),
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
        LogicNormal.del_archive(db_id)
        return LogicNormal.get_scheduler()

    @staticmethod
    def del_archive(db_id):
        archive = os.path.join(path_data, 'db', package_name, '%s.txt' % db_id)
        logger.debug('delete %s', archive)
        if os.path.isfile(archive):
            os.remove(archive)

    @staticmethod
    def get_first_video(channel_url):
        channel_id = channel_url.split('/')[-1]
        url = 'https://www.vlive.tv/globalv-web/vam-web/post/v1.0/channel-%s/starPosts' % channel_id
        params = {
            'appId': '8c6cc7b45d2568fb668be6e05b6e5a3b',
            'fields': 'contentType,title,url',
            'gcc': 'KR',
            'locale': 'ko_KR'
        }
        headers = {
            'Referer': 'https://www.vlive.tv/'
        }
        json = requests.get(url, params=params, headers=headers).json()
        video_url = None
        for data in json['data']:
            if data['contentType'] == 'VIDEO':
                video_url = data['url']
                break
        return video_url

    @staticmethod
    def get_count_video(channel_url):
        html = requests.get(channel_url).text
        pattern = re.compile(r'"videoCountOfStar":(\d+)')
        return int(pattern.findall(html)[0])