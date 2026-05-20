import json
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, request_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(request_id, []).append(websocket)

    def disconnect(self, request_id: str, websocket: WebSocket) -> None:
        conns = self._connections.get(request_id, [])
        if websocket in conns:
            conns.remove(websocket)
        if not conns:
            self._connections.pop(request_id, None)

    async def broadcast(self, request_id: str, message: dict[str, Any]) -> None:
        payload = json.dumps(message)
        dead: list[WebSocket] = []
        for ws in self._connections.get(request_id, []):
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(request_id, ws)


ws_manager = ConnectionManager()
