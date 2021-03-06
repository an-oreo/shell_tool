#!/usr/bin/env python
# vim:fileencoding=utf-8
# -*- coding: utf-8 -*-
"""
shell_tool
daq_handler.py
Author: Danyal Ahsanullah
Date: 4/24/2017
License: N/A
Description: daq handler that uses the PyDAQmx bindings to the NI DAQmx drivers
"""

import os
import threading
import numpy as np
from PyDAQmx import *
from math import ceil
from utils.timer import Timer
from utils import daq_utils as dq
from utils import constants as con


def fin_read(samples, sample_rate=con.sample_rate_, min=con.min_, max=con.max_, expand=True, *args, **kwargs):
    # global data, time  # -- may be needed?
    # buffer_resize(samples)
    buf_size = len(dq.data)
    if samples > buf_size:
        if not expand:
            samples = buf_size
            print('Warning: data buffer truncated')
        else:
            dq.buffer_resize(samples)
            # print('extended')
    timeout = ceil(samples * (1.0/sample_rate))
    analog_input = Task()
    read = int32()
    analog_input.CreateAIVoltageChan("Dev1/ai0", "", DAQmx_Val_Cfg_Default, min, max, DAQmx_Val_Volts,None)
    analog_input.CfgSampClkTiming("", sample_rate, DAQmx_Val_Rising,DAQmx_Val_FiniteSamps, samples)
    analog_input.StartTask()
    analog_input.ReadAnalogF64(samples, timeout, DAQmx_Val_GroupByChannel, dq.data, len(dq.data), byref(read), None)
    print("Acquired {} points".format(read.value))


def con_read(sample_rate=con.sample_rate_, min=con.min_, max=con.max_, file_name='OUTPUT.txt', *args, **kwargs):
    run_event = threading.Event()
    run_event.set()
    it = threading.Thread(target=dq.kb_int, args=(run_event,))
    pt = threading.Thread(target=dq.process_running, args=(run_event,))
    print('reading...')
    it.start()
    pt.start()
    j = 0
    chunk = np.zeros(con.chunk_)
    filename, extension = file_name.split('.')
    analog_input = Task()
    read = int32()
    analog_input.CreateAIVoltageChan("Dev1/ai0", "", DAQmx_Val_Cfg_Default, min, max, DAQmx_Val_Volts, None)
    analog_input.CfgSampClkTiming("", sample_rate, DAQmx_Val_Rising, DAQmx_Val_FiniteSamps, con.chunk_)
    analog_input.StartTask()
    timeout = ceil(con.chunk_ * (1.0/sample_rate))
    with open(os.path.join(dq.get_path(), file_name), 'a') as file:
        while run_event.is_set():
            analog_input.ReadAnalogF64(con.chunk_, timeout, DAQmx_Val_GroupByChannel,
                                       chunk, con.chunk_, byref(read), None)
            [file.write('{}{}'.format(val, '\n')) for val in chunk]
            chunk = np.zeros(con.chunk_)
            j += 1
        pts = j*con.chunk_
        print("Acquired {} points".format(pts))
        dq.time = Timer.get_timer('list', 0, sample_rate, pts)
        dq.time.savetxt(os.path.join(dq.get_path(), filename + '_t.' + extension))
        it.join()
        pt.join()
    return pts


if __name__ == '__main__':
    # print(len(data))
    print(con_read(file_name='test.txt') == len(dq.data))
    # print(data)
