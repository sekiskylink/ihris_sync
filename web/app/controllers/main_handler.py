# -*- coding: utf-8 -*-

"""This module contains the main handler of the application.
"""

import web
from . import render
from . import csrf_protected, db, get_session, put_session
from app.tools.utils import auth_user, audit_log


class Index:
    def GET(self):
        l = locals()
        del l['self']
        return render.login(**l)

    @csrf_protected
    def POST(self):
        session = get_session()
        params = web.input(username="", password="")
        username = params.username
        password = params.password
        r = auth_user(db, username, password)
        if r[0]:
            session.loggedin = True
            info = r[1]
            session.name = info.firstname + " " + info.lastname
            session.username = username
            session.sesid = info.id
            session.role = info.role
            session.criteria = ""
            put_session(session)
            log_dict = {
                'logtype': 'Web', 'action': 'Login', 'actor': username,
                'ip': web.ctx['ip'], 'descr': 'User %s logged in' % username,
                'user': info.id
            }
            audit_log(db, log_dict)

            l = locals()
            del l['self']
            return web.seeother("/requests")
        else:
            session.loggedin = False
            session.logon_err = r[1]
        l = locals()
        del l['self']
        return render.login(**l)


class Logout:
    def GET(self):
        session = get_session()
        log_dict = {
            'logtype': 'Web', 'action': 'Logout', 'actor': session.username,
            'ip': web.ctx['ip'], 'descr': 'User %s logged out' % session.username,
            'user': session.sesid
        }
        audit_log(db, log_dict)
        session.kill()
        return web.seeother("/")
