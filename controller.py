import serial
import time

# LoRa module configuration
LORA_PORT = "/dev/ttyUSB0"  # Adjust based on your system
BAUDRATE = 115200
MY_ADDRESS = 200            # Controller's unique address
NETWORK_ID = 5              # Shared network ID with boats

# Initialize serial connection to LoRa module
ser = serial.Serial(LORA_PORT, BAUDRATE, timeout=2)

def send_command(command):
    """
    Sends a command to the LoRa module and reads the response.
    """
    ser.write((command + '\r\n').encode())
    time.sleep(0.2)
    return ser.readline().decode(errors='ignore').strip()

def configure_lora():
    """
    Configures the LoRa module with the controller's address and network ID.
    """
    send_command(f"AT+ADDRESS={MY_ADDRESS}")
    send_command(f"AT+NETWORKID={NETWORK_ID}")
    send_command("AT+RESET")
    time.sleep(1)

def send_lora_message(dest_addr, message):
    """
    Sends a message to a specific destination address via LoRa.
    """
    command = f"AT+SEND={dest_addr},{len(message)},{message}\r\n"
    ser.write(command.encode())

def receive_lora_data():
    """
    Checks for incoming data from the LoRa module.
    """
    if ser.in_waiting:
        return ser.readline().decode(errors='ignore').strip()
    return None

def main():
    """
    Main loop to handle sending and receiving LoRa messages.
    """
    configure_lora()
    print("Controller is running. Press Ctrl+C to exit.")

    try:
        while True:
            incoming = receive_lora_data()
            if incoming:
                print(f"Received: {incoming}")
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Shutting down controller.")
    finally:
        ser.close()

if __name__ == "__main__":
    main()
