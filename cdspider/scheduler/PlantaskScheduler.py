#-*- coding: utf-8 -*-
# Licensed under the Apache License, Version 2.0 (the "License"),
# see LICENSE for more details: http://www.apache.org/licenses/LICENSE-2.0.

"""
:author:  Zhang Yi <loeyae@gmail.com>
:date:    2018-9-20 15:49:37
"""
import time
import logging
from . import BaseScheduler
from cdspider.exceptions import *
from cdspider.libs.constants import *
from cdspider.libs.utils import get_object

class PlantaskScheduler(BaseScheduler):
    """
    任务调度
    """
    DEFAULT_RATE = [7200, "每2小时一次"]

    def __init__(self, context, inqueue = None, outqueue = None):
        super(PlantaskScheduler, self).__init__(context)
        if not inqueue:
            inqueue = QUEUE_NAME_SCHEDULER_TO_TASK
        self.inqueue = self.queue[inqueue]
        if not outqueue:
            outqueue = QUEUE_NAME_SCHEDULER_TO_SPIDER
        self.outqueue = self.queue[outqueue]
        rate_map = context.obj.get('rate_map')
        self.rate_map = rate_map

    def valid(self):
        if self.outqueue.qsize() > 500000:
            self.debug("outqueue is full")
            return False
        return True

    def schedule(self, message):
        self.debug("%s schedule got message: %s" % (self.__class__.__name__, str(message)))
        if not 'mode' in message or not message['mode']:
            raise CDSpiderError("%s handler mode is missing" % self.__class__.__name__)
        self.info("%s schedule starting..." % self.__class__.__name__)
        handler_mode = message['mode']
        name = HANDLER_MODE_HANDLER_MAPPING[handler_mode]
        handler = get_object("cdspider.handler.%s" % name)(self.ctx, None)
        self.info("%s loaded handler: %s" % (self.__class__.__name__, handler))
        save = {"now": int(time.time())}
        while True:
            has_item = False
            for item in handler.schedule(message, save):
                if item:
                    item['mode'] = handler_mode
                    self.debug("%s schedule task: %s" % (self.__class__.__name__, str(item)))
                    if not self.testing_mode:
                        self.send_task(item)
                    has_item = True
            if not has_item or 'count' in message:
                break
            time.sleep(0.1)
        del handler
        self.info("%s schedule end" % self.__class__.__name__)

    def send_task(self, task):
        if self.outqueue:
            self.debug("push %s into queue: scheduler2spider" % task)
            self.outqueue.put_nowait(task)
        else:
            raise CDSpiderError("%s outqueue is missing" % self.__class__.__name__)
