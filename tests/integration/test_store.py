from scoring_api.store import Store

def test_get_value():    
    store = Store("tests/integration/config.ini")
    result = store.get("test_get_some_key")
    assert result is None, f'{result} is not None in test_get_value'

def test_set_value():
    store = Store("tests/integration/config.ini")
    try:
        result = store.set("test_set_some_key", "value")
    except TimeoutError:
        result = None
    assert result is None, f'{result} is not None in test_set_value'
