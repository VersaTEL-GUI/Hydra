# coding:utf-8
import logging
import logging.handlers
import logging.config
from functools import wraps
import traceback
import sys
import os
import getpass
import socket




class MyLoggerAdapter(logging.LoggerAdapter):
    """
    实现一个LoggerAdapter的子类，重写process()方法。
    其中对于kwargs参数的操作应该是先判断其本身是否包含extra关键字，如果包含则不使用默认值进行替换；
    如果kwargs参数中不包含extra关键字则取默认值。
    """
    def process(self, msg, kwargs):
        if 'extra' not in kwargs:
            kwargs["extra"] = self.extra
        return msg, kwargs


class Log(object):

    fmt = logging.Formatter("%(asctime)s [%(username)s] [%(transaction_id)s] [%(type)s] [%(describe1)s] [%(describe2)s] [%(data)s]",datefmt = '[%Y/%m/%d %H:%M:%S]')
    handler_input = logging.handlers.RotatingFileHandler(filename='Hydra_log.log',mode='a',maxBytes=10*1024*1024,backupCount=5)
    handler_input.setFormatter(fmt)

    def __init__(self,username,transaction_id):
        self.username = username
        self.transaction_id = transaction_id
        self.host = None

    def logger_create(self):
        logger_hydra = logging.getLogger('hydra')
        logger_hydra.addHandler(self.handler_input)
        logger_hydra.setLevel(logging.DEBUG)
        extra_dict = {
            "username": "USERNAME",
            "transaction_id":"",
            "type": "TYPE",
            "describe1": "",
            "describe2": "",
            "data": ""}
        # 获取一个自定义LoggerAdapter类的实例
        logger = MyLoggerAdapter(logger_hydra, extra_dict)
        return logger


    # write to log file
    def write_to_log(self,type,describe1,describe2,data):
        logger_hydra = self.logger_create()
        # logger_hydra.logger.removeHandler(self.handler_input)
        logger_hydra.debug(
            '',
            extra={
                'username': self.username,
                'transaction_id': self.transaction_id, #
                'type': type,
                'describe1': describe1,
                'describe2': describe2,
                'data': data})