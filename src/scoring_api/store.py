import configparser
import redis
import logging
import functools
import json

def store_cached(func):
    @functools.wraps(func)
    def wrapper(store, *args):
        s = f'{func.__name__}:'
        for arg in args:
            s += f'({arg}):'
        s = s[:-1]
        result = store.cache_get(s)
        if result is None:
            result = func(store, *args)
            store.cache_set(s, result)
        return result
    return wrapper

class Store:
    def __init__(self, config_path):
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        self.redis_client = redis.Redis(
            host=self.config['redis']['server'],
            port=self.config['redis']['port'],
            db=self.config['redis']['db'],
            socket_timeout=int(self.config['redis']['timeout'])
        )
        self.n_attempts = int(self.config['redis']['n_attempts'])
        logging.info("Redis connection established")

    def get(self, key):
        for i in range(self.n_attempts):
            try:
                value = self.redis_client.get(key)
                if value is None:
                    return None

                value = value.decode("utf-8")
                if value.isdigit():  
                    return int(value)
                
                try:
                    return float(value) if "." in value else int(value)
                except ValueError:
                    pass

                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            except redis.exceptions.TimeoutError:
                logging.error(f"Timeout error on attempt {i+1} while getting key: {key}")
                continue
        logging.error(f"Failed to get key: {key} after {self.n_attempts} attempts")
        raise redis.exceptions.TimeoutError(f"Failed to get key: {key} after {self.n_attempts} attempts")
            
    def set(self, key, value):
        if isinstance(value, (int, float)):
            value = str(value)
        elif isinstance(value, (list, dict, tuple)):
            value = json.dumps(value)

        for i in range(self.n_attempts):
            try:
                self.redis_client.set(key, value)
                return
            except redis.exceptions.TimeoutError:
                logging.error(f"Timeout error on attempt {i+1} while setting key: {key}")
                continue
        logging.error(f"Failed to set key: {key} after {self.n_attempts} attempts")
        raise redis.exceptions.TimeoutError(f"Failed to set key: {key} after {self.n_attempts} attempts")
    
    def cache_get(self, key):
        try:
            return self.get(key)
        except redis.exceptions.TimeoutError:
            return None
    
    def cache_set(self, key, value):
        try:
            return self.set(key, value)
        except redis.exceptions.TimeoutError:
            pass

    def close(self):
        self.redis_client.close()
        logging.info("Redis connection closed")