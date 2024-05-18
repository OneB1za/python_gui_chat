import asyncio
import socket
import threading
import websockets
import ipaddress


class Server:
    def __init__(self, gui):
        self.server = None
        self.loop = None
        self.connected = set()
        self.server_started = threading.Event()
        self.gui = gui

    def get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP

    async def send_message_in_chat(self, message):
        if self.connected:
            print(f'server {message}')
            for websocket in self.connected:
                await websocket.send(message)

    async def chat_server(self, websocket, path):
        ip = websocket.remote_address[0]
        # conn_tuple = (websocket, ip)
        self.connected = {conn for conn in self.connected if conn.remote_address[0] != ip}
        self.connected.add(websocket)
        try:
            # await self.send_message_in_chat(message=f'Пользователь {ip} присоединился к чату.')
            async for message in websocket:
                await self.send_message_in_chat(message)
        except websockets.exceptions.ConnectionClosedError:
            print(f"Соединение с пользователем {ip} было закрыто.")
        finally:
            self.connected.remove(websocket)
            await self.send_message_in_chat(f'Пользователь {ip} покинул чат.')

    async def start_server(self):
        self.server = await websockets.serve(self.chat_server, host=self.get_local_ip(), port=8765)
        self.server_started.set()
        try:
            await self.server.wait_closed()
        except asyncio.CancelledError:
            print("Сервер был остановлен.")

    def run_server(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self.start_server())
        finally:
            self.loop.close()

    def stop_server(self):
        self.loop.call_soon_threadsafe(self.server.close)
        future = asyncio.run_coroutine_threadsafe(self.server.wait_closed(), self.loop)
        future.result(timeout=10)
        self.server_started.clear()
