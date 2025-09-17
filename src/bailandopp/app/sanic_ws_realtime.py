from sanic import Sanic
from sanic.log import logger
import json
import time

app = Sanic("ai_agent_realtime")

@app.before_server_start
async def bootstrap(app, loop):
    logger.info("[BOOTSTRAP] Realtime WS ready.")

@app.websocket("/ws/dance")
async def ws_dance(request, ws):
    """
    Client -> server (JSON text):
      { "type": "ping" }
      { "type": "user_frame", "seq_num": 123, "timestamp_ms": 1710000000, "payload": { "joints": [72 floats] } }

    Server -> client (JSON text):
      { "type": "server_log", "payload": {"message": "..."} }
      { "type": "ai_frame", "seq_num": 123, "timestamp_ms": 1710000000, "payload": { "joints": [72 floats], "mode": "mimic" } }
    """
    logger.info("WS client connected")
    try:
        while True:
            msg = await ws.recv()
            try:
                env = json.loads(msg)
            except Exception as ex:
                await ws.send(json.dumps({"type":"error","payload":{"code":"bad_json","message":str(ex)}}))
                continue

            mtype = env.get("type")
            if mtype == "ping":
                await ws.send(json.dumps({"type":"server_log","payload":{"message":"pong"}}))
                continue

            if mtype == "user_frame":
                seq = env.get("seq_num")
                ts  = env.get("timestamp_ms", int(time.time()*1000))
                payload = env.get("payload", {})
                joints = payload.get("joints")

                if not isinstance(joints, list) or len(joints) != 72:
                    await ws.send(json.dumps({"type":"error","payload":{"code":"bad_payload","message":"joints must be 72 floats"}}))
                    continue

                # Echo back as ai_frame (mimic) for now
                await ws.send(json.dumps({
                    "type": "ai_frame",
                    "seq_num": seq,
                    "timestamp_ms": ts,
                    "payload": {"joints": joints, "mode": "mimic"}
                }))
                continue

            await ws.send(json.dumps({"type":"server_log","payload":{"message":f"recv {mtype}"}}))
    except Exception as ex:
        logger.warning(f"WS client disconnected or error: {ex}")
    finally:
        logger.info("WS client closed")

if __name__ == "__main__":
    # No protocol arg needed
    app.run(host="0.0.0.0", port=8000, debug=True)