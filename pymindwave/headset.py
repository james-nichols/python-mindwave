#!/usr/bin/env python
# -*- coding:utf-8 -*-

import threading
import serial
import parser
import time


COMMAND_BYTES = {
    'auto_connect': '\xc2',
    'disconnect': '\xc1',
}



class DongleReader(threading.Thread):
    def __init__(self, parser, *args, **kwargs):
        self.parser = parser
        self.running = True
        super(DongleReader, self).__init__(*args, **kwargs)

    def run(self):
        while self.running:
            if not self.parser.sending_data:
                time.sleep(0.5)
            self.parser.update()

    def stop(self):
        self.running = False
        self._Thread__stop()


class Headset(object):
    def __init__(self, dongle_dev, global_id=None):
        if global_id:
            self.auto_connect = False
            self.global_id = global_id
        else:
            self.auto_connect = True
        self.dongle_dev = dongle_dev
        self.dongle_fs = serial.Serial(dongle_dev,  115200, timeout=0.001)
        self.parser = parser.VirtualParser(self.dongle_fs)
        # setup listening thread
        self.dongle_reader = DongleReader(self.parser)
        self.dongle_reader.daemon = True
        self.dongle_reader.start()

    def connect(self):
        if self.auto_connect:
            self.dongle_fs.write(COMMAND_BYTES['auto_connect'])
        else:
            #@TODO connect to specific headset  11.07 2013 (houqp)
            pass

    def disconnect(self):
        self.dongle_fs.write(COMMAND_BYTES['disconnect'])

    def destroy(self):
        self.dongle_reader.stop()
        self.dongle_fs.close()

    def get_state(self):
        return self.parser.dongle_state

    def get_attention(self):
        return self.parser.attention

    def get_meditation(self):
        return self.parser.meditation

    def get_raw_values(self):
        return self.parser.raw_values

    def get_waves_vector(self):
        return self.parser.current_vector

    def get_delta_waves(self):
        return self.parser.delta

    def get_theta_waves(self):
        return self.parser.theta

    def get_alpha_waves(self):
        return (self.parser.low_alpha + self.parser.high_alpha) / 2

    def get_beta_waves(self):
        return (self.parser.low_beta + self.parser.high_beta) / 2

    def get_gamma_waves(self):
        return (self.parser.low_gamma + self.parser.mid_gamma) / 2

    def get_blink_strength(self):
        return self.parser.blink_strength

    def get(self, stuff):
        if stuff == 'attention':
            return self.get_attention()
        elif stuff == 'meditation':
            return self.get_meditation()
        elif stuff == 'raw_values':
            return self.get_raw_values()
        elif stuff == 'state':
            return self.get_state()
        elif stuff == 'waves_vector':
            return self.get_waves_vector()
        elif stuff == 'delta_waves':
            return self.get_delta_waves()
        elif stuff == 'theta_waves':
            return self.get_theta_waves()
        elif stuff == 'alpha_waves':
            return self.get_alpha_waves()
        elif stuff == 'beta_waves':
            return self.get_beta_waves()
        elif stuff == 'gamma_waves':
            return self.get_gamma_waves()
        elif stuff == 'blink_strength':
            return self.get_blink_strength()
        else:
            return None

    def setCallBack(self, variable_name, callback_function):
        self.parser.setCallBack(variable_name, callback_function)
