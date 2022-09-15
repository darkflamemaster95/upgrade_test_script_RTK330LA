import sys
import time
import os
import signal
import struct
import threading

try:
    from aceinna.core.driver import (Driver, DriverEvents)
    from aceinna.models.args import WebserverArgs
    from aceinna.framework.utils import (helper)
    from aceinna.framework.decorator import handle_application_exception
    from aceinna.devices.rtkl.uart_provider import Provider as UartProvider
    from aceinna.framework.constants import INTERFACES
except:  # pylint: disable=bare-except
    print('load package from local')
    sys.path.append('./src')
    from aceinna.core.driver import (Driver, DriverEvents)
    from aceinna.models.args import WebserverArgs
    from aceinna.framework.utils import (helper)
    from aceinna.framework.decorator import handle_application_exception
    from aceinna.devices.rtkl.uart_provider import Provider as UartProvider
    from aceinna.devices.device_manager import DeviceManager
    from aceinna.framework.constants import INTERFACES

global loop_upgrade_cnt
global fw_list
global mistake_times
global turns
global test_log
global fw_path_upgrade
global fw_path_rollback
loop_upgrade_cnt = 0
mistake_times = 0
turns = 0
test_log = open(f'test_log_{time.strftime("%H%M%S")}.txt', 'a+')

driver = Driver(WebserverArgs(
    interface=INTERFACES.UART
))

def get_info():
    logf = open('./compare.txt')
    app_info = logf.read()
    logf.close()

    app_ver = app_info.split(' ')[2]
    return app_ver

def handle_discovered(device_provider):
    global turns
    # turns = input('Input turns:')
    do_upgrade()

def get_firmware():
    global fw_path_1
    global fw_path_2
    global fw_path_upgrade
    global fw_path_rollback
    global fw_flag

    fw_path_upgrade = fw_path_1
    fw_path_rollback = fw_path_2

    fw_list = [fw_path_upgrade, fw_path_rollback]
    app_ver = get_info()
    # print(app_ver)
    if app_ver == fw_flag:
        fw_file = fw_list[0]
    else:
        fw_file = fw_list[1]
    return fw_file
    # return fw_list[cnt % 2]

def do_upgrade():
    global loop_upgrade_cnt
    global turns

    if loop_upgrade_cnt == int(turns):
        kill_app()
        return
    driver.execute('upgrade_framework', get_firmware())

def handle_upgrade_finished():
    global loop_upgrade_cnt
    global test_log
    loop_upgrade_cnt += 1

    print(f'Turn {loop_upgrade_cnt} finished')
    test_log.write(f'Turn {loop_upgrade_cnt} upgrade is Successed\n\n')
    test_log.flush()
    os.fsync(test_log)

    do_upgrade()

def handle_upgrade_fail(code, message):
    global loop_upgrade_cnt
    global test_log
    loop_upgrade_cnt += 1

    print(f'Turn {loop_upgrade_cnt} failed')
    print(f'Fail Info: {code} - {message}')
    test_log.write(f'Turn {loop_upgrade_cnt} upgrade is Failed\n\n')
    test_log.flush()
    os.fsync(test_log)

    do_upgrade()

def kill_app():
    '''Kill main thread
    '''
    os.kill(os.getpid(), signal.SIGTERM)
    sys.exit()

@handle_application_exception
def simple_start():
    driver.on(DriverEvents.Discovered, handle_discovered)
    driver.on(DriverEvents.UpgradeFinished, handle_upgrade_finished)
    driver.on(DriverEvents.UpgradeFail, handle_upgrade_fail)
    driver.detect()

if __name__ == '__main__':
    turns = int(sys.argv[1])
    fw_path_1 = input('please input the path of upgrade firmware:\n')
    fw_path_2 = input('please input the path of rollback firmware:\n')
    a_pos = fw_path_1.find('v24')
    b_pos = fw_path_1.find('.bin')
    fw_flag = fw_path_1[a_pos:b_pos]

    simple_start()

    while True:
        signal.signal(signal.SIGINT, kill_app)
