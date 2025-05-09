import pigpio
import time

#Define motor control pins
AIN1 = 22
AIN2 = 27
BIN1 = 23
BIN2 = 24
PWMA = 18
PWMB = 19
STBY = 13
#Initialize GPIO
pi = pigpio.pi()

#Set motor control pins as outputs
pi.set_mode(AIN1, pigpio.OUTPUT)
pi.set_mode(AIN2, pigpio.OUTPUT)
pi.set_mode(BIN1, pigpio.OUTPUT)
pi.set_mode(BIN2, pigpio.OUTPUT)
pi.set_mode(STBY, pigpio.OUTPUT)

def forward(speed = 75):  #Speed is the percentage (0-100)
	pi.write(STBY, 1)
	pi.write(AIN1, 1)
	pi.write(AIN2, 0)
	pi.write(BIN1, 1)
	pi.write(BIN2, 0)
	pi.set_PWM_dutycycle(PWMA, int(speed))
	pi.set_PWM_dutycycle(PWMB, int(speed))

def stop():
	pi.write(AIN1, 0)
	pi.write(AIN2, 0)
	pi.write(BIN1, 0)
	pi.write(BIN2, 0)
	pi.set_PWM_dutycycle(PWMA, 0)
	pi.set_PWM_dutycycle(PWMB, 0)

try:
	forward(50)
	input("Press Enter to stop...\n")
	stop()
finally:

	stop()
	pi.write(STBY, 0)
	pi.stop()
