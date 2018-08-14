#-*- coding: utf-8 -*-
# Licensed under the Apache License, Version 2.0 (the "License"),
# see LICENSE for more details: http://www.apache.org/licenses/LICENSE-2.0.

import logging

class Component(object):

    def __init__(self, logger, log_level):
        self.logger = logger or logging.getLogger('root')
        self.logger.setLevel(log_level)
        self.log_level = log_level

    def debug(self, message, *args, **kwargs):
        if self.log_level <= logging.DEBUG:
            self.logger.debug(message, *args, **kwargs)

    def info(self, message, *args, **kwargs):
        if self.log_level <= logging.INFO:
            self.logger.info(message, *args, **kwargs)

    def warn(self, message, *args, **kwargs):
        if self.log_level <= logging.WARN:
            self.logger.warn(message, *args, **kwargs)

    def error(self, message, *args, **kwargs):
        self.logger.error(message, *args, **kwargs)

    def fatal(self, message, *args, **kwargs):
        self.logger.fatal(message, *args, **kwargs)

    def critical(self, message, *args, **kwargs):
        self.logger.critical(message, *args, **kwargs)
