#-*- coding: utf-8 -*-
# Licensed under the Apache License, Version 2.0 (the "License"),
# see LICENSE for more details: http://www.apache.org/licenses/LICENSE-2.0.

class Base(object):

    STATUS_INIT = 0
    STATUS_ACTIVE = 1
    STATUS_DELETED = 9

from .Admindb import AdminDB
from .AttachDatadb import AttachDataDB
from .Attachmentdb import AttachmentDB
from .Commentsdb import CommentsDB
from .Keywordsdb import KeywordsDB
from .ParseRuledb import ParseRuleDB
from .Projectsdb import ProjectsDB
from .Sitesdb import SitesDB
from .Taskdb import TaskDB
from .Uniquedb import UniqueDB
from .Urlsdb import UrlsDB
