###################################################################################
# @file      SignalRangeCheck.py
# @brief     TraceStepTemplate to check if a specified value can be found for a
#            specified time in a reference signal without interruption
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


class SignalRangeCheck(NumpyBasedTraceStep):
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
            This teststep checks if a reference value (+/- tolerance limits) can be found in a signal for a defined time (without interruption).
            ''').strip()

    @classmethod
    def GetSignals(cls):
        """
        Returns the incoming and outgoing signals of the trace step.

        :rtype: list[SignalDefinition]
        """
        return [
            SignalDefinition('valuesSignal', 'IN', optional=True, description='Input Signal which delivers the values to be checked.'),
            ]

    @classmethod
    def GetParameters(cls):
        """
        Returns the input and return parameters of the trace step.

        :rtype: list[ParameterDefinition]
        """
        return [
            ParameterDefinition('referenceValue', 'IN',
                                description='Reference Value which shall be found in the values signal.'),
            ParameterDefinition('lowerTolerance', 'IN',
                                description='Tolerance for the lower limit of the reference value.'),
            ParameterDefinition('upperTolerance', 'IN',
                                description='Tolerance for the upper limit of the reference value.'),
            ParameterDefinition('timeStepSize', 'IN', description='Size of each time step provided in seconds.'),
            ParameterDefinition('targetTime', 'IN',
                                description='Time for which an uninterupted period of reference values shall be found in the values signal. Provided in seconds.'),
            ParameterDefinition('result', 'OUT',
                                description='Boolian value if the check was successful.'),
            ParameterDefinition('maxTime', 'OUT',
                                description='Maximum time found in the signal.')
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
        # import all parameters
        reference = parameters['referenceValue']
        lowerTolerance = parameters['lowerTolerance']
        upperTolerance = parameters['upperTolerance']
        timeStepSize = parameters['timeStepSize']
        targetTime = parameters['targetTime']
        # create the boundaries
        lowerBoundary = reference - lowerTolerance
        upperBoundary = reference + upperTolerance
        timeCheck = 0
        maxTime = 0
        for triggerRange in ranges:
            values = triggerRange.GetValues('valuesSignal')
            for index in values:
                # when signal values inside boundaries start a counter
                if lowerBoundary < index < upperBoundary:
                    # time check is the counter variable and gets incremented by the time step of the signal
                    timeCheck = timeCheck + timeStepSize
                    # max time is used for cases where the target was not achieved. It delivers feedback for the
                    # maximum time achieved in holding the parameter range
                    if timeCheck > maxTime: maxTime = timeCheck
                    # if target is achieve the results are given back and the analysis is finished
                    if timeCheck >= targetTime:
                        print("Time reached")
                        parameters['result'] = True
                        parameters['maxTime'] = maxTime
                        break
                # when the signal isn't inside the boundary reset the counter and check the rest of the signal
                else:
                    if timeCheck != 0: print(f"timeCheck maximum: {timeCheck}")
                    timeCheck = 0
            # if the analysis ends without reaching the target return the results
            if timeCheck < targetTime:
                print("Time target hasn't been reached")
                parameters['result'] = False
                parameters['maxTime'] = maxTime
            return