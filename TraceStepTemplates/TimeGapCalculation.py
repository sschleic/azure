###################################################################################
# @file      TimeGapCalculation.py
# @brief     TraceStepTemplate to calculate a time gap between two objects
#
# @author    FDTech GmbH
# @date      2020-07-02
# @copyright FDTech GmbH intern
# @Version   1.0
#
# |------------|---------|-----------------------------------|--------------------|
# | Date       | Version | Changes                           | Changes by         |
# |------------|---------|-----------------------------------|--------------------|
# | 02.07.2020 | 1.0     | - Initial version                 | Kevin Kleebusch    |
# |------------|---------|-----------------------------------|--------------------|
# |            |         |                                   |                    |
# |------------|---------|-----------------------------------|--------------------|
# |            |         |                                   |                    |
# |------------|---------|-----------------------------------|--------------------|
###################################################################################


import textwrap
import numpy

if any(name not in globals() for name
        in ('NumpyBasedTraceStep', 'SignalDefinition', 'ParameterDefinition')):
    from NumpyBasedTraceStep import NumpyBasedTraceStep, SignalDefinition, ParameterDefinition


class TimeGapCalculation(NumpyBasedTraceStep):
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
            This tracestep template is used to calculate a time gap between two objects.
            ''').strip()

    @classmethod
    def GetSignals(cls):
        """
        Returns the incoming and outgoing signals of the trace step.

        :rtype: list[SignalDefinition]
        """
        return [
            SignalDefinition('s_LongDist', 'IN', optional=True, description='Distance between two objects.'),
            SignalDefinition('v_LongEgo', 'IN', optional=True, description='Velocity of the following object.'),
            SignalDefinition('t_timeGap', 'OUT', optional=True, description='Resulting time gap signal.'),
            ]

    @classmethod
    def GetParameters(cls):
        """
        Returns the input and return parameters of the trace step.

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
        for triggerRange in ranges:
            # getting the signal values
            distance = triggerRange.GetValues('s_LongDist')
            velocity = triggerRange.GetValues('v_LongEgo')
            timeStamps = triggerRange.GetTimestamps()
            # creating empty result hull
            timeGap = ([])
            for index in range(len(velocity)):
                # calculation
                if distance[index] != 0 and velocity[index] != 0:
                    timeGap.append(distance[index] / velocity[index])
                elif distance[index] == 0 and velocity[index] != 0:
                    timeGap.append(0)
                # using an arbitrary value for infinity
                elif distance[index] != 0 and velocity[index] == 0:
                    timeGap.append(123.456)
                else:
                    timeGap.append(123.456)
            # building the signal from the result
            signals['t_timeGap'].Emit(timeStamps, timeGap)
