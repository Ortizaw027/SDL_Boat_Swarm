import serial
import time
import threading

class RYLR896:
    def __init__(self, port, baudrate=115200):
        self.ser = serial.Serial(port, baudrate, timeout=1)
        self.running = True

    def send_command(self, command):
        self.ser.write((command + '\r\n').encode())
        time.sleep(0.1)
        return self.ser.readline().decode(errors='ignore').strip()

    def set_address(self, address):
        return self.send_command(f'AT+ADDRESS={address}')

    def set_network_id(self, net_id):
        return self.send_command(f'AT+NETWORKID={net_id}')

    def send_data(self, recipient_address, message):
        # Number of bits is calculated based on 1 bit per character
        num_bits = len(message)  # Each character is 1 bit
        return self.send_command(f'AT+SEND={recipient_address},{num_bits},{message}')

    def receive_data(self):
        try:
            return self.ser.readline().decode(errors='ignore').strip()
        except UnicodeDecodeError:
            raw_data = self.ser.readline()  # Get the raw data as bytes
            print("Raw data received:", raw_data)  # Print the raw data for debugging
            return None  # Or return something else to indicate an error

    def reset(self):
        return self.send_command('AT+RESET')

    def check_connection(self):
        return self.send_command('AT')

    def close(self):
        self.ser.close()

    def listen_for_data(self):
        while self.running:
            received = self.receive_data()
            if received:
                print(f"Received data: {received}")

def get_valid_input(prompt, data_type=int):
    while True:
        user_input = input(prompt)
        try:
            if data_type == int:
                return int(user_input)
            elif data_type == str:
                return user_input.strip()
        except ValueError:
            print(f"Invalid input. Please enter a valid {data_type.__name__}.")

def main():
    # Replace '/dev/ttyS0' with the actual serial port of your RYLR896 module
    lora = RYLR896('/dev/ttyS0', baudrate=115200)

    print("Checking connection:", lora.check_connection())
    print("Resetting module:", lora.reset())

    # Set the LoRa address and network ID (static or user-defined)
    address = get_valid_input("Enter LoRa address (integer): ", int)
    network_id = get_valid_input("Enter LoRa network ID (integer): ", int)

    print("Setting address:", lora.set_address(address))
    print("Setting network ID:", lora.set_network_id(network_id))

    # Start a separate thread to listen for incoming data
    listen_thread = threading.Thread(target=lora.listen_for_data)
    listen_thread.daemon = True  # This will allow the thread to exit when the main program exits
    listen_thread.start()

    try:
        while True:
            # Get user input for recipient's address and message
            recipient_address = get_valid_input("Enter the recipient's address (integer): ", int)
            message_to_send = get_valid_input("Enter the message to send (string): ", str)

            # Send data with recipient's address and message
            print(f"Sending data to address {recipient_address}: {message_to_send}")
            print("Sending data:", lora.send_data(recipient_address, message_to_send))

            # Wait a little before allowing the next input or operation (adjust as needed)
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nExiting program...")
        lora.running = False  # Stop the listen thread gracefully
        lora.close()

if __name__ == '__main__':
    main()
