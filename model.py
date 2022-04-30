import traceback
import random
import string
from datetime import datetime

from framework import db

from .plugin import P

logger = P.logger
package_name = P.package_name


class ModelScheduler(db.Model):
    __tablename__ = f"{package_name}_scheduler"
    __table_args__ = {"mysql_collate": "utf8_general_ci"}
    __bind_key__ = package_name

    id = db.Column(db.Integer, primary_key=True)
    last_time = db.Column(db.DateTime, nullable=False)
    url = db.Column(db.String, nullable=False)
    title = db.Column(db.String)
    count = db.Column(db.Integer, nullable=False)
    save_path = db.Column(db.String, nullable=False)
    filename = db.Column(db.String, nullable=False)
    is_live = db.Column(db.Boolean, nullable=False)
    key = db.Column(db.String)

    def __init__(self, data):
        self.last_time = datetime.now()
        self.url = data["webpage_url"]
        self.title = data["title"]
        self.count = data["count"]
        self.save_path = data["save_path"]
        self.filename = data["filename"]
        self.is_live = data["is_live"]
        self.key = "".join([random.choice(string.ascii_lowercase) for _ in range(5)])

    def __repr__(self):
        return repr(self.as_dict())

    def as_dict(self) -> dict:
        return {x.name: getattr(self, x.name) for x in self.__table__.columns}

    @staticmethod
    def get_list(by_dict: bool = False):
        try:
            tmp = db.session.query(ModelScheduler).all()
            if by_dict:
                tmp = [x.as_dict() for x in tmp]
            return tmp
        except Exception as e:
            logger.error("Exception:%s", e)
            logger.error(traceback.format_exc())

    @staticmethod
    def find(db_id: int):
        try:
            return db.session.query(ModelScheduler).filter_by(id=db_id).first()
        except Exception as e:
            logger.error("Exception:%s %s", e, db_id)
            logger.error(traceback.format_exc())

    @staticmethod
    def create(data: dict):
        try:
            entity = ModelScheduler(data)
            db.session.add(entity)
            db.session.commit()
            return entity
        except Exception as e:
            logger.error("Exception:%s", e)
            logger.error(traceback.format_exc())
            return None

    def update(self, data=None) -> bool:
        try:
            if data is None:
                self.last_time = datetime.now()
            elif isinstance(data, int):
                self.count = data
            else:
                if "save_path" in data:
                    self.save_path = data["save_path"]
                if "filename" in data:
                    self.filename = data["filename"]
                if "is_live" in data:
                    self.is_live = data["is_live"]
            db.session.commit()
            return True
        except Exception as e:
            logger.error("Exception:%s %s", e, self.id)
            logger.error(traceback.format_exc())
            return False

    def delete(self) -> bool:
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception as e:
            logger.error("Exception:%s %s", e, self.id)
            logger.error(traceback.format_exc())
            return False


class ModelQueue(db.Model):
    __tablename__ = f"{package_name}_queue"
    __table_args__ = {"mysql_collate": "utf8_general_ci"}
    __bind_key__ = package_name

    id = db.Column(db.Integer, primary_key=True)
    created_time = db.Column(db.DateTime, nullable=False)
    url = db.Column(db.String, nullable=False)
    save_path = db.Column(db.String, nullable=False)
    filename = db.Column(db.String, nullable=False)
    key = db.Column(db.String)
    index = db.Column(db.Integer)

    def __init__(self, data):
        self.created_time = datetime.now()
        self.url = data["webpage_url"]
        self.save_path = data["save_path"]
        self.filename = data["filename"]
        self.key = "".join([random.choice(string.ascii_lowercase) for _ in range(5)])
        self.index = None

    def __repr__(self):
        return repr(self.as_dict())

    def as_dict(self) -> dict:
        return {x.name: getattr(self, x.name) for x in self.__table__.columns}

    @staticmethod
    def get_list(by_dict: bool = False):
        try:
            tmp = db.session.query(ModelQueue).all()
            if by_dict:
                tmp = [x.as_dict() for x in tmp]
            return tmp
        except Exception as e:
            logger.error("Exception:%s", e)
            logger.error(traceback.format_exc())

    @staticmethod
    def find(db_id: int):
        try:
            return db.session.query(ModelQueue).filter_by(id=db_id).first()
        except Exception as e:
            logger.error("Exception:%s %s", e, db_id)
            logger.error(traceback.format_exc())

    @staticmethod
    def peek():
        entity = None
        try:
            entity = db.session.query(ModelQueue).first()
        except Exception as e:
            logger.error("Exception:%s %s", e, entity)
            logger.error(traceback.format_exc())
        return entity

    @staticmethod
    def is_empty() -> bool:
        try:
            return db.session.query(ModelQueue).count() == 0
        except Exception as e:
            logger.error("Exception:%s", e)
            logger.error(traceback.format_exc())

    @staticmethod
    def create(data: dict):
        try:
            entity = ModelQueue(data)
            db.session.add(entity)
            db.session.commit()
            return entity
        except Exception as e:
            logger.error("Exception:%s", e)
            logger.error(traceback.format_exc())
            return None

    def set_index(self, index: int) -> bool:
        try:
            self.index = index
            db.session.commit()
            return True
        except Exception as e:
            logger.error("Exception:%s %s", e, self.id)
            logger.error(traceback.format_exc())
            return False

    def delete(self) -> bool:
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception as e:
            logger.error("Exception:%s %s", e, self.id)
            logger.error(traceback.format_exc())
            return False
