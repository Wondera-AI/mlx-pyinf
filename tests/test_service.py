import asyncio
import json
from concurrent.futures import ProcessPoolExecutor
from contextlib import asynccontextmanager
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest
import redis.asyncio as redis
from pydantic import BaseModel, ValidationError
from pytest_mock import mocker

from main import (
    STOPWORD,
    Response,
    build_pubsub_process_service,
    handle_message_cpu,
    handle_message_io,
    process_service,
    redirect_stdout,
)
from src.service import Service

# pdm run pytest -s tests/test_service.py


@pytest.fixture
def service():
    return Service()


async def local_redis_server():
    # TODO FIXTURE ME - https://stackoverflow.com/questions/28283472/py-test-mixing-fixtures-and-asyncio-coroutines
    local_redis_server = await redis.Redis.from_url("redis://localhost:6379")
    await local_redis_server.flushall()
    yield local_redis_server
    await local_redis_server.flushall()


@pytest.mark.asyncio
async def test_redis_pubsub():
    test_channel = "test_channel"
    test_message = "test_message"

    local_redis_server = await redis.Redis.from_url("redis://localhost:6379")
    # local_redis_server = await local_redis_server()
    pubsub = local_redis_server.pubsub()
    await pubsub.subscribe(test_channel)
    await local_redis_server.publish(test_channel, test_message)

    message = await pubsub.get_message(ignore_subscribe_messages=True)
    while message is None or message["type"] != "message":
        message = await pubsub.get_message(ignore_subscribe_messages=True)
        await asyncio.sleep(0.1)

    assert message["data"].decode("utf-8") == test_message


def test_handle_message_cpu(service):
    valid_request_data = {"query": {"bar": "test_bar"}, "body": {"mtype": "test_model"}}
    result = handle_message_cpu(service, valid_request_data)
    assert result == 1

    request_data = {"query": None, "body": {"mtype": "test_model"}}
    result = handle_message_cpu(service, request_data)
    assert result == "Field query cannot be None"

    # Test invalid field type
    request_data = {"query": {"bar": "test_bar"}, "body": "invalid_type"}
    result = handle_message_cpu(service, request_data)
    assert "Unexpected error" in result
    assert "argument after ** must be a mapping, not str" in result

    # Test missing field
    request_data = {"body": {"mtype": "test_model"}}
    result = handle_message_cpu(service, request_data)
    assert result == "Missing field: query"

    # Test unexpected error (non-JSON serializable return value)
    def mock_service(request):
        return object()  # Object is not JSON serializable

    request_data = {"query": {"bar": "test_bar"}, "body": {"mtype": "test_model"}}
    result = handle_message_cpu(mock_service, request_data)
    assert "Unexpected error" in result
    assert "Service returned a non-JSON serializable result" in result


@pytest.mark.asyncio
async def test_handle_message_io():
    # Define test data
    test_result = "test_result"
    test_response_channel = "test_channel"

    # Create a mock Redis connection
    mock_redis_conn = AsyncMock()

    # Patch the from_url method to return a mock Redis connection
    with patch("redis.asyncio.Redis", return_value=mock_redis_conn):
        # Patch the publish method directly in the handle_message_io function
        with patch.object(mock_redis_conn, "publish", new=AsyncMock()) as mock_publish:
            # Call the function to test
            await handle_message_io(test_result, test_response_channel)

            # Verify that the publish method was awaited with the correct parameters
            mock_publish.assert_awaited_once_with(
                test_response_channel,
                test_result,
            )


@pytest.mark.asyncio
async def test_process_service():
    mock_redis_channel = AsyncMock()
    # Create a simple message to process
    test_message = {
        "type": "message",
        "data": json.dumps(
            {
                "request_data": {
                    "query": {"bar": "test_bar"},
                    "body": {"mtype": "test_model"},
                },
                "response_channel": "test_response_channel",
                "log_key": "test_log_key",
            }
        ).encode("utf-8"),
    }

    # Create a mock queue
    queue = asyncio.Queue()

    # Insert the test message and the STOPWORD
    await queue.put(test_message)
    await queue.put(
        {"type": "message", "data": STOPWORD.encode("utf-8")}
    )  # Place STOPWORD

    # Patch the queue used in process_service
    with patch("main.asyncio.Queue", return_value=queue):
        # Patch the handle_message_io to observe the call directly
        with patch(
            "main.handle_message_io", new_callable=AsyncMock
        ) as mock_handle_message_io:
            # Run the process_service function
            task = asyncio.create_task(process_service(mock_redis_channel))

            await asyncio.sleep(0.1)

            await task  # Wait for the task to complete

            # Ensure the result was published via handle_message_io
            mock_handle_message_io.assert_called_once_with(1, "test_response_channel")


@pytest.mark.asyncio
async def test_redis_writer_logging():
    # Define a test log key
    log_key = "test_log_key"

    # Create a mock Redis connection
    mock_redis = AsyncMock()

    # Patch the async from_url method of redis to return the mock connection
    with patch("redis.asyncio.Redis", return_value=mock_redis):
        # Simulate writing to stdout using RedisWriter
        async with redirect_stdout(log_key) as redis_writer:
            print("Test log entry 1")
            print("Test log entry 2")

        print(mock_redis.hset.call_args_list)

        # Verify that the correct logs were written to Redis
        expected_logs = "Test log entry 1\nTest log entry 2\n"
        mock_redis.hset.assert_called_once_with(log_key, "logs", expected_logs)
