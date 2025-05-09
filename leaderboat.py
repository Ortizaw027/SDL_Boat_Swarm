import time
import serial
import math
import smbus2
import pigpio

# --- Configuration Variables ---
# Serial port for the LoRa module
LORA_PORT = "/dev/serial0"
# Baudrate for serial communication with the LoRa module
BAUDRATE = 115200
# Unique address for this leader boat in the LoRa network
MY_ADDRESS = 100
# Address of the follower boat to send data to
DEST_ADDR = 101
# Network ID for the LoRa network (must match other devices)
NETWORK_ID = 5

# GPIO pins connected to the TB6612FNG motor driver
# AIN1, AIN2: Logic pins for Motor A direction
# BIN1, BIN2: Logic pins for Motor B direction
# PWMA, PWMB: PWM pins for Motor A and Motor B speed control
# STBY: Standby pin to enable/disable the motor driver
AIN1, AIN2, BIN1, BIN2 = 5, 10, 13, 19
PWMA, PWMB, STBY = 9, 26, 6

# PWM duty cycle value for forward movement (0-255)
FORWARD_PWM = 90
# PWM duty cycle value for turning (0-255)
TURN_PWM = 80
# Duration in seconds for forward movement in the route
FORWARD_TIME = 3
# Duration in seconds for turning in the route
TURN_TIME = 1.5

# Current state of the leader boat (IDLE or ACTIVE)
# IDLE: Waiting for START command
# ACTIVE: Executing the predefined route and broadcasting data
STATE = "IDLE"

# --- LoRa Module Class ---
# Handles serial communication with the RYLR896 LoRa module
class RYLR896:
    def __init__(self, port, baudrate=115200):
        # Initialize serial connection
        self.ser = serial.Serial(port, baudrate, timeout=2)

    # Send an AT command to the LoRa module and read the response
    def send_command(self, command):
        self.ser.write((command + '\r\n').encode())
        # Small delay to allow the module to process the command and respond
        time.sleep(0.2)
        # Read and return the response line, stripping whitespace
        return self.ser.readline().decode(errors='ignore').strip()

    # Configure the LoRa module's address and network ID
    def configure(self, address, network_id):
        self.send_command(f"AT+ADDRESS={address}")
        self.send_command(f"AT+NETWORKID={network_id}")
        # Reset the module to apply configuration changes
        self.send_command("AT+RESET")
        # Wait for the module to reset
        time.sleep(1)

    # Send data packet to a specific destination address
    def send_data(self, dest_addr, message):
        # Format the AT command for sending data
        command = f"AT+SEND={dest_addr},{len(message)},{message}\r\n"
        # Encode and write the command to the serial port
        self.ser.write(command.encode())

    # Check for and receive data from the LoRa module
    def receive_data(self):
        # Check if there is data waiting in the serial buffer
        if self.ser.in_waiting:
            # Read a line from the serial buffer and return it
            return self.ser.readline().decode(errors='ignore').strip()
        # Return None if no data is available
        return None

# --- Hardware Initialization ---
# Initialize pigpio library
pi = pigpio.pi()

# Set motor control pins as outputs using pigpio
for pin in [AIN1, AIN2, BIN1, BIN2, STBY]:
    pi.set_mode(pin, pigpio.OUTPUT)

# Initialize I2C bus for the compass sensor
bus = smbus2.SMBus(1)
# Configure the HMC5883L compass sensor
# 0x1E is the default I2C address
# 0x00 (CONFIG_REG_A): 0x70 sets 8-average, 75 Hz, Normal Measurement
bus.write_byte_data(0x1E, 0x00, 0x70)
# 0x01 (CONFIG_REG_B): 0xA0 sets Gain = 5, Range = +/- 4.7 Gauss (adjust as needed)
bus.write_byte_data(0x1E, 0x01, 0xA0)
# 0x02 (MODE_REG): 0x00 sets Continuous Measurement Mode
bus.write_byte_data(0x1E, 0x02, 0x00)

# Initialize the LoRa module
lora = RYLR896(LORA_PORT, BAUDRATE)
# Configure the LoRa module with the boat's address and network ID
lora.configure(MY_ADDRESS, NETWORK_ID)

# --- Sensor Reading Functions ---
# Read heading data from the HMC5883L compass sensor
def read_heading():
    try:
        # Read raw data from the sensor (X, Z, Y) registers
        data = bus.read_i2c_block_data(0x1E, 0x03, 6)
        # Combine bytes to form 16-bit signed integers for X and Y axes
        x = (data[0] << 8) | data[1]
        y = (data[4] << 8) | data[5]

        # Convert raw data to signed integers (two's complement)
        if x >= 32768: x -= 65536
        if y >= 32768: y -= 65536

        # Calculate heading in radians using arctan2 (Y, X)
        # Convert radians to degrees
        heading = math.degrees(math.atan2(y, x))

        # Normalize heading to 0-360 degrees
        return heading + 360 if heading < 0 else heading
    except Exception as e:
        # Print error if reading or calculation fails
        print(f"Error reading compass: {e}")
        # Return 0.0 or last known heading in a real application
        return 0.0

# --- Motor Control Functions ---
# Move the boat straight forward
def move_forward():
    # Enable the motor driver
    pi.write(STBY, 1)
    # Set direction to forward for both motors
    pi.write(AIN1, 1); pi.write(AIN2, 0) # Motor A Forward
    pi.write(BIN1, 1); pi.write(BIN2, 0) # Motor B Forward
    # Set PWM duty cycle for forward speed
    pi.set_PWM_dutycycle(PWMA, FORWARD_PWM)
    pi.set_PWM_dutycycle(PWMB, FORWARD_PWM)
    print("Moving Forward")

# Turn the boat left
def turn_left():
    # Enable the motor driver
    pi.write(STBY, 1)
    # Set direction for turning left (Motor A Reverse, Motor B Forward)
    pi.write(AIN1, 0); pi.write(AIN2, 1) # Motor A Reverse
    pi.write(BIN1, 1); pi.write(BIN2, 0) # Motor B Forward
    # Set PWM duty cycle for turning speed
    pi.set_PWM_dutycycle(PWMA, TURN_PWM)
    pi.set_PWM_dutycycle(PWMB, TURN_PWM)
    print("Turning Left")

# Stop both motors and disable the motor driver
def stop_motors():
    pi.set_PWM_dutycycle(PWMA, 0) # Set PWM to 0
    pi.set_PWM_dutycycle(PWMB, 0)
    pi.write(STBY, 0) # Disable the motor driver
    print("Motors Stopped")

# --- Main Loop ---
print("Leader ready - IDLE until CMD,START received...")

try:
    # Infinite loop to continuously check for commands and execute the route
    while True:
        # Attempt to receive data (commands) from the LoRa module
        incoming = lora.receive_data()

        # Check if data was received and it's a valid RCV message
        if incoming and incoming.startswith("+RCV="):
            print(f"Received RAW LoRa data: {incoming}")
            try:
                # Remove the "+RCV=" prefix and split the message by commas
                parts = incoming.replace("+RCV=", "").split(",")

                # --- Command Handling ---
                # Expected format for commands: +RCV=<sender>,<length>,CMD,<command>
                if len(parts) >= 4 and parts[2] == "CMD":
                    command = parts[3].strip().upper()
                    # If START command is received
                    if command == "START":
                        print("START command received! Entering ACTIVE state.")
                        STATE = "ACTIVE"
                    # If STOP command is received
                    elif command == "STOP":
                        print("STOP command received! Entering IDLE state.")
                        STATE = "IDLE"
                        # Stop motors immediately when STOP is received
                        stop_motors()
                    # Continue to the next loop iteration after processing a command
                    continue # Skip the rest of the loop to process the next incoming message

            except ValueError as e:
                # Handle errors during data parsing
                print(f"Data parse error: {e}")
            except IndexError as e:
                # Handle errors if message format is unexpected
                print(f"Index error parsing message: {e}")
            except Exception as e:
                # Catch any other unexpected errors during processing
                print(f"An unexpected error occurred during command processing: {e}")

        # --- Route Execution and Data Broadcasting (only if in ACTIVE state) ---
        if STATE == "ACTIVE":
            # Execute a segment of the predefined route (move forward)
            move_forward()
            time.sleep(FORWARD_TIME)

            # Execute a segment of the predefined route (turn left)
            turn_left()
            time.sleep(TURN_TIME)

            # Stop motors briefly between movements (optional, depends on route design)
            stop_motors()
            # Small delay after stopping before sending data
            time.sleep(0.5)

            # --- Data Broadcasting ---
            # Get current position (using dummy values for now)
            # In a real implementation, this would come from a GPS module
            lat, lon = 43.138460, -75.232241
            # Read current heading from the compass sensor
            heading = read_heading()

            # Create the message string to send to the follower(s)
            # Format: LEADER,<latitude>,<longitude>,<heading>
            # RSSI will be automatically added by the LoRa module upon reception by the follower
            message = f"LEADER,{lat:.6f},{lon:.6f},{heading:.2f}"
            # Send the message to the destination address (follower boat)
            lora.send_data(DEST_ADDR, message)
            print(f"Sent Leader data to {DEST_ADDR}: {message}")

            # Small delay after sending data before the next route segment
            time.sleep(1)

        else:
            # If in IDLE state, just wait briefly before checking for commands again
            time.sleep(0.2)

# --- Cleanup on Exit ---
except KeyboardInterrupt:
    # Handle Ctrl+C to stop the script gracefully
    print("Stopping leader...")
    # Stop the motors
    stop_motors()
    # Close the serial connection to the LoRa module
    lora.ser.close()
    # Stop the pigpio daemon connection
    pi.stop()
except Exception as e:
    # Catch any other unexpected errors during execution
    print(f"An unexpected error caused the program to stop: {e}")
    # Attempt to clean up resources
    stop_motors()
    if lora.ser and lora.ser.isOpen():
        lora.ser.close()
    pi.stop()
