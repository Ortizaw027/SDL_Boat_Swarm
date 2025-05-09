import pigpio
import time

GPS_TX = 27  # GPS TX → Pi RX
GPS_RX = 22  # Pi TX → GPS RX
BAUD = 9600

pi = pigpio.pi()
if not pi.connected:
    raise Exception("Could not connect to pigpio daemon")

# Start software UART and set TX pin
pi.bb_serial_read_open(GPS_TX, BAUD)
pi.set_mode(GPS_RX, pigpio.OUTPUT)

# Send NMEA config over soft UART
def send_nmea_command(cmd):
    full_cmd = (cmd + '\r\n').encode()
    print("Sending:", cmd)
    pi.wave_clear()
    pi.wave_add_serial(GPS_RX, BAUD, full_cmd)
    wid = pi.wave_create()
    if wid >= 0:
        pi.wave_send_once(wid)
        while pi.wave_tx_busy():
            time.sleep(0.1)
        pi.wave_delete(wid)
    else:
        print("Failed to create waveform")

# Convert ddmm.mmmm to decimal degrees
def convert(coord, direction):
    if not coord or not direction:
        return None
    deg_len = 2 if direction in ['N', 'S'] else 3
    degrees = float(coord[:deg_len])
    minutes = float(coord[deg_len:])
    decimal = degrees + minutes / 60
    if direction in ['S', 'W']:
        decimal *= -1
    return decimal

# Parse a $GPRMC sentence manually
def parse_gprmc(sentence):
    fields = sentence.split(',')
    if len(fields) < 12 or fields[2] != 'A':
        return None  # No fix or bad sentence

    # Time and date
    hhmmss = fields[1]
    ddmmyy = fields[9]
    time_str = f"{hhmmss[:2]}:{hhmmss[2:4]}:{hhmmss[4:6]}"
    date_str = f"{ddmmyy[:2]}/{ddmmyy[2:4]}/20{ddmmyy[4:]}"

    # Lat/Lon, speed, heading
    lat = convert(fields[3], fields[4])
    lon = convert(fields[5], fields[6])
    speed = float(fields[7]) if fields[7] else 0.0
    heading = float(fields[8]) if fields[8] else 0.0

    return {
        'time': time_str,
        'date': date_str,
        'latitude': lat,
        'longitude': lon,
        'speed_knots': speed,
        'heading': heading
    }

try:
    # Disable all messages except $GPRMC
    send_nmea_command("$PUBX,40,GGA,0,0,0,0*5A")
    send_nmea_command("$PUBX,40,GLL,0,0,0,0*5C")
    send_nmea_command("$PUBX,40,VTG,0,0,0,0*5E")
    send_nmea_command("$PUBX,40,GSA,0,0,0,0*4E")
    send_nmea_command("$PUBX,40,GSV,0,0,0,0*59")

    print("Done sending config commands.")
    print("Waiting for $GPRMC data...")

    buffer = ""
    while True:
        (count, data) = pi.bb_serial_read(GPS_TX)
        if count:
            buffer += data.decode("utf-8", errors="ignore")
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                line = line.strip()
                if line.startswith("$GPRMC"):
                    result = parse_gprmc(line)
                    if result:
                        print("📡 GPS Fix:")
                        print(f"  Time     : {result['time']}")
                        print(f"  Date     : {result['date']}")
                        print(f"  Latitude : {result['latitude']:.6f}")
                        print(f"  Longitude: {result['longitude']:.6f}")
                        print(f"  Speed    : {result['speed_knots']:.2f} knots")
                        print(f"  Heading  : {result['heading']:.2f}°")
                        print("────────────")
                    else:
                        print("Waiting for GPS fix...")

        time.sleep(0.1)

except KeyboardInterrupt:
    print("Exiting...")

finally:
    pi.bb_serial_read_close(GPS_TX)
    pi.stop()
