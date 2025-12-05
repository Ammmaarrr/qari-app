from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


@router.websocket("/ws/recite")
async def websocket_recite(websocket: WebSocket):
    """WebSocket endpoint for real-time recitation analysis."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json(
                {
                    "status": "processing",
                    "interim_text": "بِسْمِ اللَّهِ",
                    "message": "Real-time analysis coming in Sprint 3",
                }
            )
    except WebSocketDisconnect:
        pass
