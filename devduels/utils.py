import json

from typing import List
from fastapi import WebSocket

from fastpanel.core.serializers import FastPanelJSONEncoder


class ConnectionManager:
    active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        message = json.dumps(message, cls=FastPanelJSONEncoder)
        print(message)
        for connection in self.active_connections:
            await connection.send({"type": "websocket.send", "text": message})
