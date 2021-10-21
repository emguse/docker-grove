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
RECORD_LENGTH = 20 # 1/2 past 1/2 future [sec]
BUTTON_MASK = 2.0 # [sec]
PRESS_READ_RATE = 64 # [Hz]
ACC_READ_RATE = 64 # [Hz]
REF_DELTA_P = 5 # [Pa]
REF_DELTA_ACC = 0.3 # [g]

class press_log():
    def __init__(self) -> None:
        self.dps310 = DPS310.pressure_sensor_DPS310() # Instance creation
        self.dps310_timer = multi_timer.multi_timer(self.dps310.read_interval) 
        self.Factors = self.dps310.read_calibration_coefficients() # Read Calibration Coefficients
        self.press = 0
        self.d_press = deque(maxlen=int(PRESS_READ_RATE * RECORD_LENGTH)) 
        self.last_p = 0
        pass
    def read_press(self):
        self.dps310_timer.timer() # Timer update
        if self.dps310_timer.up_state == True: # Time up judgment
            self.dps310_timer.up_state = False # Reset time-up status
            self.press = self.dps310.get_pressure(self.Factors) # DPS310 sensor reading
            press_data = [str(time.time()),str(self.press)] 
            self.d_press.append(press_data) # Add to queue
    def press_trigger_chk(self,b_up_state): 
        if self.last_p != 0: # Not detected the first time
            dp = abs(self.last_p - self.press) # Calculate the difference from the previous measurement
            if b_up_state == True: # Use the button's multiple detection prevention mask
                if dp >= REF_DELTA_P: # Determine if the difference exceeds the standard
                    b_up_state = False # Reset button mask status
                    self.press_trigger_after_record() # Record after triggering
            self.last_p = self.press # Update last measured value
        return b_up_state # Return the button mask status
    def press_trigger_after_record(self):
        print("Post-trigger pressure data recording")
        for i in range(int(PRESS_READ_RATE * RECORD_LENGTH /2)): # Counting half of the recording time
            while True:
                self.dps310_timer.timer() # Standby for timer-up
                if self.dps310_timer.up_state == True: # Timer up to continue processing
                    break
            self.dps310_timer.up_state = False # Reset time-up status
            self.press = self.dps310.get_pressure(self.Factors) # DPS310 sensor reading
            press_data = [str(time.time()),str(self.press)]
            self.d_press.append(press_data) # Add to queue
        self.export_p(self.d_press,"dp") # Pressure data export
    def export_p(self, d_p, trg):
        today = datetime.date.today() # Get unix time.
        filename = str(SAVE_DIR + today.strftime('%Y%m%d') + '-' + time.strftime('%H%M%S') + trg +'_p.csv') # filename generation
        try:
            with open(filename, 'w', newline='') as f: # File open in write mode
                writer = csv.writer(f)
                print("Start exporting pressure data")
                for i in d_p:
                    writer.writerow(i) # Write the contents of the queue
                print("Export Complete")
        except:
            print("File export error")

class acc_log():
    def __init__(self) -> None:
        self.adxl345 = ADXL345.ADXL345()
        self.adxl345_timer = multi_timer.multi_timer(1/ACC_READ_RATE)
        self.d_acc = deque(maxlen=int(ACC_READ_RATE * RECORD_LENGTH))
        self.last_a = [0, 0, 0]
        self.ax = 0
        self.ay = 0
        self.az = 0
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
            if self.last_a[0] != 0: # Not detected the first time
                dax = abs(self.last_a[0] - self.ax)
                if dax >= REF_DELTA_ACC:
                    b_up_state = False
                    self.acc_after_trigger_record('dax')
            self.last_a[0] = self.ax
            if self.last_a[1] != 0: # Not detected the first time
                day_ = abs(self.last_a[1] - self.ay)
                if day_ >= REF_DELTA_ACC:
                    b_up_state = False
                    self.acc_after_trigger_record('day')
            self.last_a[1] = self.ay
            if self.last_a[2] != 0: # Not detected the first time
                daz = abs(self.last_a[2] - self.az)
                if daz >= REF_DELTA_ACC:
                    b_up_state = False
                    self.acc_after_trigger_record('daz')
            self.last_a[2] = self.az
        return b_up_state
    def acc_after_trigger_record(self, trg):
        print("Post-trigger acceleration data recording")
        for i in range(int(PRESS_READ_RATE * RECORD_LENGTH /2)):
            while True:
                self.adxl345_timer.timer()
                if self.adxl345_timer.up_state == True:
                    break
            self.adxl345_timer.up_state = False
            acc_data = self.adxl345.getAxes(True)
            acc_value = acc_data.values()
            self.d_acc.append(acc_value)
        self.export_a(self.d_acc, trg)
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
                    print("Forced trigger detection")
                    p_log.export_p(p_log.d_press, 'button')
                    a_log.export_a(a_log.d_acc, 'button')              
        finally:
            p_log.dps310.stop_measurement()
            gpio.cleanup()

if __name__ == "__main__":
  main()