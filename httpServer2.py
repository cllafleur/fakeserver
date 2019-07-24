# examples/server_simple.py
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

    name = request.match_info.get('name', "Anonymous")
    text = "Hello, " + name
    return web.Response(text=text)

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

app = web.Application()
app.add_routes([web.get('/', handle),
                web.get('/echo', wshandle),
                web.get('/{name}', handle)])
app['websockets'] = []

if __name__ == '__main__':
    web.run_app(app, port=8080)