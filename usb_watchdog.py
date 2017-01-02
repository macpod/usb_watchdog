#!/usr/bin/env python

# usb_watchdog.py: Python script to configure/pet the Macpod LLC USB Watchdog dongle
# 
# Website: http://macpod.net
# Copyright Jeffrey Nelson, 2016
# Version: 1.0.0
# License: GPL V3


from __future__ import print_function
import hid
import re
import argparse
import time


def check_serialnumber(value):
    if re.match('^[\w-]+$', value) is None:
         raise argparse.ArgumentTypeError('%s must be alphanumeric' % value)
    return value

def check_timeout(value):
    ivalue = int(value)
    if ivalue == 0 or ivalue > 2**16-1:
         raise argparse.ArgumentTypeError('%s must be between 1 and 2^16-1' % value)
    return ivalue

def check_frequency(value):
    ivalue = int(value)
    if ivalue < 42 or ivalue > 2**8-1:
         raise argparse.ArgumentTypeError('%s must be between 42 and 2^8-1' % value)
    return ivalue


global_parser = argparse.ArgumentParser(add_help=False)
global_parser.add_argument('--serial-number', type=check_serialnumber, 
        help='Interacts with the designated USB Watchdog. '
            'If not provided the first USB Watchdog found will be used.')
global_parser.add_argument('--verbose', action='store_true', default=False, 
        help='Reports additional information')


settings_parser = argparse.ArgumentParser(add_help=False)
settings_parser.add_argument('--nonvolatile-timeout', type=check_timeout, 
        help='Sets a timeout period maintained across USB Watchdog reboots. '
            'This does not take effect until the next USB Watchdog reboot.')
settings_parser.add_argument('--timeout', type=check_timeout, 
        help='Sets a timeout period that is in effect until the USB Watchdog reboots.')

nonvolatile_pinglight_parser = settings_parser.add_mutually_exclusive_group(required=False)
nonvolatile_pinglight_parser.add_argument('--nonvolatile-pinglight', 
        dest='nonvolatile_pinglight', action='store_true', 
        help='Enables the ping light across USB Watchdog reboots. '
            'This does not take effect until the next USB Watchdog reboot.')
nonvolatile_pinglight_parser.add_argument('--no-nonvolatile-pinglight', 
        dest='nonvolatile_pinglight', action='store_false', 
        help='Disables the ping light across USB Watchdog reboots. '
            'This does not take effect until the next USB Watchdog reboot.')
nonvolatile_pinglight_parser.set_defaults(nonvolatile_pinglight=None)

nonvolatile_buzzer_parser = settings_parser.add_mutually_exclusive_group(required=False)
nonvolatile_buzzer_parser.add_argument('--nonvolatile-buzzer',
        dest='nonvolatile_buzzer', action='store_true', 
        help='Enables the buzzer across USB Watchdog reboots. '
            'This does not take effect until the next USB Watchdog reboot.')
nonvolatile_buzzer_parser.add_argument('--no-nonvolatile-buzzer',
        dest='nonvolatile_buzzer', action='store_false', 
        help='Disable the buzzer across USB Watchdog reboots. '
            'This does not take effect until the next USB Watchdog reboot.')
nonvolatile_buzzer_parser.set_defaults(nonvolatile_buzzer=None)

pinglight_parser = settings_parser.add_mutually_exclusive_group(required=False)
pinglight_parser.add_argument('--pinglight', dest='pinglight', action='store_true', 
        help='Enables the ping light until the USB Watchdog reboots')
pinglight_parser.add_argument('--no-pinglight', dest='pinglight', action='store_false', 
        help='Disables the ping light until the USB Watchdog reboots')
pinglight_parser.set_defaults(pinglight=None)

buzzer_parser = settings_parser.add_mutually_exclusive_group(required=False)
buzzer_parser.add_argument('--buzzer', dest='buzzer', action='store_true', 
        help='Enables the buzzer until the USB Watchdog reboots')
buzzer_parser.add_argument('--no-buzzer', dest='buzzer', action='store_false', 
        help='Disables the buzzer until the USB Watchdog reboots')
buzzer_parser.set_defaults(buzzer=None)

settings_parser.add_argument('--nonvolatile-buzzer-frequency', type=check_frequency, 
        help='Sets the buzzer frequency maintained across USB Watchdog reboots. '
            'This does not take effect until the next USB Watchdog reboot. '
            'Accepts values in the range [42-255]')
settings_parser.add_argument('--buzzer-frequency', type=check_frequency, 
        help='Sets the buzzer frequency until the USB Watchdog reboots. '
            'Accepts values in the range [42-255]')
settings_parser.add_argument('--clear-reboot-indicator', action='store_true', 
        help='Clears the reboot indicator bit of the USB Watchdog')


pet_parser = argparse.ArgumentParser(add_help=False)
pet_parser.add_argument('--detect-reboot', action='store_true', default=False, 
        help='Exits program with status code of 2 if USB Watchdog is known to have reboot. The USB Watchdog will not be pet.')
pet_parser.add_argument('--detect-timeout', action='store_true', default=False, 
        help='Exits program with status code of 3 if the USB Watchdog is known to have timed out. i'
            'The USB Watchdog will not be pet.')

parser = argparse.ArgumentParser(description='Program to set and pet a USB Watchdog from Macpod LLC.', version='1.0.0', 
        epilog='Copyright Jeffrey Nelson, 2016. Licensed under GPL V3')
subparsers = parser.add_subparsers(dest='action')

reboot_detect_parser = subparsers.add_parser('rebooted', 
        parents=[global_parser], 
        help='Identifies if the USB Watchdog is known to have reboot.',
        epilog='Returns 0 on success, 1 if a error occurs, or 2 if the unit has reboot')

triggered_parser = subparsers.add_parser('timed-out', 
        parents=[global_parser], 
        help='Identifies if the USB Watchdog has timed out.',
        epilog='Returns 0 on success, 1 if a error occurs, or 3 if the unit has timed out')

configure_parser = subparsers.add_parser('configure', 
        parents=[global_parser, settings_parser], 
        help='Configures the USB Watchdog and exits',
        epilog='Returns 0 on success or 1 if an error occurs')

oneshot_parser = subparsers.add_parser('oneshot', 
        parents=[global_parser, settings_parser, pet_parser],
        help='Pets the Watchdog once and exits', 
        epilog='Returns 0 on success or 1 if an error occurs')

parser_continuous = subparsers.add_parser('continuous', 
        parents=[global_parser, settings_parser, pet_parser],
        help='Pets the USB Watchdog continuously',
        epilog='Returns 0 on success or 1 if an error occurs')
parser_continuous.add_argument('--pet-interval', type=check_timeout, default=1, 
        help='Set time in seconds between when the USB Watchdog is \'pet\'. '
        'This should be well below the Watchdog timeout threshold.')


args = parser.parse_args()
	
###############################################################################

class USBWatchDog(object):
    FR_VERSION = 0x1
    FR_VERSION_LEN = 2

    FR_SERIAL_NUMBER = 0x2
    FR_SERIAL_NUMBER_LEN = 20
    SERIAL_NUMBER_LEN = 20
    
    FR_NONVOLATILE_TIMEOUT = 0x3
    FR_NONVOLATILE_TIMEOUT_LEN = 2

    FR_VOLATILE_TIMEOUT = 0x4
    FR_VOLATILE_TIMEOUT_LEN = 2

    FR_NONVOLATILE_PINGLIGHT_BUZZER = 0x5 
    FR_NONVOLATILE_PINGLIGHT_BUZZER_LEN = 1
    FR_VOLATILE_PINGLIGHT_BUZZER = 0x6
    FR_VOLATILE_PINGLIGHT_BUZZER_LEN = 1
    PINGLIGHT_BIT = 0x1
    BUZZER_BIT = 0x2

    FR_NONVOLATILE_BUZZER_FREQUENCY = 0x7
    FR_NONVOLATILE_BUZZER_FREQUENCY_LEN = 1

    FR_VOLATILE_BUZZER_FREQUENCY = 0x8
    FR_VOLATILE_BUZZER_FREQUENCY_LEN = 1

    FR_REBOOT_INDICATOR = 0x9
    FR_REBOOT_INDICATOR_LEN = 1

    IN_WATCHDOG_STATUS = 0x1
    IN_WATCHDOG_STATUS_LEN = 3
    WATCHDOG_IN_TIMEOUT_BIT = 0x1
    WATCHDOG_IN_REBOOT_BIT = 0x2

    OUT_PET_WATCHDOG = 0x1
    OUT_PET_WATCHDOG_LEN = 1
    WATCHDOG_OUT_TIMEOUT_BIT = 0x1
    WATCHDOG_OUT_CLEARALARM_BIT = 0x2

    def __check_open(self):
        if self._h is None:
            raise IOError('USB Watchdog not open')  

    def __to_uint16(self, array):
        return array[1]*256 + array[0]

    def __from_uint16(self, val):
        if val > 2**16 - 1:
            raise ValueError('Timeout value is too large')
        return [val % 256, val // 256]

    def __get_feature_report(self, fr_id, length):
        self.__check_open()
        array = self._h.get_feature_report(fr_id, length+1)  # report id, max len
        # hidapi's windows/hid.c seems to append an extra byte at least under Windows 10 (bug?)
        # We need to strip this off.
        if len(array) < length+1:
            raise ValueError('received unexpected value', array)
        return array[1:length+1]

    def __send_feature_report(self, array):
        self.__check_open()
        length = self._h.send_feature_report(array)
        if len(array) != length:
            raise IOError('data send failed')

    def __read_input(self, length, timeout):
        self.__check_open()
        array = self._h.read(length, timeout)  # report id, max len
        if len(array) != length:
            raise ValueError('received unexpected value')
        return array

    def __get_nonvolatile_lights_buzzer(self):
        array = self.__get_feature_report(self.FR_NONVOLATILE_PINGLIGHT_BUZZER, self.FR_NONVOLATILE_PINGLIGHT_BUZZER_LEN)
        return array[0]

    def __set_nonvolatile_pinglight_buzzer(self, pinglight=None, buzzer=None):
        val = self.__get_nonvolatile_lights_buzzer()
        newval = 0

        if pinglight is None:
            newval |= val & self.PINGLIGHT_BIT
        elif pinglight == True:
            newval |= self.PINGLIGHT_BIT

        if buzzer is None:
            newval |= val & self.BUZZER_BIT
        elif buzzer is True:
            newval |= self.BUZZER_BIT

        self.__send_feature_report([self.FR_NONVOLATILE_PINGLIGHT_BUZZER, newval])

    def __get_volatile_lights_buzzer(self):
        array = self.__get_feature_report(self.FR_VOLATILE_PINGLIGHT_BUZZER, self.FR_VOLATILE_PINGLIGHT_BUZZER_LEN)
        return array[0]

    def __set_volatile_pinglight_buzzer(self, pinglight=None, buzzer=None):
        val = self.__get_volatile_lights_buzzer()
        newval = 0

        if pinglight is None:
            newval |= val & self.PINGLIGHT_BIT
        elif pinglight is True:
            newval |= self.PINGLIGHT_BIT

        if buzzer is None:
            newval |= val & self.BUZZER_BIT
        elif buzzer is True:
            newval |= self.BUZZER_BIT

        self.__send_feature_report([self.FR_VOLATILE_PINGLIGHT_BUZZER, newval])


    def __init__(self, serial_number=None):
        self._h = hid.device()
        self._h.open(0x16D0, 0x0776, serial_number)
        
    def close(self):
        self.__check_open()
        self._h.close()
        self._h = None

    def get_version(self):
        array = self.__get_feature_report(self.FR_VERSION, self.FR_VERSION_LEN)
        return array[0], array[1]
    
    def get_serial_number(self):
        array = self.__get_feature_report(self.FR_SERIAL_NUMBER, self.FR_SERIAL_NUMBER_LEN)
        return ''.join(map(chr, array[0:]))

    def set_serial_number(self, string):
        if self.get_serial_number() != '00000000000000000000':
            raise ValueError('Serial number is already set')
        if re.match('^[\w-]+$', string) is None:
            raise ValueError('Serial number must be alphanumeric')
        if len(string) != self.SERIAL_NUMBER_LEN:
            raise ValueError('Serial number must be ', self.SERIAL_NUMBER_LEN, ' characters long')
        self.__send_feature_report([self.FR_SERIAL_NUMBER] + [ord(i) for i in string])

    def get_nonvolatile_timeout(self):
        array = self.__get_feature_report(self.FR_NONVOLATILE_TIMEOUT, self.FR_NONVOLATILE_TIMEOUT_LEN)
        return self.__to_uint16(array[0:])

    def set_nonvolatile_timeout(self, val):
        self.__send_feature_report([self.FR_NONVOLATILE_TIMEOUT] + self.__from_uint16(val))

    def get_volatile_timeout(self):
        array = self.__get_feature_report(self.FR_VOLATILE_TIMEOUT, self.FR_VOLATILE_TIMEOUT_LEN)
        return self.__to_uint16(array[0:])

    def set_volatile_timeout(self, val):
        self.__send_feature_report([self.FR_VOLATILE_TIMEOUT] + self.__from_uint16(val))

    def get_nonvolatile_pinglight(self):
        val = self.__get_nonvolatile_lights_buzzer()
        return bool(val & self.PINGLIGHT_BIT)

    def set_nonvolatile_pinglight(self, val):
        self.__set_nonvolatile_pinglight_buzzer(pinglight = val)

    def get_nonvolatile_buzzer(self):
        val = self.__get_nonvolatile_lights_buzzer()
        return bool(val & self.BUZZER_BIT)

    def set_nonvolatile_buzzer(self, val):
        self.__set_nonvolatile_pinglight_buzzer(buzzer = val)

    def get_volatile_pinglight(self):
        val = self.__get_volatile_lights_buzzer()
        return bool(val & self.PINGLIGHT_BIT)

    def set_volatile_pinglight(self, val):
        self.__set_volatile_pinglight_buzzer(pinglight = val)

    def get_volatile_buzzer(self):
        val = self.__get_volatile_lights_buzzer()
        return bool(val & self.BUZZER_BIT)

    def set_volatile_buzzer(self, val):
        self.__set_volatile_pinglight_buzzer(buzzer = val)

    def get_nonvolatile_buzzer_frequency(self):
        array = self.__get_feature_report(self.FR_NONVOLATILE_BUZZER_FREQUENCY, self.FR_NONVOLATILE_BUZZER_FREQUENCY_LEN)
        return array[0]

    def set_nonvolatile_buzzer_frequency(self, val):
        if val > 2**8 - 1:
            raise ValueError('Frequency value is too large')
        self.__send_feature_report([self.FR_NONVOLATILE_BUZZER_FREQUENCY] + [val])

    def get_volatile_buzzer_frequency(self):
        array = self.__get_feature_report(self.FR_VOLATILE_BUZZER_FREQUENCY, self.FR_VOLATILE_BUZZER_FREQUENCY_LEN)
        return array[0]

    def set_volatile_buzzer_frequency(self, val):
        if val > 2**8 - 1:
            raise ValueError('Frequency value is too large')
        self.__send_feature_report([self.FR_VOLATILE_BUZZER_FREQUENCY] + [val])

    def get_reboot_indicator(self):
        array = self.__get_feature_report(self.FR_REBOOT_INDICATOR, self.FR_REBOOT_INDICATOR_LEN)
        return bool(array[0])

    def set_reboot_indicator(self):
        self.__send_feature_report([self.FR_REBOOT_INDICATOR, 0x1])

    def get_status(self, timeout=2000):
        array = self.__read_input(self.IN_WATCHDOG_STATUS_LEN+1, timeout)
        array = self.__read_input(self.IN_WATCHDOG_STATUS_LEN+1, timeout) # Read twice to flush out old sample
        triggered = bool(array[1] & self.WATCHDOG_IN_TIMEOUT_BIT)
        reboot_indicator = bool(array[1] & self.WATCHDOG_IN_REBOOT_BIT)
        counter = self.__to_uint16(array[2:])
        return triggered, reboot_indicator, counter

    def pet(self, clear_alarm=True):
        self.__check_open()
        val = self.WATCHDOG_OUT_TIMEOUT_BIT
        if clear_alarm:
            val |= self.WATCHDOG_OUT_CLEARALARM_BIT
        length = self._h.write([self.OUT_PET_WATCHDOG, val])
        if self.OUT_PET_WATCHDOG_LEN+1 != length:
            raise ValueError('encountered unexpected error')

###############################################################################

class USBWatchDogError(Exception):
    def __init__(self, error_number):
        self.error_number = error_number 


def vprint(*print_args, **print_kwargs):
    if args.verbose:
        print(*print_args, **print_kwargs)


def general_configure(watchdog):
    try:
        if args.nonvolatile_timeout is not None:
            vprint('Setting nonvolatile timeout to', args.nonvolatile_timeout, 'seconds')
            watchdog.set_nonvolatile_timeout(args.nonvolatile_timeout)

        if args.timeout is not None:
            vprint('Setting volatile timeout to', args.timeout, 'seconds')
            watchdog.set_volatile_timeout(args.timeout)


        if args.nonvolatile_pinglight is not None:
            vprint('Setting nonvolatile ping light to', args.nonvolatile_pinglight)
            watchdog.set_nonvolatile_pinglight(args.nonvolatile_pinglight)

        if args.pinglight is not None:
            vprint('Setting volatile ping light to', args.pinglight)
            watchdog.set_volatile_pinglight(args.pinglight)


        if args.nonvolatile_buzzer is not None:
            vprint('Setting nonvolatile buzzer to', args.nonvolatile_buzzer)
            watchdog.set_nonvolatile_buzzer(args.nonvolatile_buzzer)

        if args.buzzer is not None:
            vprint('Setting volatile buzzer to', args.buzzer)
            watchdog.set_volatile_buzzer(args.buzzer)


        if args.nonvolatile_buzzer_frequency is not None:
            vprint('Setting nonvolatile buzzer frequency to', args.nonvolatile_buzzer_frequency)
            watchdog.set_nonvolatile_buzzer_frequency(args.nonvolatile_buzzer_frequency)

        if args.buzzer_frequency is not None:
            vprint('Setting volatile buzzer frequency to', args.buzzer_frequency)
            watchdog.set_volatile_buzzer_frequency(args.buzzer_frequency)


        if args.clear_reboot_indicator:
            vprint('Clearing reboot indicator')
            watchdog.set_reboot_indicator()
    except (IOError, ValueError), e:
        print('Error configuring USB Watchdog:', e)
        raise USBWatchDogError(1)


def print_settings(watchdog):
    try:
        vprint('~Configuration info~')
        vprint('Serial number:', watchdog.get_serial_number())
        vprint('Nonvolatile timeout:', watchdog.get_nonvolatile_timeout(), 'seconds')
        vprint('Volatile timeout:', watchdog.get_volatile_timeout(), 'seconds')
        vprint('Nonvolatile ping light:', watchdog.get_nonvolatile_pinglight())
        vprint('Nonvolatile buzzer:', watchdog.get_nonvolatile_buzzer())
        vprint('Volatile ping light:', watchdog.get_volatile_pinglight())
        vprint('Volatile buzzer:', watchdog.get_volatile_buzzer())
        vprint('Nonvolatile buzzer frequency:', watchdog.get_nonvolatile_buzzer_frequency())
        vprint('Volatile buzzer frequency:', watchdog.get_volatile_buzzer_frequency())
        vprint('Reboot indicator:', watchdog.get_reboot_indicator())
        vprint('~~~~~~~~~~~~~~~~~~~~')
    except (IOError, ValueError), e:
        print('Error obtaining USB Watchdog settings:', e)
        raise USBWatchDogError(1)


def handle_petting(watchdog):
    try:
        triggered, reboot_indicator, counter = watchdog.get_status()
    except (IOError, ValueError), e:
        print('Error objtaining USB Watchdog status:', e)
        raise USBWatchDogError(1)

    if reboot_indicator and args.detect_reboot:
        print('USB Watchdog reboot identified!')
        raise USBWatchDogError(2)

    if triggered and args.detect_timeout:
        print('USB Watchdog timeout identified!')
        raise USBWatchDogError(3)

    try:
        vprint('Petting')
        watchdog.pet()
    except (IOError, ValueError), e:
        print('Error petting USB Watchdog:', e)
        raise USBWatchDogError(1)


def handle_configure_action(watchdog):
    general_configure(watchdog)
    print_settings(watchdog)


def handle_oneshot_action(watchdog):
    general_configure(watchdog)
    print_settings(watchdog)
    handle_petting(watchdog)

def handle_continuous_action(watchdog):
    general_configure(watchdog)
    print_settings(watchdog)

    vprint('Pet interval:', args.pet_interval)
        
    while 1:
        handle_petting(watchdog)
        time.sleep(args.pet_interval)


def handle_rebooted_action(watchdog):
    try:
        triggered, reboot_indicator, counter = watchdog.get_status()
    except (IOError, ValueError), e:
        print('Error getting USB Watchdog status:', e)
        raise USBWatchDogError(1)

    if reboot_indicator:
        print('USB Watchdog reboot identified!')
        raise USBWatchDogError(2)


def handle_timed_out_action(watchdog):
    try:
        triggered, reboot_indicator, counter = watchdog.get_status()
    except (IOError, ValueError), e:
        print('Error getting USB Watchdog status:', e)
        raise USBWatchDogError(1)

    if triggered:
        print('USB Watchdog timeout identified!')
        raise USBWatchDogError(3)


def main():
    watchdog = None
    try:
        try:
            try:
                watchdog = USBWatchDog(args.serial_number)
            except (IOError, ValueError), e:
                print('Error opening USB Watchdog:', e)
                exit(1)

            if args.action == 'configure':
                handle_configure_action(watchdog)
            elif args.action == 'oneshot': 
                handle_oneshot_action(watchdog)
            elif args.action == 'continuous':
                handle_continuous_action(watchdog)
            elif args.action == 'rebooted':
                handle_rebooted_action(watchdog)
            elif args.action == 'timed-out': 
                handle_timed_out_action(watchdog)

        except KeyboardInterrupt:        
            raise USBWatchDogError(1)
    except USBWatchDogError, e:
        error_number = e.error_number
    else:
        error_number = 0
    finally:
        try:
            if watchdog is not None:
                #TODO see if this does anything
                watchdog.close()
        except (IOError, ValueError), e:
            print('Error closing USB Watchdog:', e)
            exit(1)


    exit(error_number)

if __name__ == '__main__':
    main()

