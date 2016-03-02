import asyncio
import certifi
import logging
import json
import ssl
import uuid

from behave import *
import websockets

log = logging.getLogger(__name__)


def wait_for(timeout, func, *args, **kwargs):
    """Block waiting for a a coroutine call to complete, with a timeout."""
    loop = asyncio.get_event_loop()
    task = asyncio.ensure_future(func(*args, **kwargs))
    try:
        loop.run_until_complete(asyncio.wait_for(task, timeout=timeout))
    except asyncio.TimeoutError as e:
        task.cancel()
        raise


async def connect(context):
    """Establish a websocket connection and send a client_id message."""
    endpoint = context.config.userdata['websocket_endpoint']
    verify = True
    if context.config.userdata['unsafe_disable_ssl_verification']:
        verify = False
    ssl_context = _ssl_context(verify=verify)
    context.websocket = await websockets.connect(endpoint, ssl=ssl_context)
    context.teardown.append(lambda: wait_for(10.0, context.websocket.close))


async def send(websocket, message):
    """JSON-encode and send a message over the websocket."""
    await websocket.send(json.dumps(message))


async def await_annotation(websocket, id):
    """Wait to see a notification about annotation with the given `id`"""
    while True:
        msg = await websocket.recv()
        try:
            data = json.loads(msg)
        except ValueError:
            log.warn('received non-JSON message: {!r}'.format(msg))
            continue

        if data.get('type') != 'annotation-notification':
            continue

        if data.get('options') != {'action': 'create'}:
            continue

        if 'payload' not in data:
            log.warn('saw annotation-notification lacking payload: {!r}'.format(msg))
            continue

        if not isinstance(data['payload'], list):
            log.warn('saw annotation-notification with bad payload format: {!r}'.format(msg))
            continue

        for annotation in data['payload']:
            if annotation.get('id') == id:
                return


@given('I am connected to the websocket')
def connect_websocket(context):
    wait_for(10.0, connect, context)
    wait_for(2.0, send, context.websocket, {
        'messageType': 'client_id',
        'value': str(uuid.uuid4()),
    })


@given('I request to be notified of all annotation events')
def request_notification_all(context):
    wait_for(2.0, send, context.websocket, {
        'filter': {
            'match_policy': 'include_all',
            'clauses': [],
            'actions': {'create': True, 'update': True, 'delete': True},
        }
    })


@then('I should receive notification of my test annotation on the websocket')
def wait_for_notification(context):
    try:
        getattr(context, 'last_test_annotation')
    except AttributeError:
        raise RuntimeError("you must create a test annotation first!")

    id = context.last_test_annotation['id']
    wait_for(5.0, await_annotation, context.websocket, id)


def _ssl_context(verify=True):
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    if not verify:
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
    return ssl_context
