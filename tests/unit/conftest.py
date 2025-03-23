import pytest
import datetime
import hashlib
import scoring_api.api as api
import redis
import os
from scoring_api.store import Store
from pytest_mock_resources import create_redis_fixture

mock_redis = create_redis_fixture()

def get_response(mock_redis, request, store=None):
    headers = {}
    context = {}
    if store is None:
        store = Store(os.path.dirname(os.path.abspath(__file__)) + "/config.ini")
        store.redis_client = mock_redis
    response, code = api.method_handler({"body": request, "headers": headers}, context, store)
    return response, code, headers, context

def set_valid_auth(request):
    if request.get("login") == api.ADMIN_LOGIN:
        request["token"] = hashlib.sha512((datetime.datetime.now().strftime("%Y%m%d%H") + api.ADMIN_SALT).encode('utf-8')).hexdigest()
    else:
        msg = (request.get("account", "") + request.get("login", "") + api.SALT).encode('utf-8')
        request["token"] = hashlib.sha512(msg).hexdigest()

@pytest.fixture
def bad_store(mocker):
    mock_redis = mocker.patch("scoring_api.store.redis.Redis")
    mock_instance = mock_redis.return_value
    mock_instance.get.side_effect = redis.exceptions.TimeoutError
    return Store(os.path.dirname(os.path.abspath(__file__)) + "/config.ini")

@pytest.fixture
def bad_auth_request():
    return [
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "", "arguments": {}},
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "sdd", "arguments": {}},
        {"account": "horns&hoofs", "login": "admin", "method": "online_score", "token": "", "arguments": {}},
    ]

@pytest.fixture
def invalid_method_request():
    return [
        {"account": "horns&hoofs", "login": "h&f", "method": "online_score"},
        {"account": "horns&hoofs", "login": "h&f", "arguments": {}},
        {"account": "horns&hoofs", "method": "online_score", "arguments": {}},
    ]

@pytest.fixture
def invalid_score_request():
        return [
            {},
            {"phone": "79175002040"},
            {"phone": "89175002040", "email": "stupnikov@otus.ru"},
            {"phone": "79175002040", "email": "stupnikovotus.ru"},
            {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": -1},
            {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": "1"},
            {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.1890"},
            {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "XXX"},
            {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.2000", "first_name": 1},
            {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.2000",
            "first_name": "s", "last_name": 2},
            {"phone": "79175002040", "birthday": "01.01.2000", "first_name": "s"},
            {"email": "stupnikov@otus.ru", "gender": 1, "last_name": 2},
        ]

@pytest.fixture
def ok_score_request():
    return [
        {"phone": "79175002040", "email": "stupnikov@otus.ru"},
        {"phone": 79175002040, "email": "stupnikov@otus.ru"},
        {"gender": 1, "birthday": "01.01.2000", "first_name": "a", "last_name": "b"},
        {"gender": 0, "birthday": "01.01.2000"},
        {"gender": 2, "birthday": "01.01.2000"},
        {"first_name": "a", "last_name": "b"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.2000",
         "first_name": "a", "last_name": "b"},
    ]

@pytest.fixture
def invalid_interests_request():
    return [
        {},
        {"date": "20.07.2017"},
        {"client_ids": [], "date": "20.07.2017"},
        {"client_ids": {1: 2}, "date": "20.07.2017"},
        {"client_ids": ["1", "2"], "date": "20.07.2017"},
        {"client_ids": [1, 2], "date": "XXX"},
    ]

@pytest.fixture
def ok_interests_request():
     return [
        {"client_ids": [1, 2, 3], "date": datetime.datetime.today().strftime("%d.%m.%Y")},
        {"client_ids": [1, 2], "date": "19.07.2017"},
        {"client_ids": [0]},
    ]
