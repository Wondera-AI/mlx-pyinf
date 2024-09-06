import argparse
import asyncio
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from contextlib import asynccontextmanager, contextmanager

import redis.asyncio as redis
from pydantic import BaseModel, ValidationError

from src.service import DeploymentArgs, Request, Service

STOPWORD = "stop"
SERVICE_IN_CHANNEL = "service-in-channel"
SERVICE_OUT_CHANNEL = "service-out-channel"
CONNECTION_DETAILS = {
    "host": "redis-17902.c322.us-east-1-2.ec2.redns.redis-cloud.com",
    "port": 17902,
    "password": "MkiTVpOWFVLGLgJ7ptZ29dY80zER4cvR",
}


class RedisWriter:
    def __init__(self, log_key):
        self.redis_client = redis.Redis(**CONNECTION_DETAILS)
        print(f"RedisWriter Log Key: {log_key}")
        self.log_key = log_key
        self.original_stdout = sys.stdout
        self.encoding = sys.stdout.encoding
        self.append_script = self.redis_client.register_script("""
        local current = redis.call('HGET', KEYS[1], ARGV[1])
        if not current then
            current = ""
        end
        local updated = current .. ARGV[2]
        redis.call('HSET', KEYS[1], ARGV[1], updated)
        return updated
        """)

    def write(self, message):
        # self.original_stdout.write(message)

        # if message.strip():
        #     # print(f"Appending to {self.log_key}")
        #     asyncio.create_task(  # noqa: RUF006
        #         self.append_script(keys=[self.log_key], args=["logs", message + "\n"]),
        #     )
        if message.strip():
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Async context, use create_task to schedule the append
                loop.call_soon_threadsafe(
                    asyncio.create_task,
                    self.append_script(
                        keys=[self.log_key],
                        args=["logs", message + "\n"],
                    ),
                )
            else:
                # Synchronous context, run the append immediately
                loop.run_until_complete(
                    self.append_script(
                        keys=[self.log_key],
                        args=["logs", message + "\n"],
                    ),
                )

        self.original_stdout.write(message)

    def flush(self):
        self.original_stdout.flush()

    def isatty(self):
        return self.original_stdout.isatty()


@contextmanager
def redirect_stdout(log_key):
    redis_writer = RedisWriter(log_key)
    original_stdout = sys.stdout
    sys.stdout = redis_writer
    try:
        yield redis_writer
    finally:
        redis_writer.flush()
        sys.stdout = original_stdout


async def run_service(channel_name: str):
    service = Service()
    # queue = asyncio.Queue()

    print(f"Starting service... Subscribing to channel: {channel_name}")
    redis_conn = redis.Redis(**CONNECTION_DETAILS)

    async with redis_conn.pubsub() as pubsub:
        await pubsub.subscribe(channel_name)
        with ProcessPoolExecutor() as pool:
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True)
                if message and message["type"] == "message":
                    task_message = message["data"].decode("utf-8")
                    if task_message == STOPWORD:
                        print("STOP")
                        break

                    handle_task(task_message, service, pool)


def handle_task(task_message, service, pool):
    try:
        task_data = json.loads(task_message)
        request_data = json.loads(task_data["request_data"])
        request_body = request_data["body"]
        response_channel = task_data["response_channel"]
        log_key = task_data["log_key"]
        print(f"Received new task: {request_body}")

        loop = asyncio.get_running_loop()
        result_future = loop.run_in_executor(
            pool,
            handle_message_cpu,
            service,
            request_body,
            log_key,
        )

        # asyncio.create_task(publish_result(result_future, response_channel))
        async def log_and_publish_result():
            # While running in async loop, capture the result and redirect stdout
            with redirect_stdout(log_key):
                result = await result_future
                print(f"Result: {result}")
                if result:
                    print(f"Publishing to {response_channel} with result {result}")
                    redis_conn = redis.Redis(**CONNECTION_DETAILS)
                    await redis_conn.publish(response_channel, result)

        asyncio.create_task(log_and_publish_result())  # noqa: RUF006

    except (KeyError, json.JSONDecodeError) as err:
        print(f"Error loading json within task: {err}")

    except Exception as e:
        print(f"Unexpected error within task: {e}")


def handle_message_cpu(service_caller, request_data, log_key):  # noqa: PLR0911
    with redirect_stdout(log_key):
        try:
            # request_params = {}
            # for fname, finfo in Request.model_fields.items():
            #     if fname not in request_data:
            #         return f"Missing field: {fname}"
            #     if request_data[fname] is None:
            #         return f"Field {fname} cannot be None"

            #     # Extract the parameter data and class type
            #     param_data = request_data[fname]
            #     param_cls = finfo.annotation

            #     # Safely instantiate the parameter class
            #     if param_cls is not None:
            #         if isinstance(param_data, dict):
            #             request_params[fname] = param_cls(**param_data)
            #         else:
            #             return f"Field {fname} is expected to be a dictionary, but got {type(param_data).__name__}"
            #     else:
            #         return f"Parameter class for field '{fname}' is None"

            request = Request(**request_data)
            result = service_caller(request=request, args=DeploymentArgs())

            if hasattr(result, "model_dump_json"):
                return result.model_dump_json()

            json.dumps(result)  # Validate JSON serialization
            return result

        except (ValidationError, TypeError, ValueError) as e:
            return f"Error calling service: {str(e)}"

        except Exception as e:
            return f"Unexpected error: {str(e)}"


# async def publish_result(result_future, response_channel):
#     result = await result_future
#     print(f"Result: {result}")
#     if result:
#         print(f"Publishing to {response_channel} with result {result}")
#         redis_conn = redis.Redis(**CONNECTION_DETAILS)
#         await redis_conn.publish(response_channel, result)


# TODO maybe deprecating this as the return type is not necessary to validate
class Response(BaseModel):
    foo: str
    bar: str


# TODO test this Rust side
def parse_annotations(
    model: type[Request] | type[Response],
) -> list[dict[str, str]]:
    model_params = []
    for name, value in model.model_fields.items():
        params = {"name": name}

        if value.annotation is str:
            params["dtype"] = "string"

        elif value.annotation is int:
            params["dtype"] = "integer"

        elif value.annotation is float:
            params["dtype"] = "float"

        elif value.annotation is bool:
            params["dtype"] = "bool"

        else:
            raise ValueError(f"dtype {value.annotation} not handled")

        params["required"] = str(value.is_required())

        model_params.append(params)

    return model_params


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Machine Learning Inference")
    parser.add_argument(
        "--build",
        type=int,
        choices=[0, 1],
        default=0,
        help="Set to 1 to build",
    )
    args = parser.parse_args()

    print(f"Build: {args.build}")
    if not args.build:
        service_in_channel = os.getenv("service-in-channel")
        # service_in_channel = "py_service-a3_3-input"
        # service_in_channel = "test_channel"
        print(f"Service in channel: {service_in_channel}")
        if not service_in_channel:
            # raise ValueError("Environment variable 'service-in-channel' is not set")
            service_in_channel = "test-channel"

        asyncio.run(run_service(service_in_channel))

    else:
        input_data = {
            "body": parse_annotations(Request),
        }

        data = {
            "input": input_data,
            "output": parse_annotations(Response),
        }

        print(f"Py Schema: {data}")

        with open("config.json", "w") as file:
            file.write(json.dumps(data))
            file.close()
