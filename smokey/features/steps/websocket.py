import asyncio
import json
import logging
import ssl
import time
import uuid

import certifi
import websockets
from behave import given, then

log = logging.getLogger(__name__)


async def websocket_connect(endpoint, timeout=10, extra_headers=None, verify=True):
    """Establish a websocket connection and send a client_id message."""
    kwargs = {'extra_headers': extra_headers}
    if endpoint.startswith('wss://'):
        kwargs['ssl'] = _ssl_context(verify=verify)
    connect_coro = websockets.connect(endpoint, **kwargs)
    websocket = await asyncio.wait_for(connect_coro, timeout)
    await websocket.send(json.dumps({
        'messageType': 'client_id',
        'value': str(uuid.uuid4()),
    }))
    await websocket.send(json.dumps({
        'filter': {
            'match_policy': 'include_all',
            'clauses': [],
            'actions': {'create': True, 'update': True, 'delete': True},
        }
    }))
    return websocket


async def websocket_close(websocket, timeout=10):
    return await asyncio.wait_for(websocket.close(), timeout)


async def websocket_await_message(websocket, timeout=10):
    return await asyncio.wait_for(websocket.recv(), timeout)


def message_matches(msg, id):
    """Check if a websocket message is for the given annotation `id`."""
    try:
        data = json.loads(msg)
    except ValueError:
        log.warn('received non-JSON message: {!r}'.format(msg))
        return False

    if data.get('type') != 'annotation-notification':
        return False

    if data.get('options') != {'action': 'create'}:
        return False

    if 'payload' not in data:
        log.warn('saw annotation-notification lacking payload: {!r}'.format(msg))
        return False

    if not isinstance(data['payload'], list):
        log.warn('saw annotation-notification with bad payload format: {!r}'.format(msg))
        return False

    for annotation in data['payload']:
        if annotation.get('id') == id:
            return True
    return False


@given('I am listening for notifications on the websocket')
def listen_for_notifications(context):
    endpoint = context.config.userdata['websocket_endpoint']
    verify = not context.config.userdata['unsafe_disable_ssl_verification']

    # Use the same HTTP headers as requests -- this allows us to take
    # advantage of any Authorization headers set by the "I am acting as the
    # test user FOO" step
    extra_headers = {}
    if 'Authorization' in context.http.headers:
        extra_headers['Authorization'] = context.http.headers['Authorization']

    loop = asyncio.get_event_loop()
    connect_coro = websocket_connect(endpoint,
                                     extra_headers=extra_headers,
                                     verify=verify)
    context.websocket = loop.run_until_complete(connect_coro)

    # Perform a best effort clean up of the websocket at the end of the
    # scenario
    def cleanup():
        try:
            loop.run_until_complete(websocket_close(context.websocket))
        except:
            pass
    context.teardown.append(cleanup)


@then('I should receive a websocket notification within {delay:d}s')
def wait_for_notification(context, delay):
    try:
        getattr(context, 'last_test_annotation')
    except AttributeError:
        raise RuntimeError("you must create a test annotation first!")

    loop = asyncio.get_event_loop()
    id = context.last_test_annotation['id']
    deadline = time.monotonic() + delay

    while True:
        timeout = deadline - time.monotonic()
        if timeout <= 0:  # past the deadline
            break
        try:
            msg_coro = websocket_await_message(context.websocket, timeout)
            msg = loop.run_until_complete(msg_coro)
        except asyncio.TimeoutError:
            pass
        else:
            if message_matches(msg, id):
                return

    raise RuntimeError("timed out waiting for notification")


def _ssl_context(verify=True):
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    if not verify:
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
    return ssl_context
