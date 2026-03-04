import socket
import json
import time
import uuid
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("telemetry")

class TelemetryExporter:
    """
    Standard UDP Telemetry Exporter.
    Simulates a generic StatsD/Datadog style exporter that has been
    causing packet loss issues in production (#1193).
    """
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8125):
        self.host = host
        self.port = port
        self.addr = (host, port)
        # Create a standard UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # In standard UDP, we don't 'connect', but we can pre-set the address
        logger.info(f"Telemetry standard UDP exporter initialized: {host}:{port}")

    def emit(self, event_name: str, value: Any, tags: Optional[Dict[str, str]] = None):
        """
        Emit a metric via UDP. 
        In standard UDP, if the packet is dropped by the OS or Network, it's gone.
        """
        payload = {
            "metric": event_name,
            "value": value,
            "tags": tags or {},
            "timestamp": time.time(),
            "id": str(uuid.uuid4())
        }
        data = json.dumps(payload).encode('utf-8')
        
        try:
            # We use sendto because it's UDP
            self.sock.sendto(data, self.addr)
        except Exception as e:
            # Usually UDP sendto doesn't error unless the message is too large
            # or the interface is down. Network congestion drops happen silently AFTER this.
            logger.error(f"UDP emission failed: {e}")

class BufferedTelemetryExporter:
    """
    Improved Telemetry Exporter with Buffering and Retry Mechanism (#1193).
    Switching to TCP or Reliable UDP (simulated here via retries and buffering).
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 8126, use_tcp: bool = True):
        self.host = host
        self.port = port
        self.addr = (host, port)
        self.use_tcp = use_tcp
        self.buffer = []
        self.max_buffer_size = 50
        self.max_retries = 3
        
        if self.use_tcp:
            # TCP is inherently reliable
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connected = False
        else:
            # Reliable UDP simulation
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.connected = True
            
        logger.info(f"Buffered Telemetry Exporter ({'TCP' if use_tcp else 'Reliable UDP'}) initialized: {host}:{port}")

    def _connect(self):
        if not self.use_tcp or self.connected:
            return True
        try:
            self.sock.settimeout(2.0)
            self.sock.connect(self.addr)
            self.connected = True
            return True
        except Exception as e:
            logger.warning(f"Failed to connect to telemetry collector via TCP: {e}")
            self.connected = False
            return False

    def emit(self, event_name: str, value: Any, tags: Optional[Dict[str, str]] = None):
        """Add event to buffer and flush if full."""
        payload = {
            "metric": event_name,
            "value": value,
            "tags": tags or {},
            "timestamp": time.time(),
            "id": str(uuid.uuid4())
        }
        self.buffer.append(payload)
        
        if len(self.buffer) >= self.max_buffer_size:
            self.flush()

    def flush(self):
        """Attempt to send buffered metrics with retries."""
        if not self.buffer:
            return

        if self.use_tcp:
            self._flush_tcp()
        else:
            self._flush_udp_reliable()

    def _flush_tcp(self):
        if not self._connect():
            # If we can't connect, keep in buffer (simulating persistence or just wait)
            if len(self.buffer) > 1000: # Don't grow indefinitely
                self.buffer = self.buffer[-500:]
            return

        data = json.dumps(self.buffer).encode('utf-8') + b"\n"
        retries = 0
        while retries <= self.max_retries:
            try:
                self.sock.sendall(data)
                self.buffer = []
                # logger.debug("Successfully flushed TCP telemetry")
                return
            except Exception as e:
                retries += 1
                self.connected = False
                logger.warning(f"TCP flush attempt {retries} failed: {e}")
                if not self._connect():
                    break
                time.sleep(0.1 * retries)

    def _flush_udp_reliable(self):
        """Simulates reliable UDP by sending packets multiple times or logging failures."""
        # For true reliable UDP we'd need ACKs, but simple retries/redundancy can help
        # or just switching to TCP as we did above is better.
        for item in self.buffer:
            data = json.dumps(item).encode('utf-8')
            sent = False
            for r in range(self.max_retries + 1):
                try:
                    self.sock.sendto(data, self.addr)
                    sent = True
                    break
                except Exception:
                    time.sleep(0.01)
        self.buffer = []

# Global instance
_exporter = None

def get_telemetry_exporter():
    global _exporter
    if _exporter is None:
        from ..config import get_settings_instance
        settings = get_settings_instance()
        # Toggle based on settings if needed, default to new reliable one
        use_reliable = getattr(settings, "TELEMETRY_RELIABLE", True)
        if use_reliable:
            _exporter = BufferedTelemetryExporter(
                host=getattr(settings, "TELEMETRY_HOST", "127.0.0.1"),
                port=getattr(settings, "TELEMETRY_PORT", 8126),
                use_tcp=True
            )
        else:
            _exporter = TelemetryExporter()
    return _exporter
