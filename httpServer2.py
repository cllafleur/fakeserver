# examples/server_simple.py
import time
from aiohttp import web
import os

async def rebuildRawRequest(req):
    request = f'{req.method} {req.raw_path} HTTP/{req.version.major}.{req.version.minor}\r\n'
    request += '\r\n'.join([f'{key}: {value}' for key,value in req.headers.items()])
    request += '\r\n' * 2
    request += (await req.content.read()).decode('utf-8')
    request = request.replace('\r\n', '<br>')
    return request

async def broadcastMessage(websockets, message):
    for user in websockets:
        if user.closed:
            websockets.remove(user)
        else:
            await user.send_str(message)

async def handle(request):
    if request.path == '/' or request.path == '/index.html':
        path = '/index.html'
        server_root = os.getcwd()
        full_path = os.path.realpath(os.path.join(server_root, path[1:]))
        body = open(full_path, 'rb').read()
        response = web.Response(headers={'Content-Length': str(len(body)), 'Content-Type': 'text/html'}, body=body)
        return response
    raw_request = await rebuildRawRequest(request)
    await broadcastMessage(request.app['websockets'], raw_request)
    time.sleep(request.app['responseDuration'])
    return web.Response(reason='Nice !!')

async def wshandle(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    request.app['websockets'].append(ws)

    async for msg in ws:
        if msg.type == web.WSMsgType.text:
            await ws.send_str("Hello, {}".format(msg.data))
        elif msg.type == web.WSMsgType.binary:
            await ws.send_bytes(msg.data)
        elif msg.type == web.WSMsgType.close:
            break
    return ws

async def setResponseDuration(request):
    duration = int(await request.content.read())
    request.app['responseDuration'] = duration
    return web.Response(reason='Duration set !')

async def getResponseDuration(request):
    duration = request.app['responseDuration']
    return web.Response(status=200, body=f'{duration}')

app = web.Application()
app.add_routes([web.get('/', handle),
                web.get('/settings/responseduration', getResponseDuration),
                web.put('/settings/responseduration', setResponseDuration),
                web.get('/echo', wshandle),
                web.get('/{name}', handle),
                web.post('/', handle),
                web.post('/{name}', handle)])
app['websockets'] = []
app['responseDuration'] = 0

if __name__ == '__main__':
    web.run_app(app, port=8080)