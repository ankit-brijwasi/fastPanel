from fastapi import WebSocket, APIRouter, WebSocketDisconnect
from websockets.exceptions import ConnectionClosedError
import motor.motor_asyncio as motor

from devduels.utils import ConnectionManager


router = APIRouter()


@router.post("/event/create")
async def create_event():
    return "hello"


@router.websocket("/ws/watch")
async def watch(websocket: WebSocket):
    manager = ConnectionManager()
    await manager.connect(websocket)
    db: motor.core.Database = websocket.app.db
    pipeline = [
        {
            "$match": {
                "$or": [
                    {"ns.coll": "participants"},
                    {"ns.coll": "events"},
                ],
                "$or": [
                    {"operationType": "insert"},
                    {"operationType": "delete"}
                ]
            }
        }
    ]
    try:
        async with db.watch(pipeline) as change_stream:
            async for change in change_stream:
                await manager.broadcast(change)

    except (WebSocketDisconnect, ConnectionClosedError):
        manager.disconnect(websocket)
