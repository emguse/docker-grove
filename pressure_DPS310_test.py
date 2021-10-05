import time
from grove.i2c import Bus
import multi_timer

ADDRESS = 0x77 
SCALE_FACTOR = 1572864 # Oversampling Rate 2 times (Low Power)

def getTwosComplement(raw_val, length):
    """Get two's complement of `raw_val`.
    Args:raw_val (int): Raw value
         length (int): Max bit length
    Returns:int: Two's complement"""
    value = raw_val
    if raw_val & (1 << (length - 1)):
        value = raw_val - (1 << length)
    return value

def calc_temp(raw_temp):
    # Traw_sc = Traw/kT
    scaled_temp = raw_temp / SCALE_FACTOR
    # Tcomp (°C) = c0*0.5 + c1*Traw_sc
    compd_temp = c0 * 0.5 + c1 * scaled_temp
    return scaled_temp, compd_temp

def calc_press(raw_press, scaled_temp):
    # Praw_sc = Praw/kP
    scaled_press = raw_press / SCALE_FACTOR
    # Pcomp(Pa) = c00 + Praw_sc*(c10 + Praw_sc *(c20+ Praw_sc *c30)) 
    #                + Traw_sc *c01 + Traw_sc *Praw_sc *(c11+Praw_sc*c21) 
    compd_press = c00 + scaled_press * (c10 + scaled_press * (c20 + scaled_press * c30))\
                     + scaled_temp * c01 + scaled_temp * scaled_press * (c11 + scaled_press * c21)
    return compd_press

# I2C bus
bus = Bus(None)

time.sleep(1.0)

# Read Calibration Coefficients
reg = {}
for i in range(0x10, 0x22):
    reg[i] = bus.read_byte_data(ADDRESS,i)

c0 = getTwosComplement(((reg[0x10]<<8 | reg[0x11])>>4), 12)
c1 = getTwosComplement(((reg[0x11] & 0x0F)<<8 | reg[0x12]), 12)
c00 = getTwosComplement((((reg[0x13]<<8 | reg[0x14])<<8 | reg[0x15])>>4), 20)
c10 = getTwosComplement((((reg[0x15] & 0x0F)<<8 | reg[0x16])<<8 | reg[0x17]), 20)
c01 = getTwosComplement((reg[0x18]<<8 | reg[0x19]), 16)
c11 = getTwosComplement((reg[0x1A]<<8 | reg[0x1B]), 16)
c20 = getTwosComplement((reg[0x1C]<<8 | reg[0x1D]), 16)
c21 = getTwosComplement((reg[0x1E]<<8 | reg[0x1F]), 16)
c30 = getTwosComplement((reg[0x20]<<8 | reg[0x21]), 16)

# Measurement Settings
bus.write_byte_data(ADDRESS, 0x06, 0x71) 
'''
# Pressure Configuration (PRS_CFG) 
# Pressure measurement rate: 0111 XXXX- 128 measurements pr. sec.
# Pressure oversampling rate: XXXX 0001 - 2 times (Low Power).  Precision : 1 PaRMS.
# 0111 0001 = 0x71 highest measurements rate 
# (At 128 measurements per second, the oversampling rate is limited to 2)
'''
bus.write_byte_data(ADDRESS, 0x07, 0xF0)
'''
# Temperature Configuration(TMP_CFG) 
# Temperature measurement: 1XXX XXXX - External sensor (in pressure sensor MEMS element)
# Temperature measurement rate: X111 XXXX - 128 measurements pr. sec.
# Temperature oversampling (precision): 0000 - single. (Default) - Measurement time 3.6 ms.
# 1111 0000 = 0xF0 highest measurements rate 
'''
bus.write_byte_data(ADDRESS, 0x09, 0x00)
'''
# Interrupt and FIFO configuration (CFG_REG)
# T_SHIFT: bit3: Temperature result bit-shift: 0 - no shift result right in data register.
# P_SHIFT: bit2: Pressure result bit-shift: 0 - no shift result right in data register.
# 0000 1100 = 0x00
'''

bus.write_byte_data(ADDRESS, 0x08, 0x07)
'''
# Sensor Operating Mode and Status (MEAS_CFG)
# Background Mode
# 111 - Background Mode Continous pressure and temperature measurement
# 0000 0111 = 0x07
'''

def read_temperature():
    reg = {}
    # read raw temperature
    for i in range(0x03, 0x06):
        reg[i] = bus.read_byte_data(ADDRESS,i)
    raw_temp = getTwosComplement(((reg[0x03]<<16) | (reg[0x04]<<8) | reg[0x05]), 24)
    # calculate temperature
    scaled_temp, compd_temp = calc_temp(raw_temp)
    return scaled_temp, compd_temp

def read_pressure(scaled_temp):
    reg = {}
    for i in range(0x00, 0x03):
        reg[i] = bus.read_byte_data(ADDRESS,i)
    raw_press = getTwosComplement(((reg[0x00]<<16) | (reg[0x01]<<8) | reg[0x02]), 24)
    compd_press = calc_press(raw_press,scaled_temp)
    return compd_press


try:
    INTERVAL_128Hz = 1/128
    timer128Hz = multi_timer.multi_timer(INTERVAL_128Hz)
    while True:
        timer128Hz.timer()
        if timer128Hz.up_state == True:
            timer128Hz.up_state = False
            scaled_temp ,temp = read_temperature()
            press = read_pressure(scaled_temp)
            print(str(time.time()) + "," + str(press))
except KeyboardInterrupt:
    pass