#!/usr/bin/env python
# -*- coding:utf-8 -*-

import platform, sys, time, threading
import numpy as np
from scipy import signal
from scipy import interpolate

import OSC
import pyaudio

from pymindwave import headset
from pymindwave.pyeeg import bin_power
from pymindwave.pyeeg import pfd 
from pymindwave.pyeeg import hfd

class HeadsetRecorderManager(object):

    def __init__(self, serial_dev = '/dev/tty.MindWaveMobile-DevA'):
        
        self.f = open('recorded_headset.txt', 'w')

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
        
    def destroy(self):
        
        self.osc_client.disconnect()
         
    def attention_callback(self, value):
        self.f.write("attention, {0}\n".format(value))
        return None

    def meditation_callback(self, value):
        self.f.write("meditation, {0}\n".format(value))
        return None

    def raw_values_callback(self, raw_values):
        """ This function takes the raw values data, in blocks specified by the block size, and 
        sends it to the sound buffer """
        print raw_values
        self.f.write("raw_data, {0}\n".format(raw_values))
        return None

    def delta_callback(self, value):
        self.f.write("delta, {0}\n".format(value))
        return None

    def theta_callback(self, value):
        self.f.write("theta, {0}\n".format(value))
        return None

    def low_alpha_callback(self, value):
        self.f.write("low_alpha, {0}\n".format(value))
        return None

    def high_alpha_callback(self, value):
        self.f.write("high_alpha, {0}\n".format(value))
        return None

    def low_beta_callback(self, value):
        self.f.write("low_beta, {0}\n".format(value))
        return None

    def high_beta_callback(self, value):
        self.f.write("high_beta, {0}\n".format(value))
        return None

    def low_gamma_callback(self, value):
        self.f.write("low_gamma, {0}\n".format(value))
        return None

    def mid_gamma_callback(self, value):
        self.f.write("mid_gamma, {0}\n".format(value))
        return None

    def high_gamma_callback(self, value):
        self.f.write("high_gamma, {0}\n".format(value))
        return None

    def blink_strength_callback(self, value):
        self.f.write("blink_strength, {0}\n".format(value))
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
  
if __name__ == "__main__":
    
    hsm = HeadsetRecorderManager()
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

