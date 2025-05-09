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
# Unique address for this follower boat in the LoRa network
MY_ADDRESS = 101
# Network ID for the LoRa network (must match other devices)
NETWORK_ID = 5

# GPIO pins connected to the TB6612FNG motor driver
# AIN1, AIN2: Logic pins for Motor A direction
# BIN1, BIN2: Logic pins for Motor B direction
# PWMA, PWMB: PWM pins for Motor A and Motor B speed control
# STBY: Standby pin to enable/disable the motor driver
AIN1, AIN2, BIN1, BIN2 = 5, 10, 13, 19
PWMA, PWMB, STBY = 9, 26, 6

# Tolerance in degrees for heading alignment before driving straight
HEADING_TOLERANCE = 5
# Balance factors for left and right motor speeds (adjust for calibration)
LEFT_MOTOR_BALANCE = 1.0
RIGHT_MOTOR_BALANCE = 1.0

# RSSI thresholds for distance control
# If RSSI is greater than RSSI_CLOSE, the boat is too close
# If RSSI is less than RSSI_FAR, the boat is too far
RSSI_CLOSE = -50
RSSI_FAR = -75
# Minimum and maximum PWM values for motor speed control
PWM_MIN = 70
PWM_MAX = 100
# Variable to store the current motor PWM duty cycle
current_pwm = 90

# Current state of the follower boat (IDLE or ACTIVE)
# IDLE: Waiting for START command
# ACTIVE: Following the leader and maintaining formation
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
# Drive the motors based on heading difference and PWM speed
def drive_motors(diff, pwm):
    # Enable the motor driver
    pi.write(STBY, 1)

    # Check if the heading difference is within the tolerance
    if abs(diff) <= HEADING_TOLERANCE:
        # Drive straight forward
        pi.write(AIN1, 1); pi.write(AIN2, 0) # Motor A Forward
        pi.write(BIN1, 1); pi.write(BIN2, 0) # Motor B Forward
        print("Driving Straight")
    # If the heading difference is positive, turn right
    elif diff > 0:
        # Turn right (Motor A Forward, Motor B Reverse)
        pi.write(AIN1, 1); pi.write(AIN2, 0) # Motor A Forward
        pi.write(BIN1, 0); pi.write(BIN2, 1) # Motor B Reverse
        print("Turning Right")
    # If the heading difference is negative, turn left
    else:
        # Turn left (Motor A Reverse, Motor B Forward)
        pi.write(AIN1, 0); pi.write(AIN2, 1) # Motor A Reverse
        pi.write(BIN1, 1); pi.write(BIN2, 0) # Motor B Forward
        print("Turning Left")

    # Set the PWM duty cycle for both motors, applying balance factors
    # Duty cycle should be between 0 and 255
    pi.set_PWM_dutycycle(PWMA, int(pwm * LEFT_MOTOR_BALANCE))
    pi.set_PWM_dutycycle(PWMB, int(pwm * RIGHT_MOTOR_BALANCE))

# Stop both motors and disable the motor driver
def stop_motors():
    pi.set_PWM_dutycycle(PWMA, 0) # Set PWM to 0
    pi.set_PWM_dutycycle(PWMB, 0)
    pi.write(STBY, 0) # Disable the motor driver
    print("Motors Stopped")

# --- Main Loop ---
print("Follower ready and waiting for START command...")

# Variable to store the last received heading from the leader
last_leader_heading = None

try:
    # Infinite loop to continuously receive data and control the boat
    while True:
        # Attempt to receive data from the LoRa module
        incoming = lora.receive_data()

        # Check if data was received and it's a valid RCV message
        if incoming and incoming.startswith("+RCV="):
            print(f"Received RAW LoRa data: {incoming}")
            try:
                # Remove the "+RCV=" prefix and split the message by commas
                parts = incoming.replace("+RCV=", "").split(",")

                # --- Check for Command Messages ---
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
                    continue

                # --- Process Data from Leader (only if in ACTIVE state) ---
                # Expected format for Leader data: +RCV=<sender>,<length>,LEADER,<lat>,<lon>,<heading>,<rssi>
                if STATE == "ACTIVE" and len(parts) >= 7 and parts[2] == "LEADER":
                    # Parse leader's data
                    # lat = float(parts[3]) # Latitude (not used in this version for control)
                    # lon = float(parts[4]) # Longitude (not used in this version for control)
                    last_leader_heading = float(parts[5]) # Leader's heading
                    rssi = int(parts[6]) # RSSI from the leader

                    print(f"Leader Heading: {last_leader_heading:.2f}° | RSSI: {rssi} dBm")

                    # Adjust PWM based on RSSI (distance control)
                    if rssi > RSSI_CLOSE:
                        # Too close, reduce speed
                        print("Distance: Too Close")
                        current_pwm = PWM_MIN
                    elif rssi < RSSI_FAR:
                        # Too far, increase speed
                        print("Distance: Too Far")
                        current_pwm = PWM_MAX
                    else:
                        # Distance is within acceptable range, interpolate PWM
                        print("Distance: OK")
                        # Linear interpolation of PWM based on RSSI within the OK range
                        # Ratio is 0 when RSSI = RSSI_CLOSE, 1 when RSSI = RSSI_FAR
                        ratio = (RSSI_CLOSE - rssi) / (RSSI_CLOSE - RSSI_FAR)
                        current_pwm = int(PWM_MIN + (PWM_MAX - PWM_MIN) * ratio)

                    print(f"Adjusted PWM: {current_pwm}")

            except ValueError as e:
                # Handle errors during data parsing
                print(f"Data parse error: {e}")
            except IndexError as e:
                # Handle errors if message format is unexpected
                print(f"Index error parsing message: {e}")
            except Exception as e:
                # Catch any other unexpected errors during processing
                print(f"An unexpected error occurred: {e}")


        # --- Heading Matching and Motor Control (only if ACTIVE and Leader data received) ---
        # Only attempt to match heading if the boat is ACTIVE and we have a leader heading
        if STATE == "ACTIVE" and last_leader_heading is not None:
            # Read the follower boat's current heading
            my_heading = read_heading()
            # Calculate the difference between leader's heading and follower's heading
            diff = last_leader_heading - my_heading

            # Normalize the heading difference to be within -180 to +180 degrees
            if diff > 180: diff -= 360
            elif diff < -180: diff += 360

            print(f"My Heading: {my_heading:.2f}° | Leader Heading: {last_leader_heading:.2f}° | Heading Difference: {diff:+.2f}°")
            # Drive the motors based on the heading difference and calculated PWM speed
            drive_motors(diff, current_pwm)

        # Small delay in the main loop to prevent high CPU usage
        time.sleep(0.5)

# --- Cleanup on Exit ---
except KeyboardInterrupt:
    # Handle Ctrl+C to stop the script gracefully
    print("Stopping follower...")
    # Stop the motors
    stop_motors()
    # Stop the pigpio daemon connection
    pi.stop()
    # Close the serial connection to the LoRa module
    lora.ser.close()
except Exception as e:
    # Catch any other unexpected errors during execution
    print(f"An unexpected error caused the program to stop: {e}")
    # Attempt to clean up resources
    stop_motors()
    pi.stop()
    if lora.ser and lora.ser.isOpen():
        lora.ser.close()

