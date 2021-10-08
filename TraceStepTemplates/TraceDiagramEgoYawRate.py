import textwrap

import os
import csv
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

if any(name not in globals() for name
        in ('NumpyBasedTraceStep', 'SignalDefinition', 'ParameterDefinition')):
    from NumpyBasedTraceStep import NumpyBasedTraceStep, SignalDefinition, ParameterDefinition


class TraceDiagramEgoYawRate(NumpyBasedTraceStep):
    """
    This is an implementation of NumpyBasedTraceStep.

    Use the interface as reference for available methods. Abstract methods have to be implemented.
    Other methods like GetDescription() are optionally overwritten. There are utility functions
    like CalculateRanges(), FitToAxis() that can be used in your code.
    """

    @staticmethod
    def GetInterfaceRevision():
        """
        Returns the interface revision of the trace step template.

        :note: This method is auto-generated for new implementations of NumpyBasedTraceStep. So do
               not delete or modify this method!

        :rtype: int
        """
        return 1

    @classmethod
    def GetDescription(cls):
        """
        Returns the description of the trace step.

        :rtype: str
        """
        return textwrap.dedent('''
            This trace step includes a diagram of the Ego yaw rate in the report.
            ''').strip()

    @classmethod
    def GetSignals(cls):
        """
        Returns the incoming and outgoing signals of the trace step.

        :rtype: list[SignalDefinition]
        """
        return []

    @classmethod
    def GetParameters(cls):
        """
        Returns the input and return parameters of the trace step.

        :rtype: list[ParameterDefinition]
        """
        return [
            ParameterDefinition('csvList', 'IN', description='list of all csv trace files'),
            ParameterDefinition('logoPath', 'IN', description='path to the logo image file to be included as watermark (optional)'),
            ]

    @classmethod
    def GetTimeAxisDefinition(cls):
        """
        Returns how the common time axis is determined. Only the logical operators **and** and
        **or** as well as references to the time axes of the signals by using the signal name are
        permitted. The use of brackets is allowed.

        :note: If a signal is not defined on the common time axis, its value is determined
               according to its interpolation rule.

        :return: Convention for building the common time axis (e.g. **'Sig1 or Sig2'**). If an
                 empty string is returned, all time axes are merged into one common time axis.
                 This corresponds to an OR concatenation of the individual time axes.
        :rtype: str
        """
        # e.g. 'Sig1 or Sig2' - timestamps either from Sig1 or Sig2 (default behavior)
        # e.g. 'Sig1 and Sig2' - only timestamps common to both Sig1 and Sig2
        return ''

    def Check(self, parameters):
        """
        Is called initially before trace analysis execution and should check the parameterization.
        In case of error, raise a TypeError or ValueError.

        :param parameters: Dictionary of parameter values.
        :type parameters: dict[str, object]
        :raise TypeError: Invalid type of a parameter.
        :raise ValueError: Invalid value of a parameter.
        """

    def Process(self, parameters, report, timeAxis, ranges, signals):
        """
        Method for executing the trace step template. Calculations can be performed based on
        the given signal values and their results can be stored in outgoing signals. Evaluation
        results and return parameters can be set.

        :note: It is recommended to evaluate over the given trigger ranges and set the result for
               each trigger range. The overall result will be automatically determined.

               It is possible to manually set the overall result using the :class:`Report` object;
               the automatic mechanism will be deactivated if used.

               Detailed spots are also reported on trigger ranges.
        :note: Access to values: All signal values within a trigger range can be accessed
               by its :class:`TriggerRange` object. Alternatively, all values of a signal can be
               accessed by the :class:`Signal` object.
        :note: To store calculated values in an outgoing signal the :class:`Signal` object is used:
               Signal.Emit(timestamps, values)
        :param parameters: Dictionary of parameter values.
        :type parameters: dict[str, object]
        :param report: The report object.
        :type report: :class:`Report`
        :param timeAxis: The common time axis of the signals over the entire trace. A limitation
                         to the trigger ranges can be provided by a :class:`TriggerRange` object.
        :type timeAxis: numpy.ndarray
        :param ranges: List of trigger ranges.
        :type ranges: list[TriggerRange]
        :param signals: Dictionary of signals.
        :type signals: dict[str, :class:`Signal`]
        """
        # get parameters
        csvList = parameters['csvList']
        logoPath = parameters['logoPath']
        
        # generate figure
        figPath = _TraceEgoYawRate(csvList, logoPath)
        
        # include fig in report
        report.Image(figPath)
        os.remove(figPath)

def _LoadTraces(csvFilePath):
    data = {}
    
    # load the csv file into a dictionary
    with open(csvFilePath, 'r') as csvFile:
        reader = csv.reader(csvFile, delimiter=';')
        keys = next(reader)
        for key, column in zip(keys, zip(*reader)):
            try:
                data[key] = np.array(column, dtype=np.float)
            except:
                data[key] = np.array(column)
                
    # delete all entries with negative timestamps
    if 'timestamp' in data:
        while len(data['timestamp']) > 0 and data['timestamp'][0] < 0:
            for key in data:
                data[key] = np.delete(data[key], 0)
        while len(data['timestamp']) > 0 and data['timestamp'][-1] < 0:
            for key in data:
                data[key] = np.delete(data[key], -1)
    
    return data

def _IncludeLogo(fig, logoPath):
    try:
        logoImage = Image.open(logoPath).convert('RGBA')
    except:
        return
    figSizePx = fig.get_size_inches() * fig.dpi
    imHeight = figSizePx[1] * 0.1
    imSize = logoImage.size
    imWidth = imSize[0] / imSize[1] * imHeight
    logoImage.thumbnail((imWidth, imHeight), Image.ANTIALIAS)
    imLeft = figSizePx[0] - 3 * imHeight
    imBottom = int(imHeight * 1.5)
    fig.figimage(logoImage, alpha=0.3, xo=imLeft, yo=imBottom)
    logoImage.close()


def _TraceEgoYawRate(csvList, logoPath, dpi=300):
    # get csv file path
    egoMotionFile = None
    for fileIndex in range(len(csvList)):
        if csvList[fileIndex].split('_')[-2] == 'egomotion':
            egoMotionFile = csvList[fileIndex]
            break
        
    # check csv file path
    if egoMotionFile is None:
        return None
    
    # load data
    egoMotionData = _LoadTraces(egoMotionFile)
    time = egoMotionData['timestamp'] / 1E6
    yawRateDps = egoMotionData['yawRate/value'] / np.pi * 180.0
    # plot data
    fig = plt.figure(dpi=dpi)
    plt.plot(time, yawRateDps)
    plt.title('Ego yaw rate')
    plt.xlabel(r'$t~/~\mathrm{s}$')
    plt.ylabel(r'$\dot\psi~/~\mathrm{deg/s}$')
    plt.grid()
    
    # include logo
    if logoPath is not None:
        _IncludeLogo(fig, logoPath)
        
    # get save path
    savePath = os.path.split(egoMotionFile)[0]
    figName = 'EgoYawRate_' + egoMotionFile.split('_')[-1].split('.')[0] + '.png'
    figPath = os.path.join(savePath, figName)
    
    # save fig
    fig.savefig(figPath, dpi=fig.dpi)
    plt.close(fig)
    
    return figPath