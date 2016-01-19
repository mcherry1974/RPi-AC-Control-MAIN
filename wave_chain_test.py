#wave_chain_test.py
#Mark Cherry
#November 2015
#
#Generate IR Transmit (Tx) data using a modulated carrier at a specified frequency
#Uses pigpio python module to create one waveform that represents the IR carrier
#Uses pigpio's 'wave_chain' function to string all the Tx data together
#IR protocol is specific to the Mitsubishi Ductless Heat Pump
#Can be modified to control other IR devices if the protocol is known

import time
import pigpio
import math

GPIO=24 #GPIO number that will output the IR data
ir_tx_freq = 38000 #ir Tx carrier frequency
ir_tx_per = math.floor(1/ir_tx_freq*1000000) #period of carrier in microseconds

#Based on research done on various HVAC IR controls
#Timing is slightly different than research
#Research Link = https://github.com/r45635/HVAC-IR-Control
HEADER_MARK = 3400
HEADER_SPACE = 1750
BIT_MARK = 450
ZERO_SPACE = 420
ONE_SPACE = 1300
REPEAT_SPACE = 17100
REPEAT_MARK = 440

#IR Control Data
#Formatted the same way as the research, 18 bytes, read LSB to MSB

#Heat On, 70C, HVane Left and Right, VVane mid
irDATA = [0x23, 0xCB, 0x26, 0x01, 0x00, 0x20, 0x08, 0x15, 0x80, 0x59, 0x83, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

#Cool On, 
#irDATA = [0x23, 0xCB, 0x26, 0x01, 0x00, 0x20, 0x18, 0x18, 0x80, 0x59, 0x83, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

CheckSum = sum(irDATA) - (math.floor(sum(irDATA)/256))*256
irDATA.append(CheckSum) #0x0C

cycle_tx=[0] #This will hold one cycle of the carrier

pi = pigpio.pi() # Connect to local Pi.

pi.set_mode(GPIO, pigpio.OUTPUT);#Set the GPIO to OUTPUT
pi.set_mode(23, pigpio.OUTPUT)
pi.set_mode(25, pigpio.INPUT)

#Create one period of carrier
cycle_pulse = [
  pigpio.pulse(1<<GPIO, 0, round(ir_tx_per/2)),
  pigpio.pulse(0, 1<<GPIO, round(ir_tx_per/2))
  ]

cur_data = []
for x in range (0, math.floor(HEADER_MARK/ir_tx_per)):
  cur_data.extend(cycle_pulse) #Add Modulated Header Mark

cur_data.extend([
  pigpio.pulse(1<<GPIO, 0, round(ir_tx_per/2)),
  pigpio.pulse(0, 1<<GPIO, math.floor(HEADER_SPACE))
  ]) #Add Header Space

pi.wave_add_generic(cur_data);
header_pulse=[]
header_pulse = pi.wave_create();#Store the wave

cur_data=[]
index = 0
while (index < len(irDATA)):
  bitTEST = 0x01
  while (bitTEST < 0x100):
    if ((bitTEST & irDATA[index]) == bitTEST):
      for x in range (0, math.floor(BIT_MARK/ir_tx_per)):
        cur_data.extend(cycle_pulse) #Add Modulated One Mark
        
      cur_data.extend([
        pigpio.pulse(1<<GPIO, 0, round(ir_tx_per/2)),
        pigpio.pulse(0, 1<<GPIO, ONE_SPACE)
        ]) #Add One Space
    else:
       for x in range (0, math.floor(BIT_MARK/ir_tx_per)):
        cur_data.extend(cycle_pulse) #Add Modulated Zero Mark
       
       cur_data.extend([
        pigpio.pulse(1<<GPIO, 0, round(ir_tx_per/2)),
        pigpio.pulse(0, 1<<GPIO, ZERO_SPACE)
        ]) #Add Zero Space
    bitTEST = bitTEST<<1
  #End Bit Test While
  index = index + 1
#End List Element Increment Loop

pi.wave_add_generic(cur_data);
data_pulse=[]
data_pulse = pi.wave_create();#Store the wave

cur_data=[]
for x in range (0, math.floor(REPEAT_MARK/ir_tx_per)):
	cur_data.extend(cycle_pulse)
	
cur_data.extend([
	pigpio.pulse(1<<GPIO, 0, round(ir_tx_per/2)),
	pigpio.pulse(0, 1<<GPIO, REPEAT_SPACE)
	])

pi.wave_add_generic(cur_data);
repeat_pulse=[]
repeat_pulse = pi.wave_create();

#----------------------------------------------------------

#Build and Send Chain
pi.wave_chain([header_pulse, data_pulse, repeat_pulse, header_pulse, data_pulse]) #Send Chain

while pi.wave_tx_busy():
	time.sleep(0.35);

pi.wave_clear()

pi.stop()
