import argparse
import asyncio
import json
from concurrent.futures import ProcessPoolExecutor

import redis.asyncio as redis
from pydantic import BaseModel

from src.service import (
    ReqBodyParams,
    ReqPathParams,  # Response,
    ReqQueryParams,
    Request,
    Service,
)


class Response(BaseModel):
    foo: str
    bar: str


REQUIRED = "required"
STOPWORD = "stop"
SERVICE_IN_CHANNEL = "service-in-channel"
SERVICE_OUT_CHANNEL = "service-out-channel"


def handle_message_cpu(service_caller, task_message):
    # Dynamically create instances of the Pydantic models from the task_message
    message_data = json.loads(task_message)
    path_params = ReqPathParams(**message_data["path"])
    query_params = ReqQueryParams(**message_data["query"])
    body_params = ReqBodyParams(**message_data["body"])

    # Create the Request instance
    request = Request(path=path_params, query=query_params, body=body_params)

    # CPU bound part: run the caller function of our service
    result = service_caller(request=request)

    return result.model_dump_json() if result else None


async def handle_message_io(redis_conn, result, response_channel):
    if result:
        await redis_conn.publish(response_channel, result)


async def process_service(channel):
    service = Service()
    loop = asyncio.get_running_loop()

    async with redis.from_url(
        url="redis://redis-17902.c322.us-east-1-2.ec2.redns.redis-cloud.com",
        port=17902,
        password="MkiTVpOWFVLGLgJ7ptZ29dY80zER4cvR",
    ) as redis_conn:
        with ProcessPoolExecutor() as pool:
            while True:
                message = await channel.get_message(ignore_subscribe_messages=True)
                if message is not None and message["type"] == "message":
                    print(f"(Reader) Message Received: {message}")
                    task_message = message["data"].decode("utf-8")
                    request_data, response_channel = task_message.split(">", 1)

                    # Offload CPU-bound part to a separate process
                    result_future = await loop.run_in_executor(
                        pool,
                        handle_message_cpu,
                        service,
                        task_message,
                    )

                    async def process_result(result_future, response_channel):
                        result = await result_future
                        await handle_message_io(redis_conn, result, response_channel)

                    # Schedule the I/O-bound part as a separate coroutine
                    asyncio.create_task(process_result(result_future, response_channel))  # noqa: RUF006

                    if task_message == STOPWORD:
                        print("(Reader) STOP")
                        break
                else:
                    print("No message received")

                await asyncio.sleep(0)  # Yield control to the event loop


async def main(channel_name: str):
    r = await redis.from_url(
        url="redis://redis-17902.c322.us-east-1-2.ec2.redns.redis-cloud.com",
        port=17902,
        password="MkiTVpOWFVLGLgJ7ptZ29dY80zER4cvR",
    )

    print(f"Subscribing to channel: {channel_name}")

    async with r.pubsub() as pubsub:
        await pubsub.subscribe(channel_name)
        await process_service(pubsub)


def parse_annotations(
    model: type[ReqPathParams]
    | type[ReqBodyParams]
    | type[ReqQueryParams]
    | type[Response],
) -> list[dict[str, str]]:
    model_params = []
    for name, value in model.model_fields.items():
        params = {"name": name}

        if value.annotation is str:
            params["dytpe"] = "string"

        elif value.annotation is int:
            params["dytpe"] = "integer"

        elif value.annotation is float:
            params["dytpe"] = "float"

        elif value.annotation is bool:
            params["dytpe"] = "bool"

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

    print(args.build)
    if not args.build:
        asyncio.run(main("server-sender"))

    else:
        # TODO handle required params

        print(ReqPathParams.model_fields)

        data = {
            "input": {
                "path": parse_annotations(ReqPathParams),
                "query": parse_annotations(ReqQueryParams),
                "body": parse_annotations(ReqBodyParams),
            },
            "output": parse_annotations(Response),
        }
        print("foo")
        print(data)

        with open("config.json", "w") as file:
            file.write(json.dumps(data))

        # match value.annotation:
        #     case str:
        #         params["dytpe"] = "string"

        #     case int:
        #         params["dytpe"] = "int"

        data = {
            "input": Request(
                path=ReqPathParams(required_foo="foo"),
                query=ReqQueryParams(),
                body=ReqBodyParams(required_foo="foo"),
            ),
            "output": Response(
                foo="foo",
                bar="bar",
            ),
        }
    # await r.publish("channel:1", "Hello")
    # await r.publish("channel:2", "World")
    # await r.publish("channel:1", STOPWORD)
    # r = redis.Redis(
    #     host="redis-17902.c322.us-east-1-2.ec2.redns.redis-cloud.com",
    #     port=17902,
    #     password="MkiTVpOWFVLGLgJ7ptZ29dY80zER4cvR",
    # )

    # pubsub = r.pubsub()
    # pubsub.subscribe("update_channel")

    # print("Listening for messages on the 'update_channel'...")
    # while True:
    #     message = pubsub.get_message()
    #     if message:
    #         response = process_message(message, my_instance)
    #         if response:
    #             r.publish("response_channel", json.dumps({"response": response}))
    #     time.sleep(0.01)

# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description="Machine Learning Experiments")
#     parser.add_argument(
#         "--gen-bindings",
#         type=int,
#         choices=[0, 1],
#         default=0,
#         help="Set to 1 to generate bindings, 0 to run training experiment",
#     )
#     parser.add_argument(
#         "--ray-address",
#         type=str,
#         help="Ray cluster address",
#         default="auto",
#     )
#     parser.add_argument(
#         "--prepare-batches",
#         action="store_true",
#         help="Prepare batches for training",
#         default=False,
#     )
#     args = parser.parse_args()


# # TODO
# xp_name = "my_experiment"

# # redis_client = redis.Redis(host="localhost", port=6379, db=0)
# # redis_logger = RedisLogger(redis_client, "stdout_logs")

# if args.gen_bindings:
#     build_configs("yaml")

# else:
#     cfg_data: dict = build_configs("loop_conf")

#     if not is_ray_running():
#         print("Ray is not running.")
#         start_local_ray()

#     # ensure experiement builds before running Ray job
#     Experiment.init_module(
#         cfg_dict=cfg_data["cfg_dict"],
#         cfg_name=cfg_data["train_cfg"],
#         models_name=cfg_data["models"],
#         datasets_name=cfg_data["datasets"],
#         losses_name=cfg_data["losses"],
#         optimizers_name=cfg_data["optimizers"],
#         metrics_name=cfg_data["metrics"],
#         tools_name=cfg_data["tools"],
#     )

#     # with redirect_stdout(redis_logger):
#     head_main(args=args, cfg_data=cfg_data)


# class Service:
#     def __init__(self, request: RequestParams):
#         self.request = request

#     def __call__(self):
#         # NOTE DO WHATEVER
#         pass


# class MyClass:
#     def __init__(self):
#         self.attribute_name = "initial_value"

#     def set_attribute(self, value):
#         self.attribute_name = value

#     def __str__(self):
#         return f"MyClass(attribute_name={self.attribute_name})"


# async def process_message(channel):
#     async for message in channel.iter(encoding="utf-8"):
#         data = json.loads(message)
#         attribute_name = data.get("attribute_name")
#         new_value = data.get("new_value")

#         if hasattr(my_instance, attribute_name):
#             setattr(my_instance, attribute_name, new_value)
#             print(f"Updated attribute value: {getattr(my_instance, attribute_name)}")
#         else:
#             print("Attribute not found")


# async def main():
#     global my_instance
#     my_instance = MyClass()

#     redis = await aioredis.create_redis("redis://redis-server")
#     (channel,) = await redis.subscribe("update_channel")

#     print("Listening for messages on the 'update_channel'...")
#     await process_message(channel)


# if __name__ == "__main__":
#     asyncio.run(main())


# class MyClass:
#     def __init__(self):
#         self.attribute_name = "initial_value"

#     def set_attribute(self, value):
#         self.attribute_name = value

#     def get_attribute(self):
#         return self.attribute_name

#     def process_request(self, request):
#         action = request.get("action")
#         if action == "set":
#             self.set_attribute(request.get("new_value"))
#         elif action == "get":
#             return self.get_attribute()
#         return "Unknown action"


# def process_message(message, my_instance):
#     if message["type"] == "message":
#         request = json.loads(message["data"])
#         response = my_instance.process_request(request)
#         return response


# class HeaderParams(BaseModel):
#     ree: str = "ree-default"
