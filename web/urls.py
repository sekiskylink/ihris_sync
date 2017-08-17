# -*- coding: utf-8 -*-

"""URL definitions of the application. Regex based URLs are mapped to their
class handlers.
"""

from app.controllers.main_handler import Index, Logout
from app.controllers.users_handler import Users
from app.controllers.groups_handler import Groups
from app.controllers.dashboard_handler import Dashboard
from app.controllers.settings_handler import Settings
from app.controllers.forgotpass_handler import ForgotPass
from app.controllers.downloads_handler import Downloads
from app.controllers.auditlog_handler import AuditLog
from app.controllers.api import iHRISRegistration

URLS = (
    r'^/', Index,
    r'/downloads', Downloads,
    r'/auditlog', AuditLog,
    r'/settings', Settings,
    r'/dashboard', Dashboard,
    r'/users', Users,
    r'/groups', Groups,
    r'/logout', Logout,
    r'/forgotpass', ForgotPass,
    # API stuff follows
    r'/api/v1/healthworker', iHRISRegistration,
)
