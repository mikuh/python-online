from aiohttp import web
import aiohttp
import paramiko
import threading
import aiohttp_cors
import asyncio


async def rev_send(socket):
    while not socket.ws.closed:
        asyncio.sleep(0.1)
        try:
            data = socket.shell.recv(8192)
            await socket.ws.send_bytes(data)
        except Exception as e:
            print(type(e), str(e))


def start_loop(loop):
    loop.run_forever()


def sftp_exec_command(ssh_client, command):
    try:
        std_in, std_out, std_err = ssh_client.exec_command(command, timeout=4)
        out = "".join([line for line in std_out])
        return out
    except Exception as e:
        print(e)
    return None


async def coding(request):
    data = await request.json()
    code_id = data["code_id"]
    code = data["code"]

    host = data["host"]
    port = int(data['port'])
    user = data['username']
    password = data['password']

    # code 不转义处理
    code = code.replace('"', '\\"')

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(host, port, user, password)
    sftp_exec_command(ssh_client, f"mkdir -p ~/{code_id}")
    sftp_exec_command(ssh_client, f"echo \"{code}\" > ~/{code_id}/main.py")
    ssh_client.close()
    return web.json_response(
        {"data": {"ssh_command": f"python ~/{code_id}/main.py"}, "error_code": 0, "msg": "ok"})


class WebSocketHandler(web.View, aiohttp_cors.CorsViewMixin):

    async def get(self):
        self.ws = web.WebSocketResponse()
        await self.ws.prepare(self.request)
        data = self.request.query
        host = data["host"]
        port = int(data['port'])
        user = data['username']
        password = data['password']
        self.sshclient = paramiko.SSHClient()
        self.sshclient.load_system_host_keys()
        self.sshclient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.sshclient.connect(host, port, user, password)
        self.shell = self.sshclient.invoke_shell(term='xterm')
        self.shell.settimeout(90)
        self.status = True

        new_loop = asyncio.new_event_loop()
        t = threading.Thread(target=start_loop, args=(new_loop,))
        t.start()

        asyncio.run_coroutine_threadsafe(rev_send(self), new_loop)

        async for msg in self.ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                if msg.data == 'close':
                    await self.ws.close()
                else:
                    self.shell.send(msg.data)
            elif msg.type == aiohttp.WSMsgType.ERROR:
                print('ws connection closed with exception %s' %
                      self.ws.exception())
            elif msg.type == aiohttp.WSMsgType.CLOSE:
                break

        print('websocket connection closed')
        new_loop.stop()
        print(t.is_alive())
        return self.ws


app = web.Application()

app.router.add_routes([web.view('/terminals/', WebSocketHandler), web.post('/coding', coding), ])

cors = aiohttp_cors.setup(
    app,
    defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
    })
for route in list(app.router.routes()):
    cors.add(route)

web.run_app(app, host="127.0.0.1", port=3000)
