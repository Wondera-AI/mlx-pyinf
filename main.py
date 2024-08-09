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
