#-*- coding: utf-8 -*-

# Licensed under the Apache License, Version 2.0 (the "License"),
# see LICENSE for more details: http://www.apache.org/licenses/LICENSE-2.0.

"""
:author:  Zhang Yi <loeyae@gmail.com>
:date:    2018-6-21 18:37:29
:version: SVN: $Id: Attachmentdb.py 2119 2018-07-04 03:56:41Z zhangyi $
"""

from . import Base

{
    "attachment": {
        'aid': int,           # 附加任务I
        'domain': str,        # 一级域名        
        'subdomain': str,     # 二级域名 
        'status': int,        # 状态        
        'rate': int,          # 更新频率
        'expire': int,        # 过期时间    
        'preparse': str,      # 预解析设置          
        'process': str,       # 解析设置
        'unique': str,        # 唯一索引设置
        'ctime': int,         # 创建时间
        'utime': int,         # 最后一次更新时间
        'creator': int,       # 创建人ID         
        'updator': int,       # 最后一次修改人ID
    }
}

class AttachmentDB(Base):
    """
    attachment database obejct
    """

    def insert(self, obj = {}):
        raise NotImplementedError

    def update(self, id, obj = {}):
        raise NotImplementedError

    def delete(self, id, where):
        raise NotImplementedError

    def delete_by_site(self, sid, where):
        raise NotImplementedError

    def delete_by_project(self, pid, where):
        raise NotImplementedError

    def active(self, id, where):
        raise NotImplementedError

    def disable(self, id, where):
        raise NotImplementedError

    def disable_by_site(self, sid, where):
        raise NotImplementedError

    def disable_by_project(self, pid, where):
        raise NotImplementedError

    def get_detail(self, id):
        raise NotImplementedError

    def get_list(self, where = {}, select=None, **kwargs):
        raise NotImplementedError
