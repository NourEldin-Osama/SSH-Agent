import json

active_connections: dict[str, list] = {}


async def broadcast_to_session(session_id: str, event: str, data: dict):
    message = json.dumps({"event": event, "data": data}, default=str)
    if session_id in active_connections:
        dead = []
        for conn in active_connections[session_id]:
            try:
                await conn.send_text(message)
            except Exception:
                dead.append(conn)
        for conn in dead:
            active_connections[session_id].remove(conn)
