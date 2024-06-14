import math
import time

"""
Units
Wavelength:nm
Angle:degree, pulse {(grating)1 pulse = 0.0018 degree, (next_filter)1 pulse = 0.36 degree}
"""
class ShimadzuSpectrometer():
    def __init__(self, controller):
        self.__controller__ = controller
        self.__type__ = 'UV'  # S, UV or IR
        self.__C1__ = 2882
        self.__C2__ = 0.0008
        """
        C1 and C2 are determined by product.
        """
        self.initialize()

    def initialize(self):
        """
        Initializing grating
        1.Return to mechanical origin.
        2.Move 'C1 - 1000' pulses.
        3.Set electrical origin.

        Initializing filter
        1.Move in a negative direction until a limit sensor senses.
        2.Move 10 pulses.
        3.Set electrical origin.
        """
        self.__controller__.returnToMechanicalOrigin(True, False)
        time.sleep(10.0)
        self.__controller__.move(self.__C1__-1000, 0)
        time.sleep(1.0)
        self.__controller__.initializeOrigin(True, False)
        time.sleep(0.1)
        self.__current_wavelength__ = 0
        self.__current_pulse__ = 0

        self.__controller__.move(0, -3000)
        time.sleep(3.0)
        self.__controller__.move(0, 10)
        time.sleep(1.0)
        self.__controller__.initializeOrigin(False, True)
        self.__current_filter__ = 1
        """
        If '         0,         0,K,K,R' is displayed, there are no issues.
        """
        return self.__controller__.getStatus()

    def changeWavelength(self, next_wavelength, next_filter=1, interlock=True):
        if self.__type__ == 'S' or self.__type__ == 'UV':
            if not (0 <= next_wavelength <= 1300):
                raise ValueError('Wavelength must be between 0 and 1300.')
        elif self.__type__ == 'IR':
            if not (0 <= next_wavelength <= 2600):
                raise ValueError('Wavelength must be between 0 and 2600.')
        if not next_filter in [1, 2, 3, 4, 5, 6]:
            raise ValueError('Next_filter must be 1, 2, 3, 4, 5 or 6.')

        theta = math.asin(-0.0006194615*(1+self.__C2__)*next_wavelength) / math.pi * 180
        next_pulse = round(-1 * theta / 0.0018)
        N_pulse = abs(self.__current_pulse__ - next_pulse)
        
        command = 'M:W'

        if next_wavelength >= self.__current_wavelength__:
            command += '+P%d' % N_pulse
        else:
            command += '-P%d' % N_pulse
        
        self.__current_pulse__ = next_pulse
        self.__current_wavelength__ = next_wavelength

        if interlock == True:
            if self.__type__ == 'S' or self.__type__ == 'UV':
                if 0 <= next_wavelength < 400:
                    next_filter = 1
                elif 400 <= next_wavelength < 600:
                    next_filter = 2
                elif 600 <= next_wavelength < 900:
                    next_filter = 3
                else:
                    next_filter = 4
            elif self.__type__ == 'IR':
                if 0 <= next_wavelength < 700:
                    next_filter = 1
                elif 700 <= next_wavelength < 900:
                    next_filter = 2
                elif 900 <= next_wavelength < 1200:
                    next_filter = 3
                elif 1200 <= next_wavelength < 1700:
                    next_filter = 4
                elif 1700 <= next_wavelength < 2600:
                    next_filter = 5
                else:
                    next_filter = 6
        
        N_filter = abs(self.__current_filter__ - next_filter)
        N_pulse = N_filter * 167
        
        if next_filter >= self.__current_filter__:
            command += '+P%d' % N_pulse
        else:
            command += '-P%d' % N_pulse
        
        self.__current_filter__ = next_filter

        self.__controller__.write(command)
        self.__controller__.go()
        return

    def measureSpectrum(self, start, end, pitch, interval, filter=1, interlock=True):
        if not interval >= 1.1:
            raise ValueError('Interval must be 1.1 or more.')
        """
        If you input a long pitch, maybe interval requires more than 1.1.
        """
        if not filter in [1, 2, 3, 4, 5, 6]:
            raise ValueError('Filter must be 1, 2, 3, 4, 5 or 6.')
        
        self.change_wavelength(start, filter, interlock)
        time.sleep(3.0)
        wavelength = start

        while wavelength <= end:
            print(wavelength)
            self.change_wavelength(wavelength, filter, interlock)
            wavelength += pitch
            time.sleep(interval)
    
    def getStatus(self):
        output = self.__controller__.getStatus()
        current_pulse_of_grating = int(output[0:10])
        current_pulse_of_filter = int(output[11:21])

        theta_of_grating = current_pulse_of_grating * (-1) * 0.0018
        current_wavelength = round(math.sin(theta_of_grating/180*math.pi) / (-0.0006194615) / (1+self.__C2__))
        current_filter = round(current_pulse_of_filter / 500 * 3)

        return self.__controller__.getStatus(), f'wavelength={current_wavelength}nm,filter=No.{current_filter}'