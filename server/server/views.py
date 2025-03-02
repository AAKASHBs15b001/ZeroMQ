from django.http import JsonResponse
from .heartbeat_handler import HeartbeatServer

server = HeartbeatServer(zmq_port=5555)

def active_devices(request):
    """API to list active devices"""
    active_devices = list(server.devices.keys())
    return JsonResponse({"active_devices": active_devices})
