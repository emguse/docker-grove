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
RECORD_LENGTH = 10 # [sec]
BUTTON_MASK = 2.0 # [sec]
PRESS_READ_RATE = 128 # [Hz]
ACC_READ_RATE = 128 # [Hz]
REF_DELTA_P = 20 # [Pa]
REF_DELTA_ACC = 0.3 # [g]

class press_log():
    def __init__(self) -> None:
        self.dps310 = DPS310.pressure_sensor_DPS310() # Instance creation
        self.dps310_timer = multi_timer.multi_timer(self.dps310.read_interval)
        self.Factors = self.dps310.read_calibration_coefficients() # Read Calibration Coefficients
        self.press = 0
        self.d_press = deque(maxlen=int(PRESS_READ_RATE * RECORD_LENGTH))
        self.last_p = 0
        self.ax = 0
        self.ay = 0
        self.az = 0
        pass
    def read_press(self):
        self.dps310_timer.timer()
        if self.dps310_timer.up_state == True:
            self.dps310_timer.up_state = False
            self.press = self.dps310.get_pressure(self.Factors)
            press_data = [str(time.time()),str(self.press)]
            self.d_press.append(press_data)
    def press_trigger_chk(self,b_up_state):
        if self.last_p != 0:
            dp = abs(self.last_p - self.press)
            if b_up_state == True:
                if dp >= REF_DELTA_P:
                    b_up_state = False
                    self.export_p(self.d_press,"dp")
            self.last_p = self.press
        return b_up_state
    def export_p(self, d_p, trg):
        today = datetime.date.today()
        filename = str(SAVE_DIR + today.strftime('%Y%m%d') + '-' + time.strftime('%H%M%S') + trg +'_p.csv')
        try:
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                print("Start exporting pressure data")
                for i in d_p:
                    writer.writerow(i)
                print("Export Complete")
        except:
            print("File export error")

class acc_log():
    def __init__(self) -> None:
        self.adxl345 = ADXL345.ADXL345()
        self.adxl345_timer = multi_timer.multi_timer(1/ACC_READ_RATE)
        self.d_acc = deque(maxlen=int(ACC_READ_RATE * RECORD_LENGTH))
        self.last_a = [0, 0, 0]
        pass
    def read_acc(self):
        self.adxl345_timer.timer()
        if self.adxl345_timer.up_state == True:
            self.adxl345_timer.up_state = False
            acc_data = self.adxl345.getAxes(True)
            acc_value = acc_data.values()
            self.d_acc.append(acc_value)
            self.ax, self.ay, self.az = acc_value
    def acc_trigger_chk(self, b_up_state):
        if b_up_state == True:
            if self.last_a[0] != 0:
                dax = abs(self.last_a[0] - self.ax)
                if dax >= REF_DELTA_ACC:
                    b_up_state = False
                    self.export_a(self.d_acc, 'dax')
            self.last_a[0] = self.ax
            if self.last_a[1] != 0:
                day_ = abs(self.last_a[1] - self.ay)
                if day_ >= REF_DELTA_ACC:
                    b_up_state = False
                    self.export_a(self.d_acc, 'day')
            self.last_a[1] = self.ay
            if self.last_a[2] != 0:
                daz = abs(self.last_a[2] - self.az)
                if daz >= REF_DELTA_ACC:
                    b_up_state = False
                    self.export_a(self.d_acc, 'daz')
            self.last_a[2] = self.az
        return b_up_state
    def export_a(self, d_a, trg):
        today = datetime.date.today()
        filename = str(SAVE_DIR + today.strftime('%Y%m%d') + '-' + time.strftime('%H%M%S') + trg + '_a.csv')
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
    button_mask = multi_timer.multi_timer(BUTTON_MASK)
    p_log = press_log()
    a_log = acc_log()
    while True:
        try:
            p_log.dps310.start_measurement()
            while True:
                button_mask.timer()
                p_log.read_press()
                a_log.read_acc()
                button_mask.up_state = p_log.press_trigger_chk(button_mask.up_state)
                button_mask.up_state = a_log.acc_trigger_chk(button_mask.up_state)
                if gpio.input(BUTTON_PIN) and button_mask.up_state == True:
                    button_mask.up_state = False
                    p_log.export_p(p_log.d_press, 'button')
                    a_log.export_a(a_log.d_acc, 'button')              
        finally:
            p_log.dps310.stop_measurement()
            gpio.cleanup()

if __name__ == "__main__":
  main()