# -*- coding: utf-8 -*-

from abc import abstractmethod

import numpy as np

if any(name not in globals() for name
        in ('NumpyBasedTraceStep', 'SignalDefinition', 'ParameterDefinition')):
    from NumpyBasedTraceStep import NumpyBasedTraceStep, SignalDefinition, ParameterDefinition


class World2EgoCoordinateSystemConverter(NumpyBasedTraceStep):
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
        return u"Takes 3 vector signals WorldX, WorldY and Heading in world coordinate system and converts WorldX, WorldY as well as their sum into ego's coordinate system."

    @classmethod
    def GetSignals(cls):
        """
        Returns the incoming and outgoing signals of the trace step.
        
        :rtype: list[SignalDefinition]
        """
        return [SignalDefinition(u'WorldX', 'IN', optional=True, description=u''),
                SignalDefinition(u'WorldY', 'IN', optional=True, description=u''),
                SignalDefinition(u'Heading', 'IN', optional=True, description=u''),
                SignalDefinition(u'EgoX', 'OUT', optional=True, description=u''),
                SignalDefinition(u'EgoY', 'OUT', optional=True, description=u''),
                SignalDefinition(u'EgoSum', 'OUT', optional=True, description=u'')]

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
            valuesX = triggerRange.GetValues(u'WorldX')
            valuesY = triggerRange.GetValues(u'WorldY')
            valuesHeading = triggerRange.GetValues(u'Heading')
            timestamps = triggerRange.GetTimestamps()

            # compute output signals
            EgoSum = np.sqrt(np.power(valuesX, 2) + np.power(valuesY, 2))
            EgoX = np.cos(valuesHeading) * EgoSum
            EgoY = np.sin(valuesHeading) * EgoSum

            # emit new signals
            signals[u'EgoX'].Emit(timestamps, EgoX)
            signals[u'EgoY'].Emit(timestamps, EgoY)
            signals[u'EgoSum'].Emit(timestamps, EgoSum)