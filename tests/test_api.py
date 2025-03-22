import scoring_api.api as api
from .conftest import get_response, set_valid_auth



def test_empty_request():
    _, code = get_response({})[:2]
    assert code == api.INVALID_REQUEST, "Test empty request failed in code"

def test_bad_auth(bad_auth_request):
    for idx, request in enumerate(bad_auth_request):
        _, code = get_response(request)[:2]
        assert code == api.FORBIDDEN, f"Request {idx} failed in code in test_bad_auth"

def test_invalid_method_request(invalid_method_request):
    for idx, request in enumerate(invalid_method_request):
        set_valid_auth(request)
        response, code = get_response(request)[:2]
        assert code == api.INVALID_REQUEST, f"Request {idx} failed in code in test_invalid_method_request"
        assert len(response) > 0, f"Request {idx} failed in response in test_invalid_method_request"

def test_invalid_score_request(invalid_score_request):
    for idx, arguments in enumerate(invalid_score_request):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments": arguments}
        set_valid_auth(request)
        response, code = get_response(request)[:2]
        assert code == api.INVALID_REQUEST, f"Request {idx} failed in code in test_invalid_score_request"
        assert len(response) > 0, f"Request {idx} failed in response in test_invalid_score_request"

def test_ok_score_request(ok_score_request):
    for idx, arguments in enumerate(ok_score_request):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments": arguments}
        set_valid_auth(request)
        response, code, _, context, _ = get_response(request)
        assert code == api.OK, f"Request {idx} failed in code in test_ok_score_request"
        score = response.get("score")
        assert isinstance(score, (int, float)) and score >= 0, f"Request {idx} failed in score in test_ok_score_request"
        assert sorted(context["has"]) == sorted(arguments.keys()), f"Request {idx} failed in context in test_ok_score_request"

def test_ok_score_admin_request():
    arguments = {"phone": "79175002040", "email": "stupnikov@otus.ru"}
    request = {"account": "horns&hoofs", "login": "admin", "method": "online_score", "arguments": arguments}
    set_valid_auth(request)
    response, code = get_response(request)[:2]
    assert code == api.OK, "Test ok score admin failed in code"
    score = response.get("score")
    assert score == 42, "Test ok score admin failed in score"

def test_invalid_interests_request(invalid_interests_request):
    for idx, arguments in enumerate(invalid_interests_request):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "clients_interests", "arguments": arguments}
        set_valid_auth(request)
        response, code = get_response(request)[:2]
        assert code == api.INVALID_REQUEST, f"Request {idx} failed in code in test_invalid_interests_request"
        assert len(response) > 0, f"Request {idx} failed in response in test_invalid_interests_request"

def test_ok_interests_request(ok_interests_request):
    for idx, arguments in enumerate(ok_interests_request):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "clients_interests", "arguments": arguments}
        set_valid_auth(request)
        response, code, _, context, _ = get_response(request)
        assert code == api.OK, f"Request {idx} failed in code in test_ok_interests_request"
        assert len(arguments["client_ids"]) == len(response), f"Request {idx} failed in response in test_ok_interests_request"
        assert all(v and isinstance(v, list) and all(isinstance(i, (bytes, str)) for i in v)
                        for v in response.values()), f"Request {idx} failed in response in test_ok_interests_request"
        assert context.get("nclients") == len(arguments["client_ids"]), f"Request {idx} failed in context in test_ok_interests_request"
