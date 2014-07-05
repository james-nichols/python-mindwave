#!/usr/bin/env python
# -*- coding:utf-8 -*-

import platform
import sys, time
import numpy as np
from scipy import signal

import OSC
import pyaudio

from pymindwave import headset
from pymindwave.pyeeg import bin_power

class HeadsetSoundManager(object):

    def __init__(self, serial_dev = '/dev/tty.MindWaveMobile-DevA', sample_rate = 44100):

        self.hs = headset.Headset(serial_dev) 
        self.hs.setCallBack("attention", self.attention_callback)
        self.hs.setCallBack("raw_values", self.raw_values_callback)
        
        self.sample_rate = sample_rate
        self.sound_buffer = np.zeros(self.sample_rate)
        
        self.pa = pyaudio.PyAudio()
        self.stream = self.pa.open(format=pyaudio.paInt16,
            channels = 1,
            rate = self.sample_rate,
            output = True,
            stream_callback = self.poll_buffer)

        self.stream.start_stream()

    def attention_callback(self, attention_value):
        "this function will be called everytime NeuroPy has a new value for attention"
        
        print "Value of attention is", attention_value
        
        return None

    def raw_values_callback(self, raw_values):
        """ This function takes the raw values data, in blocks specified by the block size, and 
        sends it to the sound buffer """
        
        #print len(signal.resample(raw_values, sample_rate))
        #print len(raw_values), raw_values
        #stream.write(10 * signal.resample(raw_values,sample_rate).astype(np.int16))
        self.sound_buffer = 5 * signal.resample(raw_values, self.sample_rate).astype(np.int16)
        print self.sound_buffer[:256], self.sound_buffer[:-256]
        return None

    def poll_buffer(self, in_data, frame_count, time_info, status):
        #print "flushing sound_buffer", sound_buffer, len(sound_buffer)
        return (self.sound_buffer, pyaudio.paContinue)
 
class HeadsetOSCManager(object):

    def __init__(self, serial_dev = '/dev/tty.MindWaveMobile-DevA', osc_host = '127.0.0.1', osc_port = '8000'):

        self.hs = headset.Headset(serial_dev)
        self.hs.setCallBack("attention", self.attention_callback)
        self.hs.setCallBack("meditation", self.meditation_callback)
        self.hs.setCallBack("raw_values", self.raw_values_callback)
        self.hs.setCallBack("delta", self.delta_callback)
        self.hs.setCallBack("theta", self.theta_callback)
        self.hs.setCallBack("low_alpha", self.low_alpha_callback)
        self.hs.setCallBack("high_alpha", self.high_alpha_callback)
        self.hs.setCallBack("low_beta", self.low_beta_callback)
        self.hs.setCallBack("high_beta", self.high_beta_callback)
        self.hs.setCallBack("low_gamma", self.low_gamma_callback)
        self.hs.setCallBack("mid_gamma", self.mid_gamma_callback)
        self.hs.setCallBack("high_gamma", self.high_gamma_callback)
        self.hs.setCallBack("blink_strength", self.blink_strength_callback)
        
        self.osc_host = osc_host
        self.osc_port = osc_port
        # Now setup OSC client to send data
        self.osc_client = OSC.OSCClient()
        self.osc_client.connect((self.osc_host, self.osc_port))
         
    def attention_callback(self, value):
        msg = OSC.OSCMessage("/eegattention")
        msg.append(value)
        self.osc_client.send(msg) 
        return None

    def meditation_callback(self, value):
        msg = OSC.OSCMessage("/eegmeditation")
        msg.append(value)
        self.osc_client.send(msg) 
        return None

    def raw_values_callback(self, raw_values):
        """ This function takes the raw values data, in blocks specified by the block size, and 
        sends it to the sound buffer """
        
        #print len(signal.resample(raw_values, sample_rate))
        print len(raw_values), raw_values
        msg = OSC.OSCMessage("/raw_data")
        msg.append(raw_values)
        self.osc_client.send(msg)
        
        #self.sound_buffer = 5 * signal.resample(raw_values, self.sample_rate).astype(np.int16)
        #print self.sound_buffer[:256]
        #print self.sound_buffer[:-255]
        return None

    def delta_callback(self, value):
        msg = OSC.OSCMessage("/eegdelta")
        msg.append(value)
        self.osc_client.send(msg) 

    def theta_callback(self, value):
        msg = OSC.OSCMessage("/eegtheta")
        msg.append(value)
        self.osc_client.send(msg) 
        return None

    def low_alpha_callback(self, value):
        msg = OSC.OSCMessage("/eeglowalpha")
        msg.append(value)
        self.osc_client.send(msg) 
        return None

    def high_alpha_callback(self, value):
        msg = OSC.OSCMessage("/eeghighalpha")
        msg.append(value)
        self.osc_client.send(msg) 
        return None

    def low_beta_callback(self, value):
        msg = OSC.OSCMessage("/eeglowbeta")
        msg.append(value)
        self.osc_client.send(msg) 
        return None

    def high_beta_callback(self, value):
        msg = OSC.OSCMessage("/eeghighbeta")
        msg.append(value)
        self.osc_client.send(msg) 
        return None

    def low_gamma_callback(self, value):
        msg = OSC.OSCMessage("/eeglowgamma")
        msg.append(value)
        self.osc_client.send(msg) 
        return None

    def mid_gamma_callback(self, value):
        msg = OSC.OSCMessage("/eegmidgamma")
        msg.append(value)
        self.osc_client.send(msg) 
        return None

    def high_gamma_callback(self, value):
        msg = OSC.OSCMessage("/eeghighgamma")
        msg.append(value)
        self.osc_client.send(msg) 
        return None

    def blink_strength_callback(self, value):
        msg = OSC.OSCMessage("/eegblinkstrength")
        msg.append(value)
        self.osc_client.send(msg) 
        return None

    def poll_buffer(self, in_data, frame_count, time_info, status):
        #print "flushing sound_buffer", sound_buffer, len(sound_buffer)
        return (self.sound_buffer, pyaudio.paContinue)
   
if __name__ == "__main__":
    
    #hsm = HeadsetSoundManager()
    local_ip = "127.0.0.1"
    pia_ip = "192.168.0.27"
    host_port_SC = 57110 
    #host_port_Max = 8000
    host_port_Max = 3444 

    #hsm = HeadsetOSCManager(osc_host = local_ip, osc_port = host_port_SC)
    hsm = HeadsetOSCManager(osc_host = local_ip, osc_port = host_port_Max)
    time.sleep(1)
    
    if hsm.hs.get_state() != 'connected':
        hsm.hs.disconnect()

    while hsm.hs.get_state() != 'connected':
        time.sleep(1)
        print 'current state: {0}'.format(hsm.hs.get_state())
        if (hsm.hs.get_state() == 'standby'):
            print 'trying to connect...'
            hsm.hs.connect()

    print 'now connected!'

    while True:
        time.sleep(1)

    print 'disconnecting...'
    hs.disconnect()
    hs.destroy()
    sys.exit(0)
  
""" 
sound_buffer = np.zeros(44100) 

def poll_buffer(in_data, frame_count, time_info, status):
    print "flushing sound_buffer", sound_buffer, len(sound_buffer)
    return (sound_buffer, pyaudio.paContinue)

# Instance of the audio stream
pa = pyaudio.PyAudio()
sample_rate = 44100
stream = pa.open(format=pyaudio.paInt16,
    channels=2,
    rate=sample_rate,
    output=True,
    stream_callback=poll_buffer)

stream.start_stream()

def raw_values_callback(raw_values):
    #print len(signal.resample(raw_values, sample_rate))
    #print len(raw_values), raw_values
    #stream.write(10 * signal.resample(raw_values,sample_rate).astype(np.int16))
    sound_buffer = 10 * signal.resample(raw_values, sample_rate).astype(np.int16)
    return None

def raw_to_spectrum(rawdata):
    flen = 50
    spectrum, relative_spectrum = bin_power(rawdata, range(flen), 512)
    #print spectrum
    #print relative_spectrum
    return spectrum

if __name__ == "__main__":
    if platform.system() == 'Darwin':
        hs = headset.Headset('/dev/tty.MindWaveMobile-DevA')
        #hs = headset.Headset('/dev/tty.MindWave-DevA')
    else:
        hs = headset.Headset('/dev/ttyUSB0')
    hs.setCallBack("attention", attention_callback)
    hs.setCallBack("raw_values", raw_values_callback)
    # wait some time for parser to udpate state so we might be able
    # to reuse last opened connection.
    time.sleep(1)
    if hs.get_state() != 'connected':
        hs.disconnect()

    while hs.get_state() != 'connected':
        time.sleep(1)
        print 'current state: {0}'.format(hs.get_state())
        if (hs.get_state() == 'standby'):
            print 'trying to connect...'
            hs.connect()

    print 'now connected!'
    
    stream.start_stream()

    #stream.start_stream()
    last_raw = hs.get_raw_values()
    while True:
        #print 'wait 1s to collect data...'
        time.sleep(1)
        #print 'attention {0}, meditation {1}'.format(hs.get('attention'), hs.get('meditation'))
        #print 'alpha_waves {0}'.format(hs.get('alpha_waves'))
        #print 'blink_strength {0}'.format(hs.get('blink_strength'))
        #print 'raw data:'
        #print hs.get('rawdata'), len(hs.get('rawdata'))

        #print raw_to_spectrum(hs.get('rawdata'))
        



    print 'disconnecting...'
    hs.disconnect()
    hs.destroy()
    sys.exit(0)

    """
