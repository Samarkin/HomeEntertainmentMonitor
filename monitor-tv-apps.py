#!/usr/bin/python3

import asyncio
import sys
from enum import Enum

import aiohttp
from aiopylgtv import WebOsClient
from aiohttp import web

# Constants
TV_IP = '192.168.1.123'
TV_MAC = '12:34:56:78:90:AB'
ONKYO_IP = '192.168.1.234'
PC_MAC = '12:34:56:78:90:CD'


class Timeouts:
    DISCONNECT = 3
    RECONNECT = 5
    RETRY_CONNECT = 3
    ONKYO_BOOT = 1
    TV_BOOT = 5

class Apps(Enum):
    PC = 'com.webos.app.hdmi4'
    Receiver = 'com.webos.app.hdmi3'

class PowerState:
    On = 'on'
    Off = 'off'
    Unknown = 'unknown'

class Onkyo:
    lock = asyncio.Lock()

    @staticmethod
    async def power_on():
        await Onkyo._send_request(0x4BB620DF)

    @staticmethod
    async def power_off():
        await Onkyo._send_request(0x4B36E21D)

    @staticmethod
    async def set_input_game():
        await Onkyo._send_request(0x4BB6B04F)

    @staticmethod
    async def set_input_tvcd():
        await Onkyo._send_request(0x4BB6906F)

    @staticmethod
    async def set_input_bddvd():
        await Onkyo._send_request(0x4B3631CE)

    @staticmethod
    async def _send_request(code):
        global stop_future
        try:
            async with Onkyo.lock:
                async with session.get((f"http://{ONKYO_IP}/ir?code={code}")):
                    pass
        except Exception as ex:
            try:
                stop_future.set_exception(ex)
            except asyncio.InvalidStateError:
                # already stopped
                pass


async def run(cmd):
    proc = await asyncio.create_subprocess_shell(cmd)
    await proc.wait()
    return proc.returncode


routes = web.RouteTableDef()


@routes.get('/tv')
async def getTvStatus(_):
    global tv_state, current_app
    try:
        input_name = Apps(current_app).name
    except ValueError:
        input_name = current_app
    return web.json_response({
        'state' : tv_state,
        'input': input_name,
    })


@routes.post('/tv/on')
async def turnTvOn(request):
    global client, tv_state
    turned_on = False
    if tv_state != PowerState.On:
        print("    Turning TV on")
        await run(f'wakeonlan -i {TV_IP} {TV_MAC}')
        turned_on = True
    input_name = request.query.get('input')
    if input_name:
        try:
            app = Apps[input_name].value
        except KeyError:
            return web.HTTPBadRequest()
        if turned_on:
            print("    Waiting for a while before switching TV inputs")
            await asyncio.sleep(Timeouts.TV_BOOT)
        await client.launch_app(app)
    return web.Response(text="OK")


@routes.post('/tv/off')
async def turnTvOff(_):
    global client, tv_state
    if tv_state == PowerState.On:
        await client.power_off()
    return web.Response(text="OK")


@routes.post('/pc/on')
async def turnPCOn(_):
    print("    Turning PC on")
    await run(f'wakeonlan {PC_MAC}')
    return web.Response(text="OK")


async def on_app_change(app):
    global current_app, tv_state
    if app == current_app:
        return
    print(f"  New input: {app}")
    prev_app,current_app = current_app,app
    if not prev_app and app:
        tv_state = PowerState.On
        print("    Turning Onkyo on")
        await Onkyo.power_on()
        print("    Waiting for a while before switching Onkyo inputs")
        await asyncio.sleep(Timeouts.ONKYO_BOOT)
    elif prev_app and not app:
        tv_state = PowerState.Off
        print("    Turning Onkyo off")
        await Onkyo.power_off()
        print("    Waiting for a while before doing anything else")
        await asyncio.sleep(Timeouts.ONKYO_BOOT)
        return

    if app == Apps.PC.value:
        print("    Switching Onkyo to PC")
        await Onkyo.set_input_game()
    elif app == Apps.Receiver.value:
        print("    Switching Onkyo to Tivo")
        await Onkyo.set_input_bddvd()
    elif not prev_app or prev_app == Apps.PC.value or prev_app == Apps.Receiver.value:
        print("    Switching Onkyo to TV")
        await Onkyo.set_input_tvcd()


async def on_state_change():
    global current_app
    app = client.current_appId

    #print(f"  [DEBUG] connected = {client.is_connected()} and app = {app}")
    await on_app_change(app)
    if app == None:
        try:
            stop_future.set_result(True)
        except asyncio.InvalidStateError:
            # already stopped
            pass


async def connect():
    global client
    client = await WebOsClient.create(TV_IP)
    await client.register_state_update_callback(on_state_change)
    await client.connect()


async def start_web():
    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', 12345).start()


async def main():
    global tv_state, current_app, stop_future, session
    tv_state = PowerState.Unknown
    current_app = None
    await start_web()
    async with aiohttp.ClientSession() as session:
        while True:
            print("Connecting...")
            tv_state = PowerState.Unknown
            current_app = None
            stop_future = asyncio.Future()
            try:
                await connect()
                await stop_future
                print("  Disconnected. I will sleep for a while and connect again")
                await asyncio.sleep(Timeouts.RECONNECT)
            except asyncio.CancelledError:
                break
            except:
                error_type, value, _ = sys.exc_info()
                print(f"  Error {error_type}: {value}")
                print("  I will sleep for a while and retry")
                await asyncio.sleep(Timeouts.RETRY_CONNECT)

asyncio.run(main())
