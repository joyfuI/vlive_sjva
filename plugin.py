import os
import traceback

from flask import Blueprint

from framework import app, path_data
from framework.logger import get_logger
from framework.util import Util
from framework.common.plugin import get_model_setting, Logic, default_route_single_module


class P(object):
    package_name = __name__.split('.')[0]
    logger = get_logger(package_name)
    blueprint = Blueprint(package_name, package_name, url_prefix=f'/{package_name}',
                          template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
                          static_folder=os.path.join(os.path.dirname(__file__), 'static'))

    # 메뉴 정의
    menu = {
        'main': [package_name, 'V LIVE'],
        'sub': [
            ['setting', '설정'], ['recent', '최근 방송'], ['scheduler', '스케줄링'], ['log', '로그']
        ],
        'category': 'vod'
    }

    plugin_info = {
        'version': '2.0.0',
        'name': package_name,
        'category_name': 'vod',
        'icon': '',
        'developer': 'joyfuI',
        'description': 'V LIVE 다운로드',
        'home': f'https://github.com/joyfuI/{package_name}',
        'more': '',
    }

    ModelSetting = get_model_setting(package_name, logger)
    logic = None
    module_list = None
    home_module = 'recent'  # 기본모듈


def initialize():
    try:
        app.config['SQLALCHEMY_BINDS'][
            P.package_name] = f"sqlite:///{os.path.join(path_data, 'db', f'{P.package_name}.db')}"
        Util.save_from_dict_to_json(P.plugin_info, os.path.join(os.path.dirname(__file__), 'info.json'))

        # 로드할 모듈 정의
        from .main import LogicMain
        P.module_list = [LogicMain(P)]

        P.logic = Logic(P)
        default_route_single_module(P)
    except Exception as e:
        P.logger.error('Exception:%s', e)
        P.logger.error(traceback.format_exc())


logger = P.logger
initialize()
