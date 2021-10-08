###################################################################################
# @file      SignalRangeCheck.py
# @brief     TraceStepTemplate to check if a specified value can be found for a
#            specified time in a reference signal without interruption
#
# @author    FDTech GmbH
# @date      2019-06-05
# @copyright FDTech GmbH intern
# @Version   1.1
#
# |------------|---------|-----------------------------------|--------------------|
# | Date       | Version | Changes                           | Changes by         |
# |------------|---------|-----------------------------------|--------------------|
# | 05.06.2019 | 1.0     | - Initial version                 | Kevin Kleebusch    |
# |------------|---------|-----------------------------------|--------------------|
# | 28.08.2019 | 1.1     | -Rework of the calculation        | Kevin Kleebusch    |
# |------------|---------|-----------------------------------|--------------------|
# |            |         |                                   |                    |
# |------------|---------|-----------------------------------|--------------------|
###################################################################################

import numpy as np
import math

if any(name not in globals() for name
        in ('NumpyBasedTraceStep', 'SignalDefinition', 'ParameterDefinition')):
    from NumpyBasedTraceStep import NumpyBasedTraceStep, SignalDefinition, ParameterDefinition


class CalculateResultantSignal(NumpyBasedTraceStep):
    """
    This is an implementation of NumpyBasedTraceStep.
    
    Use the interface as reference of available methods. Abstract methods have to be implemented.
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
        
        :rtype: unicode
        """
        return u'Calculates the direction of the signal depending on the direction of the input signals.'

    @classmethod
    def GetSignals(cls):
        """
        Returns the incoming and outgoing signals of the trace step.
        
        :rtype: list[SignalDefinition]
        """
        return [
                SignalDefinition(u'signalX', 'IN', optional=True, description=u'Signal in x direction'),
                SignalDefinition(u'signalY', 'IN', optional=True, description=u'Signal in y direction'),
                SignalDefinition(u'resultSignal', 'OUT', optional=True, description='Resulting signal'),
                SignalDefinition(u'signalQuadrant', 'OUT', optional=True, description='Quadrant in which the resulting signal is located')]

    @classmethod
    def GetParameters(cls):
        """
        Returns the input and return parameters.
        
        :rtype: list[ParameterDefinition]
        """
        return []

    @classmethod
    def GetTimeAxisDefinition(cls):
        """
        Returns how the common time axis is determined. Only the logical operators **and** and 
        **or** as well as references to the time axes of the signals by using the signal name are
        permitted. The use of brackets is allowed.
        
        :note: If a signal is not defined on the common time axis, its value is determined
               according to its interpolation rule.
        
        :return: Convention for building the common time axis (e.g. **'Sig1 or Sig2'**). If None,
                 all time axes are merged to a common time axis. This corresponds to an
                 OR concatenation of the individual time axes.
        :rtype: unicode
        """
        # e.g. 'Sig1 or Sig2' - timestamps either from Sig1 or Sig2 (default behavior)
        # e.g. 'Sig1 and Sig2' - only timestamps common to both Sig1 and Sig2
        return u''

    def Check(self, parameters):
        """
        Is called initially before execution and should check the parameterization.
        If an error exists, a TypeError or ValueError should be raised.
        
        :param parameters: Dictionary with parameter values
        :type parameters: dict[unicode, object]
        :raise TypeError: Invalid type of a parameter.
        :raise ValueError: Invalid value of a parameter.
        """
        return None

    def Process(self, parameters, report, timeAxis, ranges, signals):
        """
        Method for performing the trace step template. Calculations can be performed based on
        the given signal values and their results can be stored in outgoing signals. Evaluation
        results and output parameters can be set.
        
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
        :param parameters: Dictionary containing parameter values
        :type parameters: dict[unicode, object]
        :param report: The report object.
        :type report: :class:`.Report`
        :param timeAxis: The common time axis of the signals over the entire trace. A limitation
                         to the trigger ranges can be provided by a :class:`TriggerRange` object.
        :type timeAxis: numpy.ndarray
        :param ranges: List containing trigger ranges.
        :type ranges: list[TriggerRange]
        :param signals: Dictionary of signals.
        :type signals: dict[unicode, :class:`.Signal`]
        """
        
        for triggerRange in ranges:
            # fetch input signals
            valuesX = triggerRange.GetValues(u'signalX')
            valuesY = triggerRange.GetValues(u'signalY')
            timeStamps = triggerRange.GetTimestamps()
            # create empty signal hulls
            resultValue=([])
            quadrant=([])

            for index in range(len(valuesX)):
            # compute output signal
                if valuesX[index] >= 0:
                    resultValue.append(math.sqrt(math.pow(valuesX[index], 2) + math.pow(valuesY[index], 2)))
                else:
                    resultValue.append(-math.sqrt(math.pow(valuesX[index], 2) + math.pow(valuesY[index], 2)))

                if (valuesX[index] and valuesY[index]) > 0:
                    quadrant.append(1)
                elif valuesX[index] > 0 and valuesY[index] < 0:
                    quadrant.append(2)
                elif (valuesX[index] and valuesY[index]) < 0:
                    quadrant.append(3)
                elif valuesX[index] < 0 and valuesY[index] > 0:
                    quadrant.append(4)
                elif valuesX[index] == 0 or valuesY[index] == 0:
                    quadrant.append(0)
            
            # emit new signal
            signals[u'resultSignal'].Emit(timeStamps, resultValue)
            signals[u'signalQuadrant'].Emit(timeStamps, quadrant)