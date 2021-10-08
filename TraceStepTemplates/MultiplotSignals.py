import textwrap

import numpy

if any(name not in globals() for name
       in ('NumpyBasedTraceStep', 'SignalDefinition', 'ParameterDefinition')):
    from NumpyBasedTraceStep import NumpyBasedTraceStep, SignalDefinition, ParameterDefinition


class MultiplotSignals(NumpyBasedTraceStep):
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
            This tracestep is used to create multiple plots in one picture by using the mathplotlib.
            ''').strip()

    @classmethod
    def GetSignals(cls):
        """
        Returns the incoming and outgoing signals of the trace step.

        :rtype: list[SignalDefinition]
        """
        return [
            SignalDefinition('Mid11', 'IN', optional=False, description=''),
            SignalDefinition('Mid12', 'IN', optional=False, description=''),
            SignalDefinition('Mid13', 'IN', optional=False, description=''),
            SignalDefinition('Mid21', 'IN', optional=False, description=''),
            SignalDefinition('Mid22', 'IN', optional=False, description=''),
            SignalDefinition('Mid23', 'IN', optional=False, description=''),
            SignalDefinition('Mid31', 'IN', optional=False, description=''),
            SignalDefinition('Mid32', 'IN', optional=False, description=''),
            SignalDefinition('Mid33', 'IN', optional=False, description=''),
            SignalDefinition('Valid_flag', 'IN', optional=True, description=''),
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
            import matplotlib.pyplot as plt
            import numpy as np
            import os
            #read the signals into variabels
            Mid11 = signals['Mid11'].GetValues()
            Mid12 = signals['Mid12'].GetValues()
            Mid13 = signals['Mid13'].GetValues()
            Mid21 = signals['Mid21'].GetValues()
            Mid22 = signals['Mid22'].GetValues()
            Mid23 = signals['Mid23'].GetValues()
            Mid31 = signals['Mid31'].GetValues()
            Mid32 = signals['Mid32'].GetValues()
            Mid33 = signals['Mid33'].GetValues()
            ValidityFlag = signals['Valid_flag'].GetValues()
            #get timestamps
            # timeStamps = triggerRange.GetTimestamps()
            timeStamps = range(len(Mid11))

            #check at which timestamp the validity flag switches to true
            res = next(x for x, val in enumerate(list(ValidityFlag)) if val > 0)

            fig, axs = plt.subplots(3, 3)#, sharey=True)
            #plt.ylim(2700, 2900)
            #Plot for pixel 130558
            axs[0, 0].plot(timeStamps[res:], Mid11[res:])
            axs[0, 0].set_title('Point 130558')
            # Plot for pixel 130559
            axs[0, 1].plot(timeStamps[res:], Mid12[res:])
            axs[0, 1].set_title('Point 130559')
            # Plot for pixel 130560
            axs[0, 2].plot(timeStamps[res:], Mid13[res:])
            axs[0, 2].set_title('Point 130560')
            # Plot for pixel 131070
            axs[1, 0].plot(timeStamps[res:], Mid21[res:])
            axs[1, 0].set_title('Point 131070')
            # Plot for pixel 131071
            axs[1, 1].plot(timeStamps[res:], Mid22[res:])
            axs[1, 1].set_title('Point 131071')
            # Plot for pixel 131072
            axs[1, 2].plot(timeStamps[res:], Mid23[res:])
            axs[1, 2].set_title('Point 131072')
            # Plot for pixel 131582
            axs[2, 0].plot(timeStamps[res:], Mid31[res:])
            axs[2, 0].set_title('Point 131582')
            # Plot for pixel 131583
            axs[2, 1].plot(timeStamps[res:], Mid32[res:])
            axs[2, 1].set_title('Point 131583')
            # Plot for pixel 131584
            axs[2, 2].plot(timeStamps[res:], Mid33[res:])
            axs[2, 2].set_title('Point 131584')

            print("MIN: {0}; MAX: {1}".format(min(Mid11[res:]),max(Mid33[res:])))

            for ax in axs.flat:
                ax.set(xlabel='t [s]', ylabel='s [cm]')

            # Hide x labels and tick labels for top plots and y ticks for right plots.
            for ax in axs.flat:
                ax.label_outer()

            scaleFactor = 3.0
            imagePath = os.path.join(os.getenv("temp"), "img02.png")
            plt.savefig(imagePath, dpi=100 * scaleFactor)
            #dataContainer.ReportImage(imagePath)
            report.Image(imagePath)
            return imagePath
