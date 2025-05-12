import tkinter as tk
from tkinter import ttk
import serial
import threading
import time

# LoRa module configuration
LORA_PORT = "/dev/ttyUSB0"  # Adjust based on your system
BAUDRATE = 115200
MY_ADDRESS = 99            # Controller's unique address
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

class BoatControllerGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Boat Controller")
        self.create_widgets()
        self.running = True
        self.update_thread = threading.Thread(target=self.update_status)
        self.update_thread.start()

    def create_widgets(self):
        """
        Creates GUI widgets.
        """
        # Start Button
        self.start_button = ttk.Button(self.master, text="Start", command=self.start_boats)
        self.start_button.grid(row=0, column=0, padx=10, pady=10)

        # Stop Button
        self.stop_button = ttk.Button(self.master, text="Stop", command=self.stop_boats)
        self.stop_button.grid(row=0, column=1, padx=10, pady=10)

        # Status Display
        self.status_text = tk.Text(self.master, height=15, width=50)
        self.status_text.grid(row=1, column=0, columnspan=2, padx=10, pady=10)

    def start_boats(self):
        """
        Sends the START command to both leader and follower boats.
        """
        send_lora_message(100, "CMD,START")  # Leader address
        send_lora_message(101, "CMD,START")  # Follower address
        self.status_text.insert(tk.END, "Sent START command to boats.\n")

    def stop_boats(self):
        """
        Sends the STOP command to both leader and follower boats.
        """
        send_lora_message(100, "CMD,STOP")  # Leader address
        send_lora_message(101, "CMD,STOP")  # Follower address
        self.status_text.insert(tk.END, "Sent STOP command to boats.\n")

    def update_status(self):
        """
        Continuously checks for incoming messages and updates the status display.
        """
        while self.running:
            incoming = receive_lora_data()
            if incoming:
                self.status_text.insert(tk.END, f"Received: {incoming}\n")
                self.status_text.see(tk.END)
            time.sleep(0.1)

    def on_close(self):
        """
        Handles GUI closure.
        """
        self.running = False
        self.update_thread.join()
        ser.close()
        self.master.destroy()

def main():
    configure_lora()
    root = tk.Tk()
    app = BoatControllerGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()

if __name__ == "__main__":
    main()
