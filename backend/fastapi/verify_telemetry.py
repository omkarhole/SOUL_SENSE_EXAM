import socket
import json
import threading
import time
import logging
from api.utils.telemetry import TelemetryExporter, BufferedTelemetryExporter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_telemetry")

def start_mock_collector(port: int, is_tcp: bool = False, stop_event: threading.Event = None):
    """
    Starts a mock telemetry collector that listens for incoming metrics.
    """
    if is_tcp:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("127.0.0.1", port))
        sock.listen(5)
        sock.settimeout(1.0)
    else:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("127.0.0.1", port))
        sock.settimeout(1.0)
    
    received_count = 0
    
    logger.info(f"Mock {'TCP' if is_tcp else 'UDP'} collector started on port {port}")
    
    while not stop_event.is_set():
        try:
            if is_tcp:
                try:
                    conn, addr = sock.accept()
                    data = conn.recv(4096)
                    if data:
                        # TCP receives a list of events in our implementation
                        events = json.loads(data.decode('utf-8').strip())
                        received_count += len(events)
                        # logger.info(f"TCP RECEIVED {len(events)} events. Total: {received_count}")
                    conn.close()
                except socket.timeout:
                    continue
            else:
                data, addr = sock.recvfrom(4096)
                if data:
                    received_count += 1
                    # logger.info(f"UDP RECEIVED 1 event. Total: {received_count}")
        except socket.timeout:
            continue
        except Exception as e:
            logger.error(f"Collector error: {e}")
            
    sock.close()
    return received_count

def run_test():
    stop_event = threading.Event()
    
    # 1. Test Standard UDP (vulnerable to loss)
    udp_port = 8125
    udp_thread = threading.Thread(target=start_mock_collector, args=(udp_port, False, stop_event))
    udp_thread.start()
    
    logger.info("--- Testing Standard UDP Exporter ---")
    standard_exporter = TelemetryExporter(port=udp_port)
    for i in range(10):
        standard_exporter.emit("test.metric", i)
    
    time.sleep(0.5)
    logger.info("Standard UDP emitted 10 packets.")

    # 2. Test Buffered TCP Exporter (reliable)
    tcp_port = 8126
    tcp_thread = threading.Thread(target=start_mock_collector, args=(tcp_port, True, stop_event))
    tcp_thread.start()
    
    logger.info("--- Testing Buffered TCP Exporter ---")
    buffered_exporter = BufferedTelemetryExporter(port=tcp_port, use_tcp=True)
    buffered_exporter.max_buffer_size = 5 # Small buffer for testing
    
    for i in range(12):
        buffered_exporter.emit("reliable.metric", i)
        if i == 4 or i == 9:
            logger.info(f"Buffered {i+1} metrics, should have triggered flush.")
            
    # Final flush for remaining 2 items
    buffered_exporter.flush()
    
    time.sleep(1.0)
    stop_event.set()
    udp_thread.join()
    tcp_thread.join()
    
    logger.info("Test completed successfully.")

if __name__ == "__main__":
    run_test()
