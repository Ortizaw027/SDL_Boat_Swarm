import serial
import time

# Configuration
LORA_PORT = "/dev/serial0"  # LoRa module serial port
USB_PORT = "/dev/ttyGS0"    # USB gadget serial port
BAUDRATE = 115200

# Initialize serial connections
lora_ser = serial.Serial(LORA_PORT, BAUDRATE, timeout=1)
usb_ser = serial.Serial(USB_PORT, BAUDRATE, timeout=1)

print("Controller is running. Awaiting commands...")

try:
    while True:
        # Read from USB (commands from GUI)
        if usb_ser.in_waiting:
            cmd = usb_ser.readline().decode().strip()
            if cmd in ["CMD,START", "CMD,STOP"]:
                # Send command to both boats
                for addr in [100, 101]:
                    msg = f"AT+SEND={addr},{len(cmd)},{cmd}\r\n"
                    lora_ser.write(msg.encode())
                    print(f"Sent to {addr}: {cmd}")
            else:
                print(f"Unknown command: {cmd}")

        # Read from LoRa (data from boats)
        if lora_ser.in_waiting:
            incoming = lora_ser.readline().decode().strip()
            if incoming.startswith("+RCV="):
                print(f"Received: {incoming}")
                # Forward to GUI
                usb_ser.write((incoming + "\n").encode())

        time.sleep(0.1)

except KeyboardInterrupt:
    print("Shutting down controller...")
    lora_ser.close()
    usb_ser.close()

