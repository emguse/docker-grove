import time
from grove.i2c import Bus

address=0x77
# I2C bus
bus = Bus(None)
        
# Read Calibration Coefficients
reg = {}
for i in range(0x10, 0x22):
    reg[i] = bus.read_byte_data(address,i)

c0 = (reg[0x10]<<8 | reg[0x11])>>4
c1 = (reg[0x11] & 0x0F)<<8 | reg[0x12] 
c00 = ((reg[0x13]<<8 | reg[0x14])<<8 | reg[0x15])>>4
c10 = ((reg[0x15] & 0x0F)<<8 | reg[0x16])<<8 | reg[0x17]
c01 = reg[0x18]<<8 | reg[0x19]
c11 = reg[0x1A]<<8 | reg[0x1B]
c20 = reg[0x1C]<<8 | reg[0x1D]
c21 = reg[0x1E]<<8 | reg[0x1F]
c30 = reg[0x20]<<8 | reg[0x21]

# Measurement Settings
bus.write_byte_data(address, 0x06, 0x71) 
'''
# Pressure Configuration (PRS_CFG) 
# Pressure measurement rate: 0111 XXXX- 128 measurements pr. sec.
# Pressure oversampling rate: XXXX 0001 - 2 times (Low Power).  Precision : 1 PaRMS.
# 0111 0001 = 0x71 highest measurements rate 
# (At 128 measurements per second, the oversampling rate is limited to 2)
'''
bus.write_byte_data(address, 0x07, 0xF0)
'''
# Temperature Configuration(TMP_CFG) 
# Temperature measurement: 1XXX XXXX - External sensor (in pressure sensor MEMS element)
# Temperature measurement rate: X111 XXXX - 128 measurements pr. sec.
# Temperature oversampling (precision): 0000 - single. (Default) - Measurement time 3.6 ms.
# 1111 0000 = 0xF0 highest measurements rate 
'''
bus.write_byte_data(address, 0x09, 0x0C)
'''
# Interrupt and FIFO configuration (CFG_REG)
# T_SHIFT: bit3: Temperature result bit-shift: 1 - shift result right in data register.
# P_SHIFT: bit2: Pressure result bit-shift: 1 - shift result right in data register.
# 0000 1100 = 0x0C
'''


bus.write_byte_data(address, 0x08, )