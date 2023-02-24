import zmq

ctx = zmq.Context()
sck = ctx.socket(zmq.REQ)
address = "tcp://localhost:5678"
sck.connect(address)

sck.send_json({"command": "memeoftheday", "params": {}})
resp = sck.recv_json()
print(resp)
