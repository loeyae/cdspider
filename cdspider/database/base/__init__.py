#-*- coding: utf-8 -*-
# Licensed under the Apache License, Version 2.0 (the "License"),
# see LICENSE for more details: http://www.apache.org/licenses/LICENSE-2.0.
#version: SVN: $Id: __init__.py 1391 2018-06-22 01:43:19Z zhangyi $

class Base:
    
    STATUS_INIT = 0
    STATUS_ACTIVE = 1
    STATUS_DELETED = 9

from .Admindb import AdminDB
from .Projectdb import ProjectDB
from .Sitedb import SiteDB
from .Sitetypedb import SitetypeDB
from .Urlsdb import UrlsDB
from .Attachmentdb import AttachmentDB
from .Taskdb import TaskDB
from .Keywordsdb import KeywordsDB
from .Uniquedb import UniqueDB
from .Resultdb import ResultDB
