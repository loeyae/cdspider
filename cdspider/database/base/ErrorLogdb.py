#-*- coding: utf-8 -*-

# Licensed under the Apache License, Version 2.0 (the "License"),
# see LICENSE for more details: http://www.apache.org/licenses/LICENSE-2.0.

"""
:author:  Zhang Yi <loeyae@gmail.com>
:date:    2018-8-4 21:43:09
"""

from . import Base

{
    "error": {
        'uuid': int,        # log id
        'tid': int,         # spider task id
        'level': str,       # process info
        'url': str,         # error message
        'error': str,       # create time
        'msg': str,         # trace log
        'class': str,       # error class
        'create_ad': int,   #
    }
}

class ErrorLogDB(Base):
    """
    craw_log data object
    """

    def insert(self, obj = {}):
        raise NotImplementedError

    def update(self, id, obj = {}):
        raise NotImplementedError

    def delete(self, id):
        raise NotImplementedError