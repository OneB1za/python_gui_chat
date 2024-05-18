import asyncio
import threading
import websockets


class Client:
    def __init__(self, ip_address, gui):
        self.ip_address = ip_address
        self.websocket = None
        self.client_thread = None
        self.loop = None
        self.message_callback = None
        self.gui = gui
    async def connect_to_server(self):
        uri = f"ws://{self.ip_address}:8765"
        self.websocket = await websockets.connect(uri)
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

