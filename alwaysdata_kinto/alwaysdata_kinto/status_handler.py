# -*- coding: utf-8 -*-
import json

from collections import OrderedDict

from .constants import STATUS, STATUS_KEY, LOGS_KEY

KEYS = ['database', 'ssh_user', 'configuration', 'ssh_commands']


class RedisStatusHandler(object):
    def __init__(self, redis_client, user_id):
        self.redis_client = redis_client
        self.user_id = user_id
        self.statuses = OrderedDict()
        for key in KEYS:
            self.statuses[key] = STATUS.UNKNOWN

    def get_status(self):
        return {
            "status": self.statuses,
            "ssh_logs": self.logs.getvalue()
        }

    def __setattr__(self, key, value):
        if key in KEYS:
            self.statuses[key] = value
            self.redis_client.set(STATUS_KEY.format(self.user_id), json.dumps(self.statuses))
            return

        if key == "ssh_logs":
            self.logs = value
            self.redis_client.set(LOGS_KEY.format(self.user_id), self.logs.getvalue())
            return

        super(RedisStatusHandler, self).__setattr__(key, value)

    def __getattr__(self, key):
        if key in KEYS:
            return self.statuses[key]

        if key == 'ssh_logs':
            return self.logs
