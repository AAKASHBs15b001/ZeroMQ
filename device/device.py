import zmq
import time
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Get environment variables
SERVER_IP = os.getenv("SERVER_IP", "server1")
DEVICE_ID = os.getenv("DEVICE_ID", "device1")

def start_device():
    """Device sends heartbeats to the server periodically."""
    context = zmq.Context()
    socket = context.socket(zmq.DEALER)
    socket.setsockopt_string(zmq.IDENTITY, DEVICE_ID)

    server_address = f"tcp://{SERVER_IP}:5555"
    logging.info(f"📡 Device {DEVICE_ID} connecting to {server_address}...")
    socket.connect(server_address)

    try:
        while True:
            socket.send_multipart([DEVICE_ID.encode(), b"heartbeat"])
            logging.info(f"💓 Heartbeat sent from {DEVICE_ID} to {SERVER_IP}")
            time.sleep(5)

    except KeyboardInterrupt:
        logging.warning(f"⚠️ Device {DEVICE_ID} stopped manually!")

if __name__ == "__main__":
    start_device()
