""" Cornice services.
"""
import json
import redis
import requests

from cornice import Service

from .constants import API_BASE_URL, DEPLOY_QUEUE, ID_ALWAYSDATA_KEY, STATUS_KEY, LOGS_KEY
from .utils import hmac_digest


deploy = Service(name='deploy', path='/deploy/', description="Deploy kinto",
                 cors_origins=('*',), cors_max_age=3600)
status = Service(name='status', path='/status/', description="Status of the deployment",
                 cors_origins=('*',), cors_max_age=3600)


def get_redis_client(**kwargs):
    return redis.StrictRedis(**kwargs)


@deploy.post()
def deploy_info(request):
    """Returns Hello in JSON."""
    response = request.response

    # Get Authorization header
    try:
        authorization = request.headers['Authorization'].split(' ', 1)[1]
    except KeyError:
        response.status_code = 401

    # Check that we can use the header to authenticate
    api_response = requests.get(API_BASE_URL.format('/account/'),
                                headers={'Authorization': "Basic {}".format(authorization)})
    try:
        api_response.raise_for_status()
        id_alwaysdata = api_response.json()[0]['name']
    except requests.exceptions.HTTPError as error:
        response.status_code = 403
        return {"error": "{}".format(error)}

    # Build a offuscated user_id
    user_id = hmac_digest(request.registry.hmac_secret, authorization)

    # 3. Add the header to a queue
    r = get_redis_client(**request.registry.redis)
    r.delete(STATUS_KEY.format(user_id), LOGS_KEY.format(user_id))
    r.set(ID_ALWAYSDATA_KEY.format(user_id), id_alwaysdata)
    r.rpush(DEPLOY_QUEUE, authorization)
    response.status_code = 202
    return response


@status.get()
def get_deployment_info(request):
    response = request.response

    # 1. Get Authorization header
    try:
        authorization = request.headers['Authorization'].split(' ', 1)[1]
    except KeyError:
        response.status_code = 401

    # Build a offuscated user_id
    user_id = hmac_digest(request.registry.hmac_secret, authorization)

    r = get_redis_client(**request.registry.redis)
    status = r.get(STATUS_KEY.format(user_id))
    logs = r.get(LOGS_KEY.format(user_id))

    if status is None and logs is None:
        response.status_code = 404

    return {"status": json.loads(status), "logs": logs}
