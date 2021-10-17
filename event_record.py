import RPi.GPIO as gpio
import time
import pressure_DPS310 as DPS310
import acc_ADXL345 as ADXL345
import multi_timer
import csv
import datetime
from collections import deque

BUTTON_PIN = 5 # slot D5
SAVE_DIR = './press_log/'
SAVE_LENGTH = 10 # [sec]
BUTTON_MASK = 2.0 # [sec]
ACC_READ_RATE = 128 # [Hz]

def export_p(d_p):
    today = datetime.date.today()
    filename = str(SAVE_DIR + today.strftime('%Y%m%d') + '-' + time.strftime('%H%M%S') + '_p.csv')
    try:
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            print("Start exporting pressure data")
            for i in d_p:
                writer.writerow(i)
            print("Export Complete")
    except:
        print("File export error")
def export_a(d_a):
    today = datetime.date.today()
    filename = str(SAVE_DIR + today.strftime('%Y%m%d') + '-' + time.strftime('%H%M%S') + '_a.csv')
    try:
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            print("Start exporting acc data")
            for i in d_a:
                writer.writerow(i)
            print("Export Complete")
    except:
        print("File export error")

def main():
    gpio.setmode(gpio.BCM)
    gpio.setup(BUTTON_PIN,gpio.IN)

    dps310 = DPS310.pressure_sensor_DPS310() # Instance creation
    dps310_timer = multi_timer.multi_timer(dps310.read_interval) 

    adxl345 = ADXL345.ADXL345()
    adxl345_timer = multi_timer.multi_timer(1/ACC_READ_RATE)

    button_mask = multi_timer.multi_timer(BUTTON_MASK)

    Factors = dps310.read_calibration_coefficients() # Read Calibration Coefficients

    ivent_length = SAVE_LENGTH * (1/dps310.read_interval)
    d_press = deque(maxlen=int(ivent_length))
    d_acc = deque(maxlen=int(ivent_length))

    while True:
        try:
            dps310.start_measurement()
            while True:
                dps310_timer.timer()
                adxl345_timer.timer()
                button_mask.timer()
                if dps310_timer.up_state == True:
                    dps310_timer.up_state = False
                    # process
                    scaled_temp ,temperature = dps310.read_temperature(Factors) # read and compensation temperature
                    press = dps310.read_pressure(scaled_temp, Factors) # read and compensation pressure
                    #print(str(time.time()) + "," + str(press))
                    press_data = [str(time.time()),str(press)]
                    d_press.append(press_data)
                if adxl345_timer.up_state == True:
                    adxl345_timer.up_state = False
                    # process
                    acc_data = adxl345.getAxes(True)
                    acc_value = acc_data.values()
                    d_acc.append(acc_value)

                if gpio.input(BUTTON_PIN) and button_mask.up_state == True:
                    button_mask.up_state = False
                    export_p(d_press)
                    export_a(d_acc)
        finally:
            dps310.stop_measurement()
            gpio.cleanup()

if __name__ == "__main__":
  main()