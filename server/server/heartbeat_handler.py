import zmq
import redis
import logging
import time
import threading
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Redis Config
REDIS_HOST = "redis"
REDIS_PORT = 6379
HEARTBEAT_TIMEOUT = 10  # If no heartbeat for 10 seconds, mark as disconnected
CHECK_INTERVAL = 5  # Check for disconnected devices every 5 seconds

class HeartbeatServer:
    def __init__(self, port="5555"):
        """Initialize the heartbeat server with Redis."""
        self.port = port
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.ROUTER)
        self.socket.bind(f"tcp://*:{self.port}")

        # Set a timeout for receiving messages so we can check for disconnections
        self.socket.setsockopt(zmq.RCVTIMEO, CHECK_INTERVAL * 1000)  # Timeout every 5 seconds

        # Connect to Redis
        self.redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

        logging.info(f"🚀 Server started on port {self.port}, waiting for heartbeats...")

    def check_disconnected_devices(self):
        """Check for devices that have not sent a heartbeat within the timeout period."""
        logging.info("🔄 Starting disconnection checker thread...")
        while True:
            try:
                current_time = datetime.now().timestamp()
                devices = self.redis_client.hgetall("active_devices")

                for device_id, last_seen in devices.items():
                    last_seen = float(last_seen)
                    if current_time - last_seen > HEARTBEAT_TIMEOUT:
                        logging.warning(f"⚠️ Device {device_id} is DISCONNECTED! No heartbeat received for {HEARTBEAT_TIMEOUT} seconds.")
                        self.redis_client.hdel("active_devices", device_id)  # Remove from Redis

                time.sleep(CHECK_INTERVAL)  # Check every 5 seconds
            except Exception as e:
                logging.error(f"❌ Error in disconnection checker thread: {e}")

    def start(self):
        """Start listening for heartbeats and run the disconnection checker."""
        # Start the background thread for disconnection detection
        disconnection_thread = threading.Thread(target=self.check_disconnected_devices, daemon=True)
        disconnection_thread.start()

        while True:
            try:
                try:
                    message_parts = self.socket.recv_multipart()
                except zmq.error.Again:
                    # Timeout occurred, no message received, continue checking disconnections
                    # logging.info("⌛ No heartbeat received in the last 5 seconds...")
                    continue

                # if len(message_parts) != 2:
                #     logging.warning(f"🚨 Malformed message received: {message_parts}")
                #     continue

                device_id = message_parts[0].decode()
                message = message_parts[1].decode()

                
                self.redis_client.hset("active_devices", device_id, datetime.now().timestamp())
                logging.info(f"✅ Heartbeat received from {device_id}")

            except Exception as e:
                logging.error(f"❌ Error in heartbeat handler: {e}")

if __name__ == "__main__":
    server = HeartbeatServer()
    server.start()
