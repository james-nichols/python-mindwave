#!/usr/bin/env python
# -*- coding:utf-8 -*-

import platform, sys, time, threading
import numpy as np

import OSC

from pymindwave import headset
from pymindwave.pyeeg import bin_power
from pymindwave.pyeeg import pfd 
from pymindwave.pyeeg import hfd

class HeadsetOSCManager(object):

    def __init__(self, serial_dev = '/dev/tty.MindWaveMobile-DevA', osc_host = '127.0.0.1', osc_port = '8000'):

        self.last_raw = [0. for i in range(512)]
            
        self.low_alpha_stab = ParameterStability(10)
        self.high_alpha_stab = ParameterStability(10)
        self.low_beta_stab = ParameterStability(10)
        self.high_beta_stab = ParameterStability(10)

        self.c_low_alpha_stab = ParameterStability(10)
        self.c_high_alpha_stab = ParameterStability(10)
        self.c_low_beta_stab = ParameterStability(10)
        self.c_high_beta_stab = ParameterStability(10)
        
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
        
        #self.low_alpha_interp = ParameterInterpolator(10, 3, osc_host, osc_port, "/smoothed_low_alpha")
        #self.high_alpha_interp = ParameterInterpolator(10, 3, osc_host, osc_port, "/smoothed_high_alpha")
        #self.low_beta_interp = ParameterInterpolator(10, 3, osc_host, osc_port, "/smoothed_low_beta")
        #self.high_beta_interp = ParameterInterpolator(10, 3, osc_host, osc_port, "/smoothed_high_beta")
        #self.low_gamma_interp = ParameterInterpolator(10, 3, osc_host, osc_port, "/smoothed_low_gamma")
        #self.mid_gamma_interp = ParameterInterpolator(10, 3, osc_host, osc_port, "/smoothed_mid_gamma")
        #self.high_gamma_interp = ParameterInterpolator(10, 3, osc_host, osc_port, "/smoothed_high_gamma")
        #self.theta_interp = ParameterInterpolator(10, 3, osc_host, osc_port, "/smoothed_theta")
        #self.delta_interp = ParameterInterpolator(10, 3, osc_host, osc_port, "/smoothed_delta")
        
    def destroy(self):
        
        self.osc_client.disconnect()
         
    def attention_callback(self, value):
        msg = OSC.OSCMessage("/eegattention")
        print "Attention", value
        msg.append(value)
        self.osc_client.send(msg) 
        return None

    def meditation_callback(self, value):
        msg = OSC.OSCMessage("/eegmeditation")
        print "Meditation", value
        msg.append(value)
        self.osc_client.send(msg) 
        return None

    def raw_values_callback(self, raw_values):
        """ This function takes the raw values data, in blocks specified by the block size, and 
        sends it to the sound buffer """
        
        spec,rel_spec = bin_power(raw_values + self.last_raw, [0.5,4,7,9.5,12,21,30], 512)
         
        msg = OSC.OSCMessage("/calcdelta")
        msg.append(spec[0])
        self.osc_client.send(msg)
        msg = OSC.OSCMessage("/calctheta")
        msg.append(spec[1])
        self.osc_client.send(msg)
        
        msg = OSC.OSCMessage("/calclowbeta")
        msg.append(spec[4])
        self.osc_client.send(msg)
        
        self.c_low_beta_stab.add_point(spec[4])
        msg = OSC.OSCMessage("/calc_low_beta_instability")
        msg.append(self.c_low_beta_stab.stability)
        self.osc_client.send(msg) 

        msg = OSC.OSCMessage("/calchighbeta")
        msg.append(spec[5])
        self.osc_client.send(msg)

        self.c_high_beta_stab.add_point(spec[5])
        msg = OSC.OSCMessage("/calc_high_beta_instability")
        msg.append(self.c_high_beta_stab.stability)
        self.osc_client.send(msg) 

        msg = OSC.OSCMessage("/calclowalpha")
        msg.append(spec[2])
        self.osc_client.send(msg)

        self.c_low_alpha_stab.add_point(spec[2])
        msg = OSC.OSCMessage("/calc_low_alpha_instability")
        msg.append(self.c_low_alpha_stab.stability)
        self.osc_client.send(msg) 

        msg = OSC.OSCMessage("/calchighalpha")
        msg.append(spec[3])
        self.osc_client.send(msg)
        self.last_raw = raw_values

        self.c_high_alpha_stab.add_point(spec[3])
        msg = OSC.OSCMessage("/calc_high_alpha_instability")
        msg.append(self.c_high_alpha_stab.stability)
        self.osc_client.send(msg) 

        # We're going to try various parameters based on the raw data, from the EEG helpers
        eeg_hfd = hfd(raw_values, 10)
        eeg_pfd = pfd(raw_values)
        
        msg = OSC.OSCMessage("/eegpfd")
        msg.append(eeg_pfd)
        self.osc_client.send(msg)
        msg = OSC.OSCMessage("/eeghfd")
        msg.append(eeg_hfd)
        self.osc_client.send(msg)

        raw_values = [1. * float(i) / 32768. for i in raw_values]
        #print len(raw_values), raw_values
        msg = OSC.OSCMessage("/raw_data")
        msg.append(raw_values)
        self.osc_client.send(msg)

        return None

    def delta_callback(self, value):
        #self.delta_interp.insert_point(value)
        #if not self.delta_interp.is_alive():
        #    self.delta_interp.start()
        msg = OSC.OSCMessage("/eegdelta")
        msg.append(value)
        self.osc_client.send(msg) 

    def theta_callback(self, value):
        #self.theta_interp.insert_point(value)
        #if not self.theta_interp.is_alive():
        #    self.theta_interp.start()
        msg = OSC.OSCMessage("/eegtheta")
        msg.append(value)
        self.osc_client.send(msg) 
        return None

    def low_alpha_callback(self, value):
        #self.low_alpha_interp.insert_point(value)
        #if not self.low_alpha_interp.is_alive():
        #    self.low_alpha_interp.start()
        
        msg = OSC.OSCMessage("/eeglowalpha")
        msg.append(value)
        self.osc_client.send(msg) 
        
        self.low_alpha_stab.add_point(value)
        msg = OSC.OSCMessage("/low_alpha_instability")
        msg.append(self.low_alpha_stab.stability)
        self.osc_client.send(msg) 
        return None

    def high_alpha_callback(self, value):
        #self.high_alpha_interp.insert_point(value)
        #if not self.high_alpha_interp.is_alive():
        #    self.high_alpha_interp.start()

        msg = OSC.OSCMessage("/eeghighalpha")
        msg.append(value)
        self.osc_client.send(msg) 
        
        self.high_alpha_stab.add_point(value)
        msg = OSC.OSCMessage("/high_alpha_instability")
        msg.append(self.high_alpha_stab.stability)
        self.osc_client.send(msg) 
        return None

    def low_beta_callback(self, value):
        #self.low_beta_interp.insert_point(value)
        #if not self.low_beta_interp.is_alive():
        #    self.low_beta_interp.start()
        msg = OSC.OSCMessage("/eeglowbeta")
        msg.append(value)
        self.osc_client.send(msg) 
        
        self.low_beta_stab.add_point(value)
        msg = OSC.OSCMessage("/low_beta_instability")
        msg.append(self.low_beta_stab.stability)
        self.osc_client.send(msg) 
        return None

    def high_beta_callback(self, value):
        #self.high_beta_interp.insert_point(value)
        #if not self.high_beta_interp.is_alive():
        #    self.high_beta_interp.start()
        msg = OSC.OSCMessage("/eeghighbeta")
        msg.append(value)
        self.osc_client.send(msg) 
        
        self.high_beta_stab.add_point(value)
        msg = OSC.OSCMessage("/high_beta_instability")
        msg.append(self.high_beta_stab.stability)
        self.osc_client.send(msg) 
        return None

    def low_gamma_callback(self, value):
        #self.low_gamma_interp.insert_point(value)
        #if not self.low_gamma_interp.is_alive():
        #    self.low_gamma_interp.start()
        msg = OSC.OSCMessage("/eeglowgamma")
        msg.append(value)
        self.osc_client.send(msg) 
        return None

    def mid_gamma_callback(self, value):
        #self.mid_gamma_interp.insert_point(value)
        #if not self.mid_gamma_interp.is_alive():
        #    self.mid_gamma_interp.start()
        msg = OSC.OSCMessage("/eegmidgamma")
        msg.append(value)
        self.osc_client.send(msg) 
        return None

    def high_gamma_callback(self, value):
        #self.high_gamma_interp.insert_point(value)
        #if not self.high_gamma_interp.is_alive():
        #    self.high_gamma_interp.start()
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

class ParameterStability():

    def __init__(self, length):
        self.buf = np.zeros(length)
        self.stability = 0.0

    def add_point(self, value):
        self.buf[:-1] = self.buf[1:]
        self.buf[-1] = value
        
        self.stability = np.std(self.buf)
        #self.stability = (np.absolute(self.buf[1:] - self.buf[:-1]) / (self.buf.size)).sum()
  
class ParameterInterpolator(threading.Thread):
    
    def __init__(self, freq, buf_len, osc_host, osc_port, msg_name):

        self.frequency = freq
        self.buf = np.zeros(buf_len)

        self.interpolator = interpolate.interp1d([-1.0, 0.0, 1.0], self.buf, 'quadratic')
        self.interpolated_buf = self.interpolator(np.linspace(0.0, 1.0, self.frequency)) 
        self.interpolated_buf_counter = 0

        self.osc_client = OSC.OSCClient()
        self.osc_client.connect((osc_host, osc_port))
        self.osc_msg_name = msg_name
        
        self.running = True
        super(ParameterInterpolator, self).__init__()
    
    def insert_point(self, value):
        self.buf[:-1] = self.buf[1:]
        self.buf[-1] = value
        self.interpolator = interpolate.interp1d([-1.0, 0.0, 1.0], self.buf, 'quadratic')
        self.interpolated_buf = self.interpolator(np.linspace(0.0, 1.0, self.frequency)) 
        self.interpolated_buf_counter = 0

    def run(self):
        while self.running:
            while self.interpolated_buf_counter < self.frequency:
                msg = OSC.OSCMessage(self.osc_msg_name)
                msg.append(self.interpolated_buf[self.interpolated_buf_counter])
                self.osc_client.send(msg) 
                self.interpolated_buf_counter += 1
                time.sleep(1.0 / float(self.frequency))
                 

    def stop(self):

        self.osc_client.disconnect()
        self.running = False
        selt._Thread__stop()
      
if __name__ == "__main__":
    
    #hsm = HeadsetSoundManager()
    local_ip = "127.0.0.1"
    pia_ip = "192.168.0.27"
    host_port_SC = 57120 
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
    hsm.destroy()
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
