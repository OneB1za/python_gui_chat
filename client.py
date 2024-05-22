import asyncio
import json
import threading
import websockets


class Client:
    def __init__(self, ip_address, gui, username):
        self.ip_address = ip_address
        self.websocket = None
        self.username = username

        self.client_thread = None
        self.loop = None
        self.gui = gui

        if not self.username: # todo
            ValueError("Авторизуйтесь перед тем как зайти в чат")

    async def connect_to_server(self):
        uri = f"ws://{self.ip_address}:8765"
        self.websocket = await websockets.connect(uri)
        await self.websocket.send(json.dumps({'username': self.username}))
        print(f'Connected to {self.ip_address}')

    def send_message(self, message):
        asyncio.run_coroutine_threadsafe(self._send_message(message), self.loop)

    async def _send_message(self, message):
        await self.websocket.send(message)

    async def receive_message(self):
        try:
            while True:
                message = await self.websocket.recv()
                self.gui.update_chat_window(message)
                print(f'receive {message}')
        except websockets.exceptions.ConnectionClosed:
            print('Клиент отключился от сервера')

    def start_client_thread(self):
        self.client_thread = threading.Thread(target=self.run_client)
        self.client_thread.start()

    def run_client(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.connect_to_server())
        self.loop.run_until_complete(self.receive_message())

    def stop_client_thread(self):
        if self.websocket:
            self.websocket.close()
            self.websocket = None
            if self.gui.server_instance:
                self.gui.server_instance.connected.discard(self.websocket)
