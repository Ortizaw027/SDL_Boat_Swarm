import pigpio
import time

# Define motor control pins
AIN1 = 22
AIN2 = 27
BIN1 = 23
BIN2 = 24
PWMA = 18
PWMB = 19
STBY = 13

# Initialize pigpio
pi = pigpio.pi()

# Set motor control pins as outputs
pi.set_mode(AIN1, pigpio.OUTPUT)
pi.set_mode(AIN2, pigpio.OUTPUT)
pi.set_mode(BIN1, pigpio.OUTPUT)
pi.set_mode(BIN2, pigpio.OUTPUT)
pi.set_mode(STBY, pigpio.OUTPUT)

# Set PWM frequency to 1 kHz (Adjust if needed)
pi.set_PWM_frequency(PWMA, 1000)
pi.set_PWM_frequency(PWMB, 1000)

def test_pwm():
    """Gradually increase and decrease PWM to observe motor response."""
    pi.write(STBY, 1)  # Enable the motor driver
    pi.write(AIN1, 1)  # Set forward direction
    pi.write(AIN2, 0)
    pi.write(BIN1, 1)
    pi.write(BIN2, 0)

    print("Increasing PWM...")
    for pwm in range(0, 256, 10):  # Sweep PWM from 0 to 255 in steps of 10
        print(f"PWM: {pwm}")
        pi.set_PWM_dutycycle(PWMA, pwm)
        pi.set_PWM_dutycycle(PWMB, pwm)
        time.sleep(1)

    print("Decreasing PWM...")
    for pwm in range(255, -1, -10):  # Sweep PWM down to 0
        print(f"PWM: {pwm}")
        pi.set_PWM_dutycycle(PWMA, pwm)
        pi.set_PWM_dutycycle(PWMB, pwm)
        time.sleep(1)

    stop()

def stop():
    """Stop the motors."""
    pi.set_PWM_dutycycle(PWMA, 0)
    pi.set_PWM_dutycycle(PWMB, 0)
    pi.write(AIN1, 0)
    pi.write(AIN2, 0)
    pi.write(BIN1, 0)
    pi.write(BIN2, 0)
    pi.write(STBY, 0)  # Put motor driver in standby

try:
    test_pwm()
finally:
    stop()
    pi.stop()
