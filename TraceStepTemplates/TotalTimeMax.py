# -*- coding: utf-8 -*-

from abc import abstractmethod

import numpy

if any(name not in globals() for name
        in ('NumpyBasedTraceStep', 'SignalDefinition', 'ParameterDefinition')):
    from NumpyBasedTraceStep import NumpyBasedTraceStep, SignalDefinition, ParameterDefinition


class TotalTimeMax(NumpyBasedTraceStep):
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
        return u'Calculate maximum value of trigger range durations.'

    @classmethod
    def GetSignals(cls):
        """
        Returns the incoming and outgoing signals of the trace step.
        
        :rtype: list[SignalDefinition]
        """
        return [SignalDefinition(u'Signal', 'IN', optional=False, description=u''),
                SignalDefinition(u'TotalTimeMax', 'OUT', optional=False, description=u'')]

    @classmethod
    def GetParameters(cls):
        """
        Returns the input and return parameters.
        
        :rtype: list[ParameterDefinition]
        """
        return [ParameterDefinition(u'TotalTimeMax', 'OUT', description=u'')]

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
        
        totalTime = float(0)
        # print(type(totalTime))
        # print(totalTime)
        totalTimeMax = float(u'NaN')
        # print(type(totalTimeMax))
        # print(totalTime)
        resultTimestamps = []

        for triggerRange in ranges:
            values = triggerRange.GetValues(u'Signal')
            timestamps = triggerRange.GetTimestamps()

            if values.size > 0:
                totalTime = timestamps[-1] - timestamps[0]
                totalTimeMax = max(totalTime, totalTimeMax)
                print(totalTimeMax)
                resultTimestamps.append(timestamps)
                triggerRange.SetResultText(u'Success.\nTotal time of this trigger range: %2.3f' % totalTime)
            else:
                triggerRange.SetResultText(u'No values in the given trigger range.')
                
        # concatenate timestamps
        timestampsArray = numpy.concatenate(resultTimestamps)
        # create numpy.ndarray with totalTime as constant value, to match length of timestamp array
        valuesArray = numpy.empty((len(timestampsArray)))
        valuesArray.fill(totalTimeMax)
        # print(type(valuesArray))
        # print(len(valuesArray))
        
        
        # write new signal
        signals[u'TotalTimeMax'].Emit(
        values=valuesArray,
        timestamps=timestampsArray)
        
        # write parameter
        parameters[u'TotalTimeMax'] = totalTimeMax
            
            
