import time
from typing import Any
from pydantic import BaseModel


class ReqPathParams(BaseModel):
    required_foo: str


class ReqQueryParams(BaseModel):
    bar: str = "bar-default"


class ReqBodyParams(BaseModel):
    required_foo: str
    optional_foo: str = "foo-default"


class Request(BaseModel):
    path: ReqPathParams
    query: ReqQueryParams
    body: ReqBodyParams
    # header: HeaderParams


# class Response(BaseModel):
#     foo: str
#     bar: str


class Service:
    def __init__(self):
        self.name = "model_A"
        # self.request =
        # self.loggger = Logger()
        # auto capture STDOUT
        pass

    # TODO http, ws, func, cron
    # TODO workflow, tasks, flyte
    # @resources(memory="1Gi", cpu="1")
    def __call__(self, request: Request) -> Any:
        # NOTE DO WHATEVER\

        # self.service("general_model_a").call()

        # # main()
        # # self.logger.info()

        # self.logger.info()

        # self.logger.error()

        # promise = self.services("model_B").call(request, data)

        # # garuanteed
        # embd1 = promise.data.embeddings

        # self.http_req("http://")

        # self.logger.state()

        time.sleep(5)

        return 1
