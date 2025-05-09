import time
import math
import smbus2
import serial

#HMC5883l I2C Address found by using sudo i2cdetect -y 1 command in terminal
HMC5883l_ADDR = 0x1E

#Register addresses
CONFIG_REG_A = 0x00 #Configures the averaging, data rate, and measurement mode
CONFIG_REG_B = 0x01 #Sets the gain for the magnetometer
MODE_REG = 0x02     #Sets the operating mode of sensor(single,continuous, or idle mode)
DATA_REG = 0x03     #Main register where heading data will be stored

#Initialize I2C(Bus 1 for Raspberry Pi)
bus = smbus2.SMBus(1)

#Function to initialize sensor
def init_sensor():

	    #8-average, 15 Hz, normal mode
	    bus.write_byte_data(HMC5883l_ADDR, CONFIG_REG_A, 0x70)

	    #Sets the gain to 5
	    bus.write_byte_data(HMC5883l_ADDR, CONFIG_REG_B, 0xA0)

	    #Sets the sensor to continuous measurement mode
	    bus.write_byte_data(HMC5883l_ADDR, MODE_REG, 0x00)

	    #Delay to ensure sensor has time to respond
	    time.sleep(0.1)

#Function to read the sensor data
def read_data():

	    #Reads 6 bytes(0x03 to 0x08)from the data registers which corresponds to the X, Y, and Z axis
	    data = bus.read_i2c_block_data(HMC5883l_ADDR, DATA_REG, 6)

	    #Combine the MSB and LSB for each axis since the sensor returns the magnetic field data in pairs(high byte + low byte) for each axis
	    x = (data[0] << 8) | data[1]
	    z = (data[2] << 8) | data[3]
	    y = (data[4] << 8) | data[5]

	    #Convert to signed 16-bit values to ensure none of the axis values exceed the upper limit(32768) if any do we subtract 65536 to get the negative value in 2's compliment form
	    if x >= 32768:
	    	x -= 65536
	    if y >= 32768:
	    	y -= 65536
	    if z >= 32768:
	    	z -= 65536

	    return x, y, z

#Function to calculate heading in degrees
def calculate_heading(x, y):

	#Get the heading(angle) in radians
	heading = math.atan2(y, x)

	#Convert radians to degrees
	heading = math.degrees(heading)
	#Adjust heading to be between 0 and 360 degrees
	if heading < 0:
	    heading += 360

	return heading

#Function to convert heading into cardinal direction
def get_direction(heading):
	if (heading >= 337.5 or heading < 22.5):
	    return "(N)"
	elif (heading >= 22.5 and heading < 67.5):
	    return "(NE)"
	elif (heading >= 67.5 and heading < 112.5):
	    return "(E)"
	elif (heading >= 112.5 and heading < 157.5):
	    return "(SE)"
	elif (heading >= 157.5 and heading < 202.5):
	    return "(S)"
	elif (heading >= 202.5 and heading < 247.5):
	    return "(SW)"
	elif (heading >= 247.5 and heading < 292.5):
	    return "(W)"
	elif (heading >= 292.5 and heading < 337.5):
	    return "(NW)"

#Initialize the sensor
init_sensor()

#Continuously read and display data
while True:


	#Calls read_data function to get the X, Y, and Z magnetometer values
	x, y, z = read_data()

	heading = calculate_heading(x, y)

	direction = get_direction(heading)

	print(f"Heading (degrees): {heading}, {direction}")

	#Wait for a second before the next reading
	time.sleep(.5)
