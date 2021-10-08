###################################################################################
# @file      CheckSignalInEnvelope_OptionSignals.py
# @brief     TraceStepTemplate to check if a signal has values between min and max
#            coming from a standard template with optional signals
#
# @author    FDTech GmbH
# @date      2020-07-14
# @copyright FDTech GmbH intern
# @Version   1.0
#
# |------------|---------|-----------------------------------|--------------------|
# | Date       | Version | Changes                           | Changes by         |
# |------------|---------|-----------------------------------|--------------------|
# | 14.07.2020 | 1.0     | - Initial version                 | Kevin Kleebusch    |
# |------------|---------|-----------------------------------|--------------------|
# |            |         |                                   |                    |
# |------------|---------|-----------------------------------|--------------------|
# |            |         |                                   |                    |
# |------------|---------|-----------------------------------|--------------------|
###################################################################################

import textwrap

import numpy
import numpy.ma as ma

if any(name not in globals() for name
        in ('NumpyBasedTraceStep', 'SignalDefinition', 'ParameterDefinition')):
    from NumpyBasedTraceStep import NumpyBasedTraceStep, SignalDefinition, ParameterDefinition


class CheckSignalInEnvelope_OptionalSignals(NumpyBasedTraceStep):
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
            Checks that the values of the input signal 'signalToCheck' lie between the values of the input signals 'min' and 'max'.

            Note: If this is the case the output signal is 0. Otherwise the corresponding deviation is written to the output signal 'deviation'.
            ''').strip()

    @classmethod
    def GetSignals(cls):
        """
        Returns the incoming and outgoing signals of the trace step.

        :rtype: list[SignalDefinition]
        """
        return [
            SignalDefinition('signalToCheck', 'IN', optional=True,
                            description='The signal to check.'),
            SignalDefinition('max', 'IN', optional=True,
                            description='The signal for the upper bound.'),
            SignalDefinition('min', 'IN', optional=True,
                            description='The signal for the lower bound.'),
            SignalDefinition('deviation', 'OUT', optional=True,
                            description='The output signal with the calculated deviation of '
                                        'the envelope check.')
            ]

    @classmethod
    def GetParameters(cls):
        """
        Returns the input and return parameters of the trace step.

        :rtype: list[ParameterDefinition]
        """
        return [
            ParameterDefinition('startTime', 'IN', default=float('-inf'),
                                description="The check starts at timestamp 'startTime'."),
            ParameterDefinition('tolerance', 'IN', default=0,
                                description="A positive value taken into account when "
                                            "comparing 'signalToCheck' with 'min' and 'max'."),
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
        return 'signalToCheck'

    def Check(self, parameters):
        """
        Is called initially before trace analysis execution and should check the parameterization.
        In case of error, raise a TypeError or ValueError.

        :param parameters: Dictionary of parameter values.
        :type parameters: dict[str, object]
        :raise TypeError: Invalid type of a parameter.
        :raise ValueError: Invalid value of a parameter.
        """
        startTime = parameters['startTime']
        tolerance = parameters['tolerance']
        if not isinstance(startTime, (float, int)):
            raise ValueError(f"The paramater 'startTime' has no valid type "
                             f"({type(startTime)}).")
        if not isinstance(tolerance, (float, int)):
            raise ValueError(f"The paramater 'tolerance' has no valid type "
                             f"({type(tolerance)}).")
        if tolerance < 0:
            raise ValueError(f"The parameter 'tolerance' must be greater than or equal to zero "
                             f"({tolerance}).")

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
        tolerance = parameters['tolerance']
        startTime = parameters['startTime']
        for triggerRange in ranges:
            # get the signal values starting from startTime
            allTimestamps = triggerRange.GetTimestamps()
            startTimeMask = triggerRange.GetTimestamps() >= startTime
            signalValues = triggerRange.GetValues('signalToCheck')[startTimeMask]
            if len(signalValues) == 0:  # pylint: disable=len-as-condition
                triggerRange.SetResultNone()
                continue
            timeStamps = allTimestamps[startTimeMask]

            # mask the idle values of the signal as invalid
            # cast to float to avoid overflow in subsequent calculations
            maskedSignalValues = ma.masked_invalid(signalValues.astype(numpy.float64))

            # get the min/max values starting from startTime
            minValues = triggerRange.GetValues('min')[startTimeMask]
            maxValues = triggerRange.GetValues('max')[startTimeMask]

            # mask the idle values of min/max as invalid
            maskedMinValues = ma.masked_invalid(minValues)
            maskedMaxValues = ma.masked_invalid(maxValues)

            # calculate the boolean masks that indicate whether lower and upper bound are satisfied.
            minSatisfiedMask = (maskedSignalValues + tolerance) >= maskedMinValues
            maxSatisfiedMask = (maskedSignalValues - tolerance) <= maskedMaxValues

            # Only when the values of minSatisfiedMask and maxSatisfiedMask are TRUE, the signal is
            # within the envelope.
            envelopeSatisfied = minSatisfiedMask & maxSatisfiedMask
            failureCount = len(ma.nonzero(~envelopeSatisfied)[0])

            # Check, whether min and max are inverted (faulty) at any point.
            # Spots with FALSE values in both, minSatisfiedMask and maxSatisfiedMask, indicate
            # such points.
            invertedMinMax = numpy.any(~(minSatisfiedMask | maxSatisfiedMask))

            if failureCount == 0:
                triggerRange.SetResultSuccess()
                triggerRange.SetResultText('0 failed spots found')
                signals['deviation'].Emit(timeStamps, numpy.zeros(len(timeStamps)))
            else:
                triggerRange.SetResultFailed()
                if invertedMinMax:
                    # Deviation plot might be not feasible due to faulty min/max input signals.

                    # Build list of continuous boolean values.
                    boolRanges = self.CalculateRanges(~numpy.logical_or(minSatisfiedMask,
                                                                        maxSatisfiedMask))
                    for boolRange in boolRanges:
                        if boolRange[2]:  # continuous TRUE represents inverted values
                            errorStartTime = timeStamps[boolRange[0]]
                            if boolRange[1] < len(timeStamps):
                                errorEndTime = timeStamps[boolRange[1]]
                            else:
                                errorEndTime = timeStamps[-1]
                            triggerRange.Range(startTime=errorStartTime,
                                               stopTime=errorEndTime,
                                               message="The signals 'min' and 'max' are inverted!",
                                               resultId=triggerRange.RESULT_ID_ERROR)
                else:
                    # Spots and ranges must be in temporal order. Therefore failed spots are only
                    # reported, when there are no error ranges, to not violate this restriction.
                    failedSpots = ma.where(~envelopeSatisfied)[0]
                    if len(failedSpots) > 0:
                        for failIndex in numpy.nditer(failedSpots):
                            triggerRange.Spot(timeStamps[failIndex],
                                              resultId=triggerRange.RESULT_ID_FAILED)

                triggerRange.SetResultText(f'{failureCount} failed spots found')

                maskedMinDeviationValues = (
                    ma.masked_greater(maskedSignalValues - maskedMinValues, 0))
                maskedMaxDeviationValues = (
                    ma.masked_less(maskedSignalValues - maskedMaxValues, 0))

                deviationValues = (maskedMinDeviationValues.filled(0)
                                   +maskedMaxDeviationValues.filled(0))
                if invertedMinMax:
                    signals['deviation'].Emit(
                        timeStamps[(minSatisfiedMask | maxSatisfiedMask)],
                        deviationValues[(minSatisfiedMask | maxSatisfiedMask)])
                else:
                    signals['deviation'].Emit(timeStamps, deviationValues)
