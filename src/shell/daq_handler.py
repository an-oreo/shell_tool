import numpy as np
from PyDAQmx import *
import constants as CON
import os
from timer import Timer

data = np.zeros(0, dtype=np.float64)
time = Timer(0, CON.sample_rate_, 0)


def buffer_resize(data_size, _dtype=np.float64, maintain=False, *args, **kwargs):
    global data, time
    if maintain:
        buff_size = len(data)
        if buff_size > data_size:
            data = np.concatenate([data, np.zeros(data_size-buff_size, dtype=data.dtype)])
            # time = np.concatenate([time, np.zeros(data_size-buff_size, dtype=time.dtype)])
        else:
            data = data[0:data_size]
            # time = time[0:data_size]
    else:
        data = np.zeros(data_size, _dtype)
        # time = np.zeros(data_size, _dtype)


def fin_read(samples, sample_rate=CON.sample_rate_,
             min=CON.min_, max=CON.max_, expand=True, *args, **kwargs):
    global data, time  # -- may be needed?
    # buffer_resize(samples)
    buf_size = len(data)
    if samples > buf_size:
        if not expand:
            samples = buf_size
            print('Warning: data buffer truncated')
        else:
            buffer_resize(samples)
            # print('extended')
    from math import ceil
    timeout = ceil(samples * (1.0/sample_rate))
    analog_input = Task()
    read = int32()
    analog_input.CreateAIVoltageChan("Dev1/ai0", "", DAQmx_Val_Cfg_Default, min, max, DAQmx_Val_Volts,None)
    analog_input.CfgSampClkTiming("", sample_rate, DAQmx_Val_Rising,DAQmx_Val_FiniteSamps, samples)
    analog_input.StartTask()
    analog_input.ReadAnalogF64(samples, timeout, DAQmx_Val_GroupByChannel, data, len(data), byref(read), None)
    print("Acquired {} points".format(read.value))


def con_read(sample_rate=CON.sample_rate_, samples=CON.samples_, min=CON.min_, max=CON.max_, *args, **kwargs):
    analog_input = Task()
    read = int32()
    analog_input.CreateAIVoltageChan("Dev1/ai0", "", DAQmx_Val_Cfg_Default, min, max, DAQmx_Val_Volts, None)
    analog_input.CfgSampClkTiming("", sample_rate, DAQmx_Val_Rising, DAQmx_Val_FiniteSamps, samples)
    analog_input.StartTask()
    analog_input.ReadAnalogF64(samples, 10.0, DAQmx_Val_GroupByChannel, data, len(data), byref(read), None)
    print("Acquired {} points".format(read.value))


def view(entries: int, tail: bool, *args, **kwargs):
    if tail:
        print(data[-int(entries):])
    else:
        print(data[0:int(entries)])


def get_path(file=None):
    import os
    path = os.getcwd()
    try:
        path = os.path.join(path, 'OUTPUT')
    except FileNotFoundError:
        os.mkdir('OUTPUT')
        path = os.path.join(path, 'OUTPUT')
    if file:
        path = os.path.join(path,file)
    return path


def save(file_name, path=None, delim=None, *args, **kwargs):
    if not path:
        path = get_path()
    filename, extension = file_name.split('.')
    key = data.dtype.name
    delim_dict = {'.txt': ' ',
                  '.mat': ' ',
                  '.csv': ',',
                  '.gz': ' '
                  }
    fmt_dict = {'float64': '%.18e',
                'float32': '%.9e',
                'float': '%.9e',
                # 'int32'  : '',
                # 'int64'  : '',
                # 'int': '',
                }
    if not delim:
        delim = delim_dict[extension]

    #  TODO: Data blocking for multiple smaller files
    np.savetxt(os.path.join(path, filename) + extension, data,
               delimiter=delim, fmt=fmt_dict.get(key, '%.18e'))

    with open(os.path.join(path, filename) + '_t.' + extension, 'w') as time_file:
        temp_time = time.initial
        for i in range(0, len(data)):
            time_file.writelines('{}\n'.format(item) for item in temp_time)
            time_file.write('{:.18e}'.format(temp_time))
            temp_time += time.time_step