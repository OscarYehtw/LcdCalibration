# 11/23/2020 cluadeliao@
# 1. Add flicker measurement

# 11/28/2020 claudeliao@
# 1. Fix bug

# 12/07/2020 claudeliao@
# 1. Comment octopus change_color_mode() function to fix b/174821312

# 12/15/2020 claudeliao@
# 1. Update logging for multi-up

"""
Copyright 2020 Google Inc. All Rights Reserved.
Author: claudeliao@
Last updated: 12/15/2020
"""
import time

from ColorCalFramework.CS2000 import *
from ColorCalFramework.Hyperion import *
from ColorCalFramework.PR_Series import *
# from ColorCalFramework.Octopus import *
from ColorCalFramework.color_basic_class_func import *
import logging

# +++++++++++++
def measure(patterns, cal_cfg, fct_tool, delay_time=0.2):

    cs2000 = None
    hyperion = None
    pr_series = None
    # dsn = cal_cfg.sn
    instrument = cal_cfg.instrument_type
    # pattern_apk = cal_cfg.pattern_apk
    user_matrix = cal_cfg.user_matrix
    serial_port = cal_cfg.serial_port

    results = []

    if instrument == InstrumentType.CS2000:
        cs2000 = CS2000(serial_port)
        cs2000.open()
    elif instrument == InstrumentType.Hyperion:
        hyperion = Hyperion(usb_port=serial_port)
        hyperion.open()
    elif instrument == InstrumentType.PRSeries:
        pr_series = PRSeries(serial_port)
        pr_series.open()
    else:
        print('[ERROR] No instrument for connection.')
        return False

    try:

        for i in range(len(patterns)):
            if patterns[i] is None:
                continue

            result = fct_tool.set_background_color(patterns[i].R, patterns[i].G, patterns[i].B)

            if result:
                logging.info('start measuring')
            else:
                logging.info('[ERROR] fail to switch color pattern')
                continue

            time.sleep(delay_time)

            if instrument == InstrumentType.CS2000:
                if cs2000.measure_data():
                    XYZ = cs2000.read_measured_data(data_mode=DataMode.COLORIMETRIC_DATA,
                                                    colorimetric_data_type=ColorimetricDataType.XYZ)
            elif instrument == InstrumentType.PRSeries:
                if pr_series.measure_data():
                    XYZ = pr_series.read_measured_data(data_code=DataCode.XYZ)
            elif instrument == InstrumentType.Hyperion:
                XYZ = hyperion.measure(sbw=user_matrix)
                if XYZ is None:
                    for j in range(3):
                        XYZ = hyperion.measure(sbw=user_matrix)
                        if not XYZ is None:
                            break
                        else:
                            print('[ERROR] hyperion measure failed!')
                        time.sleep(0.1)
            else:
                print('No instrument for measurement.')
                return False

            patterns[i].XYZ = np.array(XYZ)
            # add x, y
            sum_xyz = (patterns[i].X + patterns[i].Y + patterns[i].Z)
            if sum_xyz > 0:
                x = patterns[i].X / sum_xyz
                y = patterns[i].Y / sum_xyz
            else:
                x = 0
                y = 0
            results.append([patterns[i].name, patterns[i].R, patterns[i].G, patterns[i].B,
                            patterns[i].X, patterns[i].Y, patterns[i].Z, x, y])

    except Exception as e:
        print(' ********** [ERROR] measurement exception **********')
        print('[ERROR] {}'.format(e))
        print(' ********** [ERROR] measurement exception **********')

    finally:
        if instrument == InstrumentType.CS2000:
            if not cs2000 is None:
                cs2000.close()
        elif instrument == InstrumentType.Hyperion:
            if not hyperion is None:
                hyperion.close()
        elif instrument == InstrumentType.PRSeries:
            if not pr_series is None:
                pr_series.close()
        else:
            print('[ERROR] No instrument to close.')

    return results

def measure_logger_retries(patterns, cal_cfg, fct_tool, test_data, delay_time=0.2):
    '''
    investigate retest issue where measurements are sometimes empty
    this method prints info to test_data.logger
    this method deploys 10 tries before return. retries_delay is hard coded to 0.5s
    '''
    cs2000 = None
    hyperion = None
    pr_series = None
    # dsn = cal_cfg.sn
    instrument = cal_cfg.instrument_type
    # pattern_apk = cal_cfg.pattern_apk
    user_matrix = cal_cfg.user_matrix
    serial_port = cal_cfg.serial_port

    retries = 10
    retries_delay = 0.5
    results = []

    if instrument == InstrumentType.CS2000:
        cs2000 = CS2000(serial_port)
        cs2000.open()
    elif instrument == InstrumentType.Hyperion:
        hyperion = Hyperion(usb_port=serial_port)
        hyperion.open()
    elif instrument == InstrumentType.PRSeries:
        pr_series = PRSeries(serial_port)
        pr_series.open()
    else:
        print('[ERROR] No instrument for connection.')
        return False

    try:

        for i in range(len(patterns)):
            if patterns[i] is None:
                test_data.logger.error(f'{patterns[i]} pattern is None! Skip.')
                continue
            # debug TODO: remove below
            test_data.logger.info(f' start test pattern name:{patterns[i].name}, index:{i}')
            test_data.logger.info(f'R:{patterns[i].R}, G:{patterns[i].G}, B:{patterns[i].B}')
            # debug end

            result = fct_tool.set_background_color(patterns[i].R, patterns[i].G, patterns[i].B)

            if result:
                logging.info('start measuring')
            else:
                # failure occured -> previously causeing empty values -> retest
                while retries >= 0:
                  time.sleep(retries_delay)
                  result = fct_tool.set_background_color(patterns[i].R, patterns[i].G, patterns[i].B)
                  test_data.logger.info(f'{patterns[i]} - FCT failed to switch background. Retries left: {retries}!')
                  retries = retries - 1
                  if result:
                    # retries pass
                    break
                if not result:
                  # retries fail
                  logging.info('[ERROR] fail to switch color pattern')
                  test_data.logger.error(f'{patterns[i]} - FCT failed to switch background! Skip.')
                  continue

            time.sleep(delay_time)

            if instrument == InstrumentType.CS2000:
                if cs2000.measure_data():
                    XYZ = cs2000.read_measured_data(data_mode=DataMode.COLORIMETRIC_DATA,
                                                    colorimetric_data_type=ColorimetricDataType.XYZ)
            elif instrument == InstrumentType.PRSeries:
                if pr_series.measure_data():
                    XYZ = pr_series.read_measured_data(data_code=DataCode.XYZ)
            elif instrument == InstrumentType.Hyperion:
                XYZ = hyperion.measure(sbw=user_matrix)
                if XYZ is None:
                    for j in range(3):
                        XYZ = hyperion.measure(sbw=user_matrix)
                        if not XYZ is None:
                            break
                        else:
                            test_data.logger.error('hyperion measure failed.')
                            print('[ERROR] hyperion measure failed!')
                        time.sleep(0.1)
            else:
                test_data.logger.error('No instrument for measurement.')
                print('No instrument for measurement.')
                return False

            patterns[i].XYZ = np.array(XYZ)

            # debug TODO: remove below
            test = XYZ
            test_data.logger.info(f'pattern {patterns[i].name} XYZ is {test}')
            # debug end

            # add x, y
            sum_xyz = (patterns[i].X + patterns[i].Y + patterns[i].Z)
            if sum_xyz > 0:
                x = patterns[i].X / sum_xyz
                y = patterns[i].Y / sum_xyz
            else:
                x = 0
                y = 0

            # debug TODO: remove below
            test = [patterns[i].name, patterns[i].R, patterns[i].G, patterns[i].B,
                            patterns[i].X, patterns[i].Y, patterns[i].Z, x, y]
            test_data.logger.info(f'test pattern name result:{test}')
            # debug end

            results.append([patterns[i].name, patterns[i].R, patterns[i].G, patterns[i].B,
                            patterns[i].X, patterns[i].Y, patterns[i].Z, x, y])

    except Exception as e:
        test_data.logger.error(f'Exception occured. {e}')
        print(' ********** [ERROR] measurement exception **********')
        print('[ERROR] {}'.format(e))
        print(' ********** [ERROR] measurement exception **********')

    finally:
        if instrument == InstrumentType.CS2000:
            if not cs2000 is None:
                cs2000.close()
        elif instrument == InstrumentType.Hyperion:
            if not hyperion is None:
                hyperion.close()
        elif instrument == InstrumentType.PRSeries:
            if not pr_series is None:
                pr_series.close()
        else:
            test_data.logger.error(f'No instrument to close')
            print('[ERROR] No instrument to close.')

    return results


def measure_calibrated_logger_retries(patterns, cal_cfg, fct_tool, test_data, delay_time=0.2):
    '''
    this is a "duplicate" of measure_logger_retries with only one difference
    it uses "lcd fill_calib" instead of "lcd fill"
    '''
    cs2000 = None
    hyperion = None
    pr_series = None
    # dsn = cal_cfg.sn
    instrument = cal_cfg.instrument_type
    # pattern_apk = cal_cfg.pattern_apk
    user_matrix = cal_cfg.user_matrix
    serial_port = cal_cfg.serial_port

    retries = 10
    retries_delay = 0.5
    results = []

    if instrument == InstrumentType.CS2000:
        cs2000 = CS2000(serial_port)
        cs2000.open()
    elif instrument == InstrumentType.Hyperion:
        hyperion = Hyperion(usb_port=serial_port)
        hyperion.open()
    elif instrument == InstrumentType.PRSeries:
        pr_series = PRSeries(serial_port)
        pr_series.open()
    else:
        print('[ERROR] No instrument for connection.')
        return False

    try:

        for i in range(len(patterns)):
            if patterns[i] is None:
                test_data.logger.error(f'{patterns[i]} pattern is None! Skip.')
                continue
            # debug TODO: remove below
            test_data.logger.info(f' start test pattern name:{patterns[i].name}, index:{i}')
            test_data.logger.info(f'R:{patterns[i].R}, G:{patterns[i].G}, B:{patterns[i].B}')
            # debug end

            result = fct_tool.set_calib_background_color(patterns[i].R, patterns[i].G, patterns[i].B)

            if result:
                logging.info('start measuring')
            else:
                # failure occured -> previously causeing empty values -> retest
                while retries >= 0:
                  time.sleep(retries_delay)
                  result = fct_tool.set_calib_background_color(patterns[i].R, patterns[i].G, patterns[i].B)
                  test_data.logger.info(f'{patterns[i]} - FCT failed to switch background. Retries left: {retries}!')
                  retries = retries - 1
                  if result:
                    # retries pass
                    break
                if not result:
                  # retries fail
                  logging.info('[ERROR] fail to switch color pattern')
                  test_data.logger.error(f'{patterns[i]} - FCT failed to switch background! Skip.')
                  continue

            time.sleep(delay_time)

            if instrument == InstrumentType.CS2000:
                if cs2000.measure_data():
                    XYZ = cs2000.read_measured_data(data_mode=DataMode.COLORIMETRIC_DATA,
                                                    colorimetric_data_type=ColorimetricDataType.XYZ)
            elif instrument == InstrumentType.PRSeries:
                if pr_series.measure_data():
                    XYZ = pr_series.read_measured_data(data_code=DataCode.XYZ)
            elif instrument == InstrumentType.Hyperion:
                XYZ = hyperion.measure(sbw=user_matrix)
                if XYZ is None:
                    for j in range(3):
                        XYZ = hyperion.measure(sbw=user_matrix)
                        if not XYZ is None:
                            break
                        else:
                            test_data.logger.error('hyperion measure failed.')
                            print('[ERROR] hyperion measure failed!')
                        time.sleep(0.1)
            else:
                test_data.logger.error('No instrument for measurement.')
                print('No instrument for measurement.')
                return False

            patterns[i].XYZ = np.array(XYZ)

            # debug TODO: remove below
            test = XYZ
            test_data.logger.info(f'pattern {patterns[i].name} XYZ is {test}')
            # debug end

            # add x, y
            sum_xyz = (patterns[i].X + patterns[i].Y + patterns[i].Z)
            if sum_xyz > 0:
                x = patterns[i].X / sum_xyz
                y = patterns[i].Y / sum_xyz
            else:
                x = 0
                y = 0

            # debug TODO: remove below
            test = [patterns[i].name, patterns[i].R, patterns[i].G, patterns[i].B,
                            patterns[i].X, patterns[i].Y, patterns[i].Z, x, y]
            test_data.logger.info(f'test pattern name result:{test}')
            # debug end

            results.append([patterns[i].name, patterns[i].R, patterns[i].G, patterns[i].B,
                            patterns[i].X, patterns[i].Y, patterns[i].Z, x, y])

    except Exception as e:
        test_data.logger.error(f'Exception occured. {e}')
        print(' ********** [ERROR] measurement exception **********')
        print('[ERROR] {}'.format(e))
        print(' ********** [ERROR] measurement exception **********')

    finally:
        if instrument == InstrumentType.CS2000:
            if not cs2000 is None:
                cs2000.close()
        elif instrument == InstrumentType.Hyperion:
            if not hyperion is None:
                hyperion.close()
        elif instrument == InstrumentType.PRSeries:
            if not pr_series is None:
                pr_series.close()
        else:
            test_data.logger.error(f'No instrument to close')
            print('[ERROR] No instrument to close.')

    return results


def measure_flciker(patterns, cal_cfg, fct_tool, delay_time=0.2):

    hyperion = None
    # dsn = cal_cfg.sn
    instrument = cal_cfg.instrument_type
    # pattern_apk = cal_cfg.pattern_apk
    user_matrix = cal_cfg.user_matrix
    serial_port = cal_cfg.serial_port

    results = []

    if instrument == InstrumentType.Hyperion:
        hyperion = Hyperion(usb_port=serial_port)
        hyperion.open()
    else:
        print('[ERROR] No instrument for connection.')
        return False

    for i in range(len(patterns)):

        result = fct_tool.set_background_color(patterns[i].R, patterns[i].G, patterns[i].B)

        if result:
            logging.info('start measuring')
        else:
            logging.info('[ERROR] fail to switch color pattern')
            continue

        time.sleep(delay_time)

        if instrument == InstrumentType.Hyperion:
            flicker = hyperion.measure(sbw=user_matrix, measurement_type=MeasurementType.Flicker,)
        else:
            print('[ERROR] No instrument for measurement.')
            return False

        results.append([patterns[i], flicker])

    if instrument == InstrumentType.Hyperion:
        if not hyperion is None:
            hyperion.close()
    else:
        print('[ERROR] No instrument to close.')

    return results


def measure_bl_currents(bl_currents, cal_cfg, fct_tool, delay_time=0.2):

    cs2000 = None
    hyperion = None
    pr_series = None
    # dsn = cal_cfg.sn
    instrument = cal_cfg.instrument_type
    # pattern_apk = cal_cfg.pattern_apk
    user_matrix = cal_cfg.user_matrix
    serial_port = cal_cfg.serial_port

    results = []

    if instrument == InstrumentType.CS2000:
        cs2000 = CS2000(serial_port)
        cs2000.open()
    elif instrument == InstrumentType.Hyperion:
        hyperion = Hyperion(usb_port=serial_port)
        hyperion.open()
    elif instrument == InstrumentType.PRSeries:
        pr_series = PRSeries(serial_port)
        pr_series.open()
    else:
        print('[ERROR] No instrument for connection.')
        return False

    try:

        result = fct_tool.set_background_color(255, 255, 255)
        if result:
            logging.info('show white pattern pass!')
            time.sleep(0.5)
        else:
            logging.info('[ERROR] show white pattern fail!')
            return False

        for i in range(len(bl_currents)):

            result = fct_tool.set_current(bl_currents[i])
            if result:
                logging.info('start measuring')
            else:
                logging.info('[ERROR] fail to switch bl currents')
                continue

            time.sleep(delay_time)

            if instrument == InstrumentType.CS2000:
                if cs2000.measure_data():
                    XYZ = cs2000.read_measured_data(data_mode=DataMode.COLORIMETRIC_DATA,
                                                    colorimetric_data_type=ColorimetricDataType.XYZ)
            elif instrument == InstrumentType.PRSeries:
                if pr_series.measure_data():
                    XYZ = pr_series.read_measured_data(data_code=DataCode.XYZ)
            elif instrument == InstrumentType.Hyperion:
                XYZ = hyperion.measure(sbw=user_matrix)
                if XYZ is None:
                    for j in range(3):
                        XYZ = hyperion.measure(sbw=user_matrix)
                        if not XYZ is None:
                            break
                        time.sleep(0.1)
            else:
                print('[ERROR] No instrument for measurement.')
                return False

            # add x, y
            sum_xyz = (XYZ[0] + XYZ[1] + XYZ[2])
            if sum_xyz > 0:
                x = XYZ[0] / sum_xyz
                y = XYZ[1] / sum_xyz
            else:
                x = 0
                y = 0
            results.append([bl_currents[i], 255, 255, 255, XYZ[0], XYZ[1], XYZ[2], x, y])

    except Exception as e:
        print(' ********** [ERROR] measurement exception **********')
        print('[ERROR] {}'.format(e))
        print(' ********** [ERROR] measurement exception **********')

    finally:

        if instrument == InstrumentType.CS2000:
            if not cs2000 is None:
                cs2000.close()
        elif instrument == InstrumentType.Hyperion:
            if not hyperion is None:
                hyperion.close()
        elif instrument == InstrumentType.PRSeries:
            if not pr_series is None:
                pr_series.close()
        else:
            print('[ERROR] No instrument to close.')

    return results

def measure_bl_brightness(bl_brightness, cal_cfg, fct_tool, delay_time=0.2):

    cs2000 = None
    hyperion = None
    pr_series = None
    # dsn = cal_cfg.sn
    instrument = cal_cfg.instrument_type
    # pattern_apk = cal_cfg.pattern_apk
    user_matrix = cal_cfg.user_matrix
    serial_port = cal_cfg.serial_port

    results = []

    if instrument == InstrumentType.CS2000:
        cs2000 = CS2000(serial_port)
        cs2000.open()
    elif instrument == InstrumentType.Hyperion:
        hyperion = Hyperion(usb_port=serial_port)
        hyperion.open()
    elif instrument == InstrumentType.PRSeries:
        pr_series = PRSeries(serial_port)
        pr_series.open()
    else:
        print('No instrument for connection.')
        return False

    try:

        result = fct_tool.set_background_color(255, 255, 255)
        if result:
            logging.info('show white pattern pass!')
            time.sleep(0.1)
        else:
            logging.info('[ERROR] show white pattern fail!')
            return False

        for k in bl_brightness:

            result, current = fct_tool.set_brightness(bl_brightness[k])
            if result:
                logging.info('start measuring')
            else:
                logging.info('[ERROR] fail to switch bl brightness')
                continue

            time.sleep(delay_time)

            if instrument == InstrumentType.CS2000:
                if cs2000.measure_data():
                    XYZ = cs2000.read_measured_data(data_mode=DataMode.COLORIMETRIC_DATA,
                                                    colorimetric_data_type=ColorimetricDataType.XYZ)
            elif instrument == InstrumentType.PRSeries:
                if pr_series.measure_data():
                    XYZ = pr_series.read_measured_data(data_code=DataCode.XYZ)
            elif instrument == InstrumentType.Hyperion:
                XYZ = hyperion.measure(sbw=user_matrix)
                if XYZ is None:
                    for i in range(3):
                        XYZ = hyperion.measure(sbw=user_matrix)
                        if not XYZ is None:
                            break
                        time.sleep(0.1)

            else:
                print('No instrument for measurement.')
                return False

            # add x, y
            sum_xyz = (XYZ[0] + XYZ[1] + XYZ[2])
            if sum_xyz > 0:
                x = XYZ[0] / sum_xyz
                y = XYZ[1] / sum_xyz
            else:
                x = 0
                y = 0
            results.append([k, 255, 255, 255, XYZ[0], XYZ[1], XYZ[2], x, y, current])

    except Exception as e:
        print(' ********** [ERROR] measurement exception **********')
        print('[ERROR] {}'.format(e))
        print(' ********** [ERROR] measurement exception **********')

    finally:

        if instrument == InstrumentType.CS2000:
            if not cs2000 is None:
                cs2000.close()
        elif instrument == InstrumentType.Hyperion:
            if not hyperion is None:
                hyperion.close()
        elif instrument == InstrumentType.PRSeries:
            if not pr_series is None:
                pr_series.close()
        else:
            print('[ERROR] No instrument to close.')

    return results


def measure_bl_brightness_logger_retries(bl_brightness, cal_cfg, fct_tool, test_data, delay_time=0.2):
    '''
    investigate retest issue where measurements are sometimes empty
    this method prints info to test_data.logger
    this method deploys 10 tries before return. retries_delay is hard coded to 0.5s
    '''

    cs2000 = None
    hyperion = None
    pr_series = None
    # dsn = cal_cfg.sn
    instrument = cal_cfg.instrument_type
    # pattern_apk = cal_cfg.pattern_apk
    user_matrix = cal_cfg.user_matrix
    serial_port = cal_cfg.serial_port

    retries = 10
    retries_delay = 0.5
    results = []

    if instrument == InstrumentType.CS2000:
        cs2000 = CS2000(serial_port)
        cs2000.open()
    elif instrument == InstrumentType.Hyperion:
        hyperion = Hyperion(usb_port=serial_port)
        hyperion.open()
    elif instrument == InstrumentType.PRSeries:
        pr_series = PRSeries(serial_port)
        pr_series.open()
    else:
        print('No instrument for connection.')
        test_data.logger.error('No instrument for connection.')
        return False

    try:

        result = fct_tool.set_background_color(255, 255, 255)
        if result:
            logging.info('show white pattern pass!')
            time.sleep(0.1)
        else:
            logging.info('[ERROR] show white pattern fail!')
            return False

        for k in bl_brightness:

            result, current = fct_tool.set_brightness(bl_brightness[k])
            if result:
                logging.info('start measuring')
            else:
                # failure occured -> previously causeing empty values -> retest
                while retries >= 0:
                  time.sleep(retries_delay)
                  result, current = fct_tool.set_brightness(bl_brightness[k])
                  test_data.logger.info(f'{k} - FCT failed to set bl brightness. Retries left: {retries}!')
                  retries = retries - 1
                  if result:
                    # retries pass
                    break
                if not result:
                  # retries fail
                  logging.info('[ERROR] fail to switch bl brightness')
                  test_data.logger.error(f'{k} - FCT failed to set bl brightness! Skip.')
                  continue

            time.sleep(delay_time)

            if instrument == InstrumentType.CS2000:
                if cs2000.measure_data():
                    XYZ = cs2000.read_measured_data(data_mode=DataMode.COLORIMETRIC_DATA,
                                                    colorimetric_data_type=ColorimetricDataType.XYZ)
            elif instrument == InstrumentType.PRSeries:
                if pr_series.measure_data():
                    XYZ = pr_series.read_measured_data(data_code=DataCode.XYZ)
            elif instrument == InstrumentType.Hyperion:
                XYZ = hyperion.measure(sbw=user_matrix)
                if XYZ is None:
                    for i in range(3):
                        XYZ = hyperion.measure(sbw=user_matrix)
                        if not XYZ is None:
                            break
                        time.sleep(0.1)

            else:
                test_data.logger.error('No instrument for measurement.')
                print('No instrument for measurement.')
                return False

            # debug TODO: remove below
            test = XYZ
            test_data.logger.info(f'BL {k} XYZ is {test}')
            # debug end

            # add x, y
            sum_xyz = (XYZ[0] + XYZ[1] + XYZ[2])
            if sum_xyz > 0:
                x = XYZ[0] / sum_xyz
                y = XYZ[1] / sum_xyz
            else:
                x = 0
                y = 0
            results.append([k, 255, 255, 255, XYZ[0], XYZ[1], XYZ[2], x, y, current])

            # additional current measurement per x-functional requests
            fBool, current = fct_tool.calc_current_ma(test_data)
            test_data.logger.info(f'measure backlight LED drive current for {k} nits, current: {current}')
            test_data.measurements[f'LED_current_{k}_nits'] = float(current)

    except Exception as e:
        test_data.logger.error(f'Exception occured. {e}')
        print(' ********** [ERROR] measurement exception **********')
        print('[ERROR] {}'.format(e))
        print(' ********** [ERROR] measurement exception **********')

    finally:

        if instrument == InstrumentType.CS2000:
            if not cs2000 is None:
                cs2000.close()
        elif instrument == InstrumentType.Hyperion:
            if not hyperion is None:
                hyperion.close()
        elif instrument == InstrumentType.PRSeries:
            if not pr_series is None:
                pr_series.close()
        else:
            test_data.logger.error(f'No instrument to close')
            print('[ERROR] No instrument to close.')

    return results


def main():

    pattern = Pattern(0, 0, 0, 64, 64, 64)
    patterns = [pattern, ]
    cal_config = CalibrationConfig()
    # octopus = Octopus()
    # connected = octopus.init()
    #
    # if connected:
    #     results = measure(100, patterns, cal_config, octopus)
    #     for result in results:
    #         print(result)


if __name__ == '__main__':
    main()
