import asyncio
import json
import logging
import multiprocessing
import queue
import ssl
import time
import uuid

import certifi
import websockets
from behave import given, then

log = logging.getLogger(__name__)


def tail_websocket(endpoint, queue, ready, close, verify=True):
    loop = asyncio.get_event_loop()
    coro = enqueue_websocket_messages(endpoint, queue, ready, close, verify)
    loop.run_until_complete(coro)


async def enqueue_websocket_messages(endpoint, queue, ready, close, verify=True):
    websocket = await connect(endpoint, verify)
    pending = {websocket.recv()}

    # signal to the controlling process that we're ready
    ready.set()

    while True:
        done, pending = await asyncio.wait(pending, timeout=0.1)

        if done:
            for msg in done:
                queue.put_nowait(msg.result())
            pending.add(websocket.recv())

        if close.is_set():
            break

    for msg in pending:
        msg.cancel()
    await websocket.close()


async def connect(endpoint, verify=True):
    """Establish a websocket connection and send a client_id message."""
    ssl_context = _ssl_context(verify=verify)
    websocket = await websockets.connect(endpoint, ssl=ssl_context)
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

    messages = multiprocessing.Queue(maxsize=1000)
    close = multiprocessing.Event()  # signal shutdown to the remote process
    ready = multiprocessing.Event()  # remote process signals readiness to us
    websocket = multiprocessing.Process(target=tail_websocket,
                                        args=(endpoint, messages, ready, close),
                                        kwargs={'verify': verify})
    websocket.start()

    if not ready.wait(5.0):
        raise RuntimeError('failed to connect to websocket in 5s')

    context.websocket = websocket
    context.websocket_messages = messages

    # When we teardown the test context, we set the "close" event, which will
    # trigger clean websocket shutdown, and then wait for the process to
    # complete.
    def cleanup():
        close.set()
        websocket.join()
    context.teardown.append(cleanup)


@then('I should receive a websocket notification within {delay:d}s')
def wait_for_notification(context, delay):
    try:
        getattr(context, 'last_test_annotation')
    except AttributeError:
        raise RuntimeError("you must create a test annotation first!")

    id = context.last_test_annotation['id']
    timeout = time.time() + delay

    while True:
        try:
            msg = context.websocket_messages.get(timeout=0.1)
        except queue.Empty:
            if time.time() > timeout:
                break
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
