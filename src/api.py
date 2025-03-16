#!/usr/bin/env python
# -*- coding: utf-8 -*-

import abc
import json
import datetime
import logging
import hashlib
import uuid
from argparse import ArgumentParser
from http.server import BaseHTTPRequestHandler, HTTPServer
from scoring import get_score, get_interests


SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}

class Field(abc.ABC):
    def __init__(self, required=False, nullable=False, empty_value=None):
        self.required = required
        self.nullable = nullable
        self.empty_value = empty_value

    def __set_name__(self, owner, name):
        self.owner = owner
        self.public_name = name
        self.private_name = '_' + name

    def __get__(self, obj, objtype=None):
        return getattr(obj, self.private_name)
        
    def __set__(self, obj, value):
        if self.required and value is None:
            raise ValueError(f"Required field {self.public_name} in {self.owner.__name__} is not provided")
        
        if value is None:
            value = self.empty_value

        if not self.nullable and value == self.empty_value:
            raise ValueError(f"Required field {self.public_name} in {self.owner.__name__} is not provided")
        
        if value == self.empty_value:
            setattr(obj, self.private_name, self.empty_value)
            return
        
        flag = self.validate(value)
        if flag:
            setattr(obj, self.private_name, value)
        else:
            raise ValueError(f"Value {value} is not valid for field {self.public_name} in {self.owner.__name__}")
        
    @abc.abstractmethod
    def validate(self, value):
        pass

class CharField(Field):
    def __init__(self, required=False, nullable=False, empty_value=""):
        super().__init__(required, nullable, empty_value)

    def validate(self, value):
        if not isinstance(value, str):
            return False
        return True


class ArgumentsField(Field):
    def __init__(self, required=False, nullable=False, empty_value={}):
        super().__init__(required, nullable, empty_value)

    def validate(self, value):
        if not isinstance(value, dict):
            return False
        return True


class EmailField(CharField):
    def validate(self, value):
        flag = super().validate(value)
        if not flag:
            return False
        if "@" not in value:
            return False
        return True


class PhoneField(Field):
    def validate(self, value):
        if not isinstance(value, str) and not isinstance(value, int):
            return False
        val = str(value)
        if not val.startswith("7") or len(val) != 11:
            return False
        return True


class DateField(Field):
    def __init__(self, required=False, nullable=False, empty_value=None):
        super().__init__(required, nullable, empty_value)

    def validate(self, value):
        if not isinstance(value, str):
            return False
        try:
            datetime.datetime.strptime(value, "%d.%m.%Y")
        except ValueError:
            return False
        return True


class BirthDayField(DateField):
    def validate(self, value):
        flag = super().validate(value)
        if not flag:
            return False
        if datetime.datetime.now().year - datetime.datetime.strptime(value, "%d.%m.%Y").year > 70:
            return False
        return True


class GenderField(Field):        
    def validate(self, value):
        if not isinstance(value, int):
            return False
        if value not in [0, 1, 2]:
            return False
        return True


class ClientIDsField(Field):
    def __init__(self, required=False, nullable=False, empty_value=[]):
        super().__init__(required, nullable, empty_value)

    def validate(self, value):
        if not isinstance(value, list):
            return False
        for item in value:
            if not isinstance(item, int):
                return False
        return True
    
class Request:
    def __init__(self, **kwargs):
        self.has = []
        for key in self.__class__.__dict__:
            if isinstance(self.__class__.__dict__[key], Field):
                if key in kwargs:
                    setattr(self, key, kwargs[key])
                    self.has.append(key)
                else:
                    setattr(self, key, None)
        if not self.validate():
            raise ValueError(f"Invalid request arguments {kwargs} for {self.__class__.__name__}")

    def validate(self):
        return True

class ClientsInterestsRequest(Request):
    client_ids = ClientIDsField(required=True, nullable=False)
    date = DateField(required=False, nullable=True)


class OnlineScoreRequest(Request):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def validate(self):
        if 'phone' in self.has and 'email' in self.has:
            return True
        if 'first_name' in self.has and 'last_name' in self.has:
            return True
        if 'gender' in self.has and 'birthday' in self.has:
            return True
        return False


class MethodRequest(Request):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


def check_auth(request):
    if request.is_admin:
        digest = hashlib.sha512((datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).encode('utf-8')).hexdigest()
    else:
        digest = hashlib.sha512((request.account + request.login + SALT).encode('utf-8')).hexdigest()
    return digest == request.token


def method_handler(request, ctx, store):        
    try:
        if "body" not in request:
            method = MethodRequest()
        else:
            method = MethodRequest(**request["body"])
        ctx["has"] = []

        if not check_auth(method):
            logging.error("Forbidden")
            return {"error": "Forbidden"}, FORBIDDEN
    
        if method.method == "online_score":
            if method.is_admin:
                return {"score": 42}, OK
            online_score = OnlineScoreRequest(**method.arguments)
            ctx["has"] = online_score.has
            return {"score": get_score(store, online_score.phone, online_score.email,
                                       online_score.birthday, online_score.gender,
                                       online_score.first_name, online_score.last_name)}, OK
        elif method.method == "clients_interests":
            clients_interests = ClientsInterestsRequest(**method.arguments)
            ctx["has"] = clients_interests.has
            ctx["nclients"] = len(clients_interests.client_ids)
            out = {}
            for client_id in clients_interests.client_ids:
                out[client_id] = get_interests(store, client_id)
            return out, OK
        else:
            logging.error(f"Method not found: {method.method}")
            return {"error": "Method not found"}, NOT_FOUND
    except ValueError as e:
        logging.error(f"Validation error: {e}")
        return {"error": str(e)}, INVALID_REQUEST


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = None

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
        except:
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context, self.store)
                except Exception as e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r).encode('utf-8'))
        return


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-p", "--port", action="store", type=int, default=8080)
    parser.add_argument("-l", "--log", action="store", default=None)
    args = parser.parse_args()
    logging.basicConfig(filename=args.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", args.port), MainHTTPHandler)
    logging.info("Starting server at %s" % args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()