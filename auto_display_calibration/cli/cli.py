from serial.tools import list_ports
import serial
import time

class UartPort:
    def __init__(self, port, baudrate=115200, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None

    def open(self):
        self.ser = serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            timeout=self.timeout
        )

    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()

    def send(self, cmd: str):
        data = (cmd + "\r").encode("ascii")
        self.ser.write(data)

    def set_port(self, port):
        self.port = port

# Windows: port="COM0"
_uart = UartPort(port="COM0", baudrate=115200)
# Linux: port="/dev/ttyUSB0"
#_uart = UartPort(port="/dev/ttyUSB0", baudrate=115200)

def detect_com_ports():
    """
    Detect all available UART / COM ports on system
    """
    ports = list_ports.comports()
    return [p.device for p in ports]

def enable_lcd(r, g, b, brightness):
    """
    UART version:
      - send: FILL RRGGBB\r
      - send: BL brightness\r
    """
    try:
        _uart.open()
    except Exception as e:
        print(f"[FAIL] Failed to open UART: {e}")
        return False

    try:
        # range check
        r = max(0, min(255, int(r)))
        g = max(0, min(255, int(g)))
        b = max(0, min(255, int(b)))
        brightness = max(0, min(100, int(brightness)))

        # RGB888 -> hex string
        rgb888 = f"{r:02X}{g:02X}{b:02X}"

        # Send commands
        _uart.send(f"FILL {rgb888}")
 
        # delay 100 ms
        time.sleep(0.1)
 
        # Send commands
        _uart.send(f"BL {brightness}")

        return True

    except Exception as e:
        print(f"[FAIL] UART Error: {e}")
        return False

    finally:
        _uart.close()
