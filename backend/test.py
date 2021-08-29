import zmq

ctx = zmq.Context()
sck = ctx.socket(zmq.REQ)
sck.connect("ipc://endpoint.ipc")
print(f"Socket bound")

sck.send_json({
    "command": "say_test",
    "params": {
        "text": "Give me a slap daddy"
    }
})
print(sck.recv_json())
