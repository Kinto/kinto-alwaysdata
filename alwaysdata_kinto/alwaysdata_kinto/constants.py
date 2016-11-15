API_BASE_URL = "https://api.alwaysdata.com/v1{}"
DEPLOY_QUEUE = "deploy"

ID_ALWAYSDATA_KEY = 'alwaysdata_kinto.{}.id'
STATUS_KEY = 'alwaysdata_kinto.{}.status'
LOGS_KEY = 'alwaysdata_kinto.{}.logs'

REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0


class STATUS:
    UNKNOWN = "unknown"
    CREATED = "created"
    EXISTS = "exists"
    ERROR = "error"
