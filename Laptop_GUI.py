import tkinter as tk
from tkinter import ttk
import serial
import threading

# Replace 'COM3' with your actual COM port
USB_PORT = "COM3"
USB_BAUD = 115200

class SerialGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Controller GUI")
        self.master.geometry("600x400")

        # Initialize serial connection
        try:
            self.ser = serial.Serial(USB_PORT, USB_BAUD, timeout=1)
            print(f"Connected to {USB_PORT} at {USB_BAUD} baud.")
        except serial.SerialException as e:
            print(f"Serial error: {e}")
            self.ser = None

        # Create START button
        self.start_button = tk.Button(master, text="START", width=20, command=self.send_start)
        self.start_button.pack(pady=5)

        # Create STOP button
        self.stop_button = tk.Button(master, text="STOP", width=20, command=self.send_stop)
        self.stop_button.pack(pady=5)

        # Create Treeview for displaying boat data
        columns = ("Latitude", "Longitude", "Heading", "RSSI")
        self.tree = ttk.Treeview(master, columns=columns, show='headings')
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        self.tree.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Dictionary to keep track of boat data
        self.boat_data = {}

        # Start a thread to read incoming data
        if self.ser:
            self.running = True
            self.read_thread = threading.Thread(target=self.read_serial)
            self.read_thread.daemon = True
            self.read_thread.start()

        # Handle window closing
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def send_start(self):
        if self.ser and self.ser.is_open:
            try:
                self.ser.write(b"START\n")
                print("Sent: START")
            except serial.SerialException as e:
                print(f"Error sending START: {e}")
        else:
            print("Serial port not open.")

    def send_stop(self):
        if self.ser and self.ser.is_open:
            try:
                self.ser.write(b"STOP\n")
                print("Sent: STOP")
            except serial.SerialException as e:
                print(f"Error sending STOP: {e}")
        else:
            print("Serial port not open.")

    def read_serial(self):
        while self.running:
            try:
                if self.ser.in_waiting:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        self.process_data(line)
            except serial.SerialException as e:
                print(f"Serial error: {e}")
                break

    def process_data(self, data):
        """
        Expected data format: ID,LAT,LON,HEADING,RSSI
        Example: 1,40.7128,-74.0060,90,45
        """
        parts = data.split(',')
        if len(parts) == 5:
            boat_id = parts[0]
            lat = parts[1]
            lon = parts[2]
            heading = parts[3]
            rssi = parts[4]

            # Update existing entry or add new one
            if boat_id in self.boat_data:
                self.tree.item(self.boat_data[boat_id], values=(lat, lon, heading, rssi))
            else:
                item = self.tree.insert('', tk.END, values=(lat, lon, heading, rssi))
                self.boat_data[boat_id] = item

    def on_closing(self):
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SerialGUI(root)
    root.mainloop()
