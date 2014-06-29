import struct
from time import time
from time import sleep
from numpy import mean
import serial


SYNC_BYTES = [0xaa, 0xaa]

def bigend_24b(b1, b2, b3):
    return b1* 255 * 255 + 255 * b2 + b3


"""
This is a Driver Class for the Neurosky Mindwave. The Mindwave consists of a
headset and an usb dongle.  The dongle communicates with the mindwave headset
wirelessly and can relay the data to a program that opens its usb serial port.

Some clarification on the Neurosky docs: The Neurosky Chip/Board is used in
several devices, for example the Neurosky Mindset, the Neurosky Mindwave,
Mattel MindFlex and several others. These chips all use the same protocol over
a serial connection, but depending on the device, some kind of middleware is
used. The Mindset uses bluetooth to communicate with the computer, the Mindwave
has its own proprietary dongle, and the MindFlex uses a dumbed down RF protocol
to communicate with the "main" board of the game.

However, all of these devices speak essentially the same protocol. I also had
the impression, before reading the docs, that only the Mindset provides raw
values, which is obviously not the case.

The Mindwave ships with a TCP/IP server to provide apps a relatively easy way
to access the data. Maybe I will write a substitute in Python in the future,
but for now I am satisfied with using Python only.
"""

class VirtualParser(object):
    
    """Setting callback:a call back can be associated with all the above 
    variables so that a function is called when the variable is updated. 
    Syntax: setCallBack("variable",callback_function)
    for eg. to set a callback for attention data the syntax will be 
    setCallBack("attention",callback_function)"""
    __attention=0
    __meditation=0
    __raw_value=0
    __raw_values=[]
    __delta=0
    __theta=0
    __low_alpha=0
    __high_alpha=0
    __low_beta=0
    __high_beta=0
    __low_gamma=0
    __mid_gamma=0    
    __poor_signal=0
    __blink_strength=0 

    callBacksDictionary={} #keep a track of all callbacks
    
    def __init__(self, input_fstream, raw_buffer_len=512):
        #self.parser = self.run()
        #self.parser.next()
        self.current_meditation = 0
        self.current_attention= 0
        self.current_blink_strength = 0
        self.current_spectrum = []
        self.sending_data = False
        self.dongle_state ="initializing"
        self.raw_file = None
        self.esense_file = None
        self.input_fstream = input_fstream
        self.input_stream = []
        self.read_more_stream()
        self.raw_buffer_len = raw_buffer_len
        self.buffer_len = 512*3

    def is_sending_data(self):
        self.sending_data = True
        self.dongle_state = 'connected'

    def read_more_stream(self):
        self.input_stream += [ord(b) for b in list(self.input_fstream.read(1000))]
        sleep(0.1)

    def parse_payload(self, payload):
        while len(payload) > 0:
            #@TODO parse excode?  13.07 2013 (houqp)
            code = payload.pop(0)
            if code >= 0x80:
                vlen = payload.pop(0)
                # multi-byte codes
                if code == 0x80:
                    self.is_sending_data()
                    high_word = payload.pop(0)
                    low_word = payload.pop(0)
                    value = high_word * 256 + low_word
                    if value > 32768:
                        value -= 65536
                    self.raw_value = value
                elif code == 0x83:
                    self.is_sending_data()
                    # ASIC_EEG_POWER_INT
                    # delta, theta, low-alpha, high-alpha, low-beta, high-beta,
                    # low-gamma, high-gamma
                    self.delta=bigend_24b(payload.pop(0), payload.pop(0), payload.pop(0))
                    self.theta=bigend_24b(payload.pop(0), payload.pop(0), payload.pop(0))
                    self.low_alpha=bigend_24b(payload.pop(0), payload.pop(0), payload.pop(0))
                    self.high_alpha=bigend_24b(payload.pop(0), payload.pop(0), payload.pop(0))
                    self.low_beta=bigend_24b(payload.pop(0), payload.pop(0), payload.pop(0))
                    self.high_beta=bigend_24b(payload.pop(0), payload.pop(0), payload.pop(0))
                    self.low_gamma=bigend_24b(payload.pop(0), payload.pop(0), payload.pop(0))
                    self.mid_gamma=bigend_24b(payload.pop(0), payload.pop(0), payload.pop(0))

                elif code == 0xd0:
                    # headset found
                    # 0xaa 0xaa 0x04 0xd0 0x02 0x05 0x05 0x23
                    self.global_id = 255 * payload.pop(0) + payload.pop(0)
                    self.dongle_state = 'connected'
                elif code == 0xd1:
                    # headset not found
                    # 0xaa 0xaa 0x04 0xd1 0x02 0x05 0x05 0xf2
                    self.error = 'not found'
                elif code == 0xd2:
                    # 0xaa 0xaa 0x04 0xd2 0x02 0x05 0x05 0x21
                    self.disconnected_global_id = 255 * payload.pop(0) + payload.pop(0)
                    self.dongle_state = 'disconnected'
                elif code == 0xd3:
                    # request denied
                    # 0xaa 0xaa 0x02 0xd3 0x00 0x2c
                    self.error = 'request denied'
                elif code == 0xd4:
                    # standby mode, only pop the useless byte
                    # 0xaa 0xaa 0x03 0xd4 0x01 0x00 0x2a
                    self.dongle_state = 'standby'
                    payload.pop(0)
                else:
                    # unknown multi-byte codes
                    pass
            else:
                # single-byte codes
                val = payload.pop(0)
                self.is_sending_data()
                if code == 0x02:
                    self.poor_signal = val
                elif code == 0x04:
                    self.attention = val
                elif code == 0x05:
                    self.meditation = val
                elif code == 0x16:
                    self.blink_strength = val
                else:
                    # unknown code
                    pass

    def consume_stream(self):
        while 1:
            while self.input_stream[:2] != SYNC_BYTES:
                retry = 0
                while len(self.input_stream) <= 3:
                    retry += 1
                    if retry > 3:
                        return False
                    self.read_more_stream()
                self.input_stream.pop(0)
            # remove sync bytes
            self.input_stream.pop(0)
            self.input_stream.pop(0)
            plen = 170
            while plen == 170:
                # we are in sync now
                if len(self.input_stream) == 0:
                    return False
                plen = self.input_stream.pop(0)
                if plen == 170:
                    # in sync
                    continue
                else:
                    break
            if plen > 170:
                # plen too large
                continue

            if (len(self.input_stream) < plen + 1):
                # read the payload and checksum
                self.read_more_stream()
            if (len(self.input_stream) < plen + 1):
                return False

            chksum = 0
            for bv in self.input_stream[:plen]:
                chksum += bv
            # take the lowest byte and invert
            chksum = chksum & ord('\xff')
            chksum = (~chksum) & ord('\xff')
            payload = self.input_stream[:plen+1]
            self.input_stream = self.input_stream[plen+1:]
            # pop chksum and compare
            if chksum != payload.pop():
                # invalid payload, skip
                continue
            else:
                self.parse_payload(payload)
                return

    def update(self):
        self.consume_stream()
        #input_stream = self.input_fstream.read(1000)
        #for b in input_stream:
            #self.parser.send(ord(b))	# Send each byte to the generator

    def write_serial(self, string):
        self.input_fstream.write(string)

    def start_raw_recording(self, file_name):
        self.raw_file = file(file_name, "wt")
        self.raw_start_time = time()

    def start_esense_recording(self, file_name):
        self.esense_file = file(file_name, "wt")
        self.esense_start_time = time()

    def stop_raw_recording(self):
        if self.raw_file:
            self.raw_file.close()
            self.raw_file = None

    def stop_esense_recording(self):
        if self.esense_file:
            self.esense_file.close()
            self.esense_file = None

    def run(self):
        """
            This generator parses one byte at a time.
        """
        last = time()
        i = 1
        times = []
        while 1:
            byte = yield
            if byte== 0xaa:
                byte = yield # This byte should be "\aa" too
                if byte== 0xaa:
                    # packet synced by 0xaa 0xaa
                    packet_length = yield
                    packet_code = yield
                    if packet_code == 0xd4:
                        # standing by
                        self.dongle_state= "standby"
                    elif packet_code == 0xd0:
                        self.dongle_state = "connected"
                    elif packet_code == 0xd2:
                        data_len = yield
                        headset_id = yield
                        headset_id += yield
                        self.dongle_state = "disconnected"
                    else:
                        self.sending_data = True
                        left = packet_length-2
                        while left>0:
                            if packet_code ==0x80: # raw value
                                row_length = yield
                                a = yield
                                b = yield
                                value = struct.unpack("<h",chr(a)+chr(b))[0]
                                self.raw_values.append(value)
                                if len(self.raw_values)>self.buffer_len:
                                    self.raw_values = self.raw_values[-self.buffer_len:]
                                left-=2

                                if self.raw_file:
                                    t = time()-self.raw_start_time
                                    self.raw_file.write("%.4f,%i\n" %(t, value))
                            elif packet_code == 0x02: # Poor signal
                                a = yield
                                self.poor_signal = a
                                if a>0:
                                    pass
                                left-=1
                            elif packet_code == 0x04: # Attention (eSense)
                                a = yield
                                if a>0:
                                    v = struct.unpack("b",chr(a))[0]
                                    if v>0:
                                        self.current_attention = v
                                        if self.esense_file:
                                            self.esense_file.write("%.2f,,%i\n" % (time()-self.esense_start_time, v))
                                left-=1
                            elif packet_code == 0x05: # Meditation (eSense)
                                a = yield
                                if a>0:
                                    v = struct.unpack("b",chr(a))[0]
                                    if v>0:
                                        self.current_meditation = v
                                        if self.esense_file:
                                            self.esense_file.write("%.2f,%i,\n" % (time()-self.esense_start_time, v))

                                left-=1
                            elif packet_code == 0x16: # Blink Strength
                                self.current_blink_strength = yield
                                left-=1
                            elif packet_code == 0x83:
                                vlength = yield
                                self.current_vector = []
                                for row in range(8):
                                    a = yield
                                    b = yield
                                    c = yield
                                    value = a*255*255+b*255+c
                                    #value = c*255*255+b*255+a
                                    self.current_vector.append(value)
                                left -= vlength
                            packet_code = yield
                else:
                    pass # sync failed
            else:
                pass # sync failed
    
    def setCallBack(self,variable_name,callback_function):
        """Setting callback:a call back can be associated with all the above variables so that a function is called when the variable is updated. Syntax: setCallBack("variable",callback_function)
           for eg. to set a callback for attention data the syntax will be setCallBack("attention",callback_function)"""
        self.callBacksDictionary[variable_name]=callback_function
        
    #setting getters and setters for all variables
    
    #attention
    @property
    def attention(self):
        "Get value for attention"
        return self.__attention
    @attention.setter
    def attention(self,value):
        self.__attention=value
        if self.callBacksDictionary.has_key("attention"): #if callback has been set, execute the function
            self.callBacksDictionary["attention"](self.__attention)
            
    #meditation
    @property
    def meditation(self):
        "Get value for meditation"
        return self.__meditation
    @meditation.setter
    def meditation(self,value):
        self.__meditation=value
        if self.callBacksDictionary.has_key("meditation"): #if callback has been set, execute the function
            self.callBacksDictionary["meditation"](self.__meditation)
            
    #raw_value
    @property
    def raw_value(self):
        "Get value for raw_value"
        return self.__raw_value
    @raw_value.setter
    def raw_value(self,value):
        self.__raw_value=value
        self.__raw_values.append(value)
        if self.callBacksDictionary.has_key("raw_value"): #if callback has been set, execute the function
            self.callBacksDictionary["raw_value"](self.__raw_value)
        if len(self.__raw_values) == self.raw_buffer_len: 
            if self.callBacksDictionary.has_key("raw_values"): #if callback has been set, execute the function
                self.callBacksDictionary["raw_values"](self.__raw_values)
                del self.__raw_values[:]
            else:
                self.__raw_values.pop(0)

    #raw_values
    @property
    def raw_values(self):
        "Get value for raw_values"
        return self.__raw_values

    #delta
    @property
    def delta(self):
        "Get value for delta"
        return self.__delta
    @delta.setter
    def delta(self,value):
        self.__delta=value
        if self.callBacksDictionary.has_key("delta"): #if callback has been set, execute the function
            self.callBacksDictionary["delta"](self.__delta)

    #theta
    @property
    def theta(self):
        "Get value for theta"
        return self.__theta
    @theta.setter
    def theta(self,value):
        self.__theta=value
        if self.callBacksDictionary.has_key("theta"): #if callback has been set, execute the function
            self.callBacksDictionary["theta"](self.__theta)

    #low_alpha
    @property
    def low_alpha(self):
        "Get value for low_alpha"
        return self.__low_alpha
    @low_alpha.setter
    def low_alpha(self,value):
        self.__low_alpha=value
        if self.callBacksDictionary.has_key("low_alpha"): #if callback has been set, execute the function
            self.callBacksDictionary["low_alpha"](self.__low_alpha)

    #high_alpha
    @property
    def high_alpha(self):
        "Get value for high_alpha"
        return self.__high_alpha
    @high_alpha.setter
    def high_alpha(self,value):
        self.__high_alpha=value
        if self.callBacksDictionary.has_key("high_alpha"): #if callback has been set, execute the function
            self.callBacksDictionary["high_alpha"](self.__high_alpha)


    #low_beta
    @property
    def low_beta(self):
        "Get value for low_beta"
        return self.__low_beta
    @low_beta.setter
    def low_beta(self,value):
        self.__low_beta=value
        if self.callBacksDictionary.has_key("low_beta"): #if callback has been set, execute the function
            self.callBacksDictionary["low_beta"](self.__low_beta)

    #high_beta
    @property
    def high_beta(self):
        "Get value for high_beta"
        return self.__high_beta
    @high_beta.setter
    def high_beta(self,value):
        self.__high_beta=value
        if self.callBacksDictionary.has_key("high_beta"): #if callback has been set, execute the function
            self.callBacksDictionary["high_beta"](self.__high_beta)

    #low_gamma
    @property
    def low_gamma(self):
        "Get value for low_gamma"
        return self.__low_gamma
    @low_gamma.setter
    def low_gamma(self,value):
        self.__low_gamma=value
        if self.callBacksDictionary.has_key("low_gamma"): #if callback has been set, execute the function
            self.callBacksDictionary["low_gamma"](self.__low_gamma)

    #mid_gamma
    @property
    def mid_gamma(self):
        "Get value for mid_gamma"
        return self.__mid_gamma
    @mid_gamma.setter
    def mid_gamma(self,value):
        self.__mid_gamma=value
        if self.callBacksDictionary.has_key("mid_gamma"): #if callback has been set, execute the function
            self.callBacksDictionary["mid_gamma"](self.__mid_gamma)
    
    #poor_signal
    @property
    def poor_signal(self):
        "Get value for poor_signal"
        return self.__poor_signal
    @poor_signal.setter
    def poor_signal(self,value):
        self.__poor_signal=value
        if self.callBacksDictionary.has_key("poor_signal"): #if callback has been set, execute the function
            self.callBacksDictionary["poor_signal"](self.__poor_signal)
    
    #blink_strength
    @property
    def blink_strength(self):
        "Get value for blink_strength"
        return self.__blink_strength
    @blink_strength.setter
    def blink_strength(self,value):
        self.__blink_strength=value
        if self.callBacksDictionary.has_key("blink_strength"): #if callback has been set, execute the function
            self.callBacksDictionary["blink_strength"](self.__blink_strength)


class Parser(VirtualParser):
    def __init__(self, serial_dev='/dev/ttyUSB0'):
        self.dongle = serial.Serial(serial_dev,  115200, timeout=0.001)
        VirtualParser.__init__(self, self.dongle)



