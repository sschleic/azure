# coding: utf8
import os
import socket
import time

from application.api.Api import Api
from lib.common.Properties import PropertyTypeId
from lib.tooling.Capabilities import Toolcaps
from lib.tooling.Descriptors import ToolDescriptor, PropertyDescriptor, JobDescriptor
from lib.tooling.toolLibs.base.AbstractAdapter import ToolAdapter
from lib.tooling.toolLibs.base.Proxy import ToolAdapterProxy
from tts.tooling.tool.SSH_2.SSHClient import SSHClient

import subprocess, sys

###############################################################################
# @file CarMakerLinuxAdapter.py
# @brief Custom tooladapter to get a connection between ECU-TEST and CarMaker
# on linux
#
# @author FDTech GmbH & TraceTronic GmbH
# @copyright unknown
# @Version: 1.3
#
# |------------|---------|-----------------------------------|--------------------|
# | Date       | Version | Changes                           | Changes by         |
# |------------|---------|-----------------------------------|--------------------|
# | 04.04.2019 | 0.5     | - Initial version                 | Kevin Kleebusch    |
# |            |         |                                   | Fabian Nobis       |
# |------------|---------|-----------------------------------|--------------------|
# | 09.01.2020 | 1.0     | - General improvements            | Oliver Kiethe      |
# |            |         |                                   | Kevin Kleebusch    |
# |------------|---------|-----------------------------------|--------------------|
# | 28.02.2020 | 1.1     | - Added a option to wait          | Kevin Kleebusch    |
# |            |         |   for CarMaker to finish          |                    |
# |            |         |   saving the signalfile           |                    |
# |------------|---------|-----------------------------------|--------------------|
# | 09.03.2020 | 1.2     | - Added a test step to transfer   | Kevin Kleebusch    |
# |            |         |   a given folder with scenarios   |                    |
# |            |         |   to the CarMaker machine         |                    |
# |------------|---------|-----------------------------------|--------------------|
# | 16.08.2021 | 1.3     | - Added a timeout option to the   | Stephan Schleicher |
# |            |         |   SendTclCommand job              | Oliver Kiethe      |
# |            |         | - Get free port for CarMaker      |                    |
# |            |         | - Added option to start a remote  |                    |
# |            |         |   session                         |                    |
# |------------|---------|-----------------------------------|--------------------|
###############################################################################


TOOLNAME = 'CarMaker-Linux'
TOOLCAPS = Toolcaps.GetNull()


def IsInstalled():
    return True


def CreateToolAdapter(host=None, port=None):
    return ToolAdapterProxy(CarMakerLinuxAdapter())


class CarMakerLinuxAdapter(ToolAdapter):
    def __init__(self):
        ToolAdapter.__init__(self)

        self._socket = None

        self._sshClient = None

        self._mstscPid = 0

        self._CMcmdport = 0

        self.displayNumber = 1245

        self._toolDesc = ToolDescriptor(
            TOOLNAME,
            [],  # must be an empty list
            0,
            # Each property of the adapter has some parameters
            # Adapter internal name and description, a default value, a name for the GUI (displayName),
            # which type the value can be
            # List of PropertyDescriptors:
            [
                PropertyDescriptor.CreateInstance(
                    name='ipAddress',
                    displayName='IP address of CarMaker GUI host',
                    displayLevel=0,
                    description='The IP adress of the host where the CarMaker GUI to automate is located.',
                    type=PropertyTypeId.string,
                    validReferences=None,
                    default='127.0.0.1',
                    readonly=False
                ),
                PropertyDescriptor.CreateInstance(
                    name='carMakerBasePath',
                    displayName='CarMaker project path',
                    displayLevel=0,
                    description='Base path of CarMaker project on Linux host.',
                    type=PropertyTypeId.string,
                    validReferences=None,
                    default='',
                    readonly=False
                ),
                PropertyDescriptor.CreateInstance(
                    name='sshPort',
                    displayName='SSH port',
                    displayLevel=0,
                    description='SSH port of the CarMaker Linux host.',
                    type=PropertyTypeId.int,
                    validReferences=None,
                    default=22,
                    readonly=False
                ),
                PropertyDescriptor.CreateInstance(
                    name='sshUsername',
                    displayName='SSH username',
                    displayLevel=0,
                    description='User name to log into the CarMaker Linux host via SSH.',
                    type=PropertyTypeId.string,
                    validReferences=None,
                    default='',
                    readonly=False
                ),
                PropertyDescriptor.CreateInstance(
                    name='sshKeyPath',
                    displayName='SSH private key path',
                    displayLevel=0,
                    description='Absolute path to the private key file on the local machine.',
                    type=PropertyTypeId.string,
                    validReferences=None,
                    default='',
                    readonly=False
                ),
                PropertyDescriptor.CreateInstance(
                    name='startScriptPath',
                    displayName='Start Script Path',
                    displayLevel=0,
                    description='Absolute path of the start script file on the machine.',
                    type=PropertyTypeId.string,
                    validReferences=None,
                    default='',
                    readonly=False
                ),
                PropertyDescriptor.CreateInstance(
                    name='libPath',
                    displayName='CarMaker-Extension Library Path',
                    displayLevel=0,
                    description='Absolut path of the CarMakerExtension Libary on the machine.',
                    type=PropertyTypeId.string,
                    validReferences=None,
                    default='',
                    readonly=False
                ),
                PropertyDescriptor.CreateInstance(
                    name='Headless',
                    displayName='Starting CarMaker on a virtual display',
                    displayLevel=0,
                    description='If true, starts CarMaker on virtual display via "Xvfb"',
                    type=PropertyTypeId.bool,
                    validReferences=None,
                    default=True,
                    readonly=False
                ),
                PropertyDescriptor.CreateInstance(
                    name='Remote',
                    displayName='Remote Session',
                    displayLevel=0,
                    description='If true, opens SSH session with username and password',
                    type=PropertyTypeId.bool,
                    validReferences=None,
                    default=False,
                    readonly=False
                ),
                PropertyDescriptor.CreateInstance(
                    name='StartCarmaker',
                    displayName='Start CarMaker',
                    displayLevel=0,
                    description='If true, starts and connects to CarMaker with the start of the configuration',
                    type=PropertyTypeId.bool,
                    validReferences=None,
                    default=True,
                    readonly=False
                ),
            ],
            # Each tooljob and each option in the tooljob has it's own parameters:
            # internal name, name for the GUI, default values, description and type
            # List of ToolJobs:
            [
                JobDescriptor(
                    'SendTclCommand', 
                    [
                        PropertyDescriptor.CreateInstance(
                            name='tclCommand',
                            displayName='TCL Command',
                            description='',
                            default='',
                            type=PropertyTypeId.string
                        ),
                        PropertyDescriptor.CreateInstance(
                            name='timeout',
                            displayName='Timeout',
                            description='Timeout in seconds',
                            default=None,
                            type=PropertyTypeId.object
                        )
                    ],
                    'Sends a TCL command to CarMaker and returns its response.',
                    PropertyDescriptor.CreateInstance(
                        name='result',
                        description='',
                        type=PropertyTypeId.string
                    ),
                ),
                JobDescriptor(
                    'LoadScenario', 
                    [
                        PropertyDescriptor.CreateInstance(
                            name='scenarioName',
                            displayName='Scenario name',
                            description='',
                            default='',
                            type=PropertyTypeId.string
                        )
                    ],
                    'Loads a given CarMaker scenario.',
                    PropertyDescriptor.CreateInstance(
                        name='result',
                        description='',
                        type=PropertyTypeId.string
                    ),
                ),
                JobDescriptor(
                    'StartSimulation', 
                    [],
                    'Starts the CarMaker simulation.',
                    PropertyDescriptor.CreateInstance(
                        name='result',
                        description='',
                        type=PropertyTypeId.string
                    ),
                ),
                JobDescriptor(
                    'StopSimulation', 
                    [
                        PropertyDescriptor.CreateInstance(
                            name='stopImmediately',
                            displayName='Stop immediately',
                            description='Stops the simulation immediately if true, else it waits for the simulation to finish.',
                            default=True,
                            type=PropertyTypeId.bool
                        ),
                        PropertyDescriptor.CreateInstance(
                            name='timeout',
                            displayName='Timeout',
                            description='Timeout in seconds if waiting for simulation end.',
                            default=1000,
                            type=PropertyTypeId.int,
                        ),
                    ],
                    'Stops the CarMaker simulation.',
                    PropertyDescriptor.CreateInstance(
                        name='result',
                        description='',
                        type=PropertyTypeId.string
                    ),
                ),
                JobDescriptor(
                    'ChangeParameter', 
                    [
                        PropertyDescriptor.CreateInstance(
                            name='parameterName',
                            displayName='Parameter name',
                            description='',
                            default='',
                            type=PropertyTypeId.string
                        ),
                        PropertyDescriptor.CreateInstance(
                            name='parameterValue',
                            displayName='Parameter value',
                            description='',
                            default='',
                            type=PropertyTypeId.string
                        ),
                    ],
                    'Changes a named value parameter.',
                    PropertyDescriptor.CreateInstance(
                        name='result',
                        description='',
                        type=PropertyTypeId.string
                    ),
                ),
                JobDescriptor(
                    'SendSshCommand', 
                    [
                        PropertyDescriptor.CreateInstance(
                            name='sshCommand',
                            displayName='SSH Command',
                            description='',
                            default='',
                            type=PropertyTypeId.string
                        ),
                    ],
                    'Sends a SSH command and returns its response.',
                    PropertyDescriptor.CreateInstance(
                        name='result',
                        description='',
                        type=PropertyTypeId.string
                    ),
                ),
                JobDescriptor(
                    'TransferTrace', 
                    [
                        PropertyDescriptor.CreateInstance(
                            name='recordingFileName',
                            displayName='Recording file name',
                            description='Name of the recording file (file type .erg)',
                            default='.erg',
                            type=PropertyTypeId.string
                        ),
                        PropertyDescriptor.CreateInstance(
                            name='waitTime',
                            displayName='Include waiting period',
                            description='Include a waiting period of 5x30sec',
                            default=True,
                            type=PropertyTypeId.bool
                        ),
                    ],
                    'Transfers the tracefile from the remote host to the local recording folder.',
                    PropertyDescriptor.CreateInstance(
                        name='result',
                        description='',
                        type=PropertyTypeId.string
                    ),
                ),
                JobDescriptor(
                    'TransferScenarios', 
                    [
                        PropertyDescriptor.CreateInstance(
                            name='scenarioFolder',
                            displayName='Path to the scenario folder',
                            description='Absolute path to the the scenario folder (will be moved recursive!)',
                            default=r'C:\\PATH\\TO\\FOLDER',
                            type=PropertyTypeId.string
                        ),
                        PropertyDescriptor.CreateInstance(
                            name='roadFolder',
                            displayName='Path to the topology folder',
                            description='Absolute path to the the topology folder (will be moved recursive!)',
                            default=r'C:\\PATH\\TO\\FOLDER',
                            type=PropertyTypeId.string
                        ),
                    ],
                    'Transfer the scenarios to the CarMaker machine',
                    PropertyDescriptor.CreateInstance(
                        name='result',
                        description='',
                        type=PropertyTypeId.string
                    ),
                ),
                JobDescriptor(
                    'EnableRecording', 
                    [],
                    'Configures CarMaker to start recording everything to an .erg file.',
                    PropertyDescriptor.CreateInstance(
                        name='result',
                        description='',
                        type=PropertyTypeId.string
                    ),
                ),
                JobDescriptor(
                    'StartCarmaker', 
                    [],
                    'Starts Carmaker.',
                    PropertyDescriptor.CreateInstance(
                        name='result',
                        description='',
                        type=PropertyTypeId.string
                    ),
                ),
                JobDescriptor(
                    'StopCarmaker', 
                    [],
                    'Stops Carmaker',
                    PropertyDescriptor.CreateInstance(
                        name='result',
                        description='',
                        type=PropertyTypeId.string
                    ),
                ),
                JobDescriptor(
                    'TransferFile', 
                    [
                        PropertyDescriptor.CreateInstance(
                                name='filePath',
                                displayName='Path to the file which will be copied',
                                description='Path of the file',
                                default='PATH//TO//MOVIE.mp4',
                                type=PropertyTypeId.string
                        ),
                    ],
                    'Transfers the file from the remote host to the local recording folder.',
                    PropertyDescriptor.CreateInstance(
                            name='result',
                            description='',
                            type=PropertyTypeId.string),
                    ),
            ]
        )

    # proceeding at start of the configuration
    def OnConfigure(self):
        print('Connecting to CarMaker host via SSH')
        self._sshClient = SSHClient(self.GetTypedProperty('ipAddress'),
                                    self.GetTypedProperty('sshPort'),
                                    self.GetTypedProperty('sshUsername'),
                                    privateKeyPath='{0}'.format(self.GetTypedProperty('sshKeyPath')))

        if self.GetTypedProperty('Remote'):
            self.__StartRemoteSession()
            time.sleep(7)
            
            
        # If headless true then use function "Xvfb" for virtual display
        if self.GetTypedProperty('Headless'):
            sshCommand = "Xvfb :{0}".format(self.displayNumber)
            self.JobSendSshCommand(sshCommand, blocking=False)
            
        if self.GetTypedProperty('StartCarmaker'):
            self.__StartCarmaker()
            # build connection via the given ipAddress and port for the gui
            self.__ConnectToCarMaker(self.GetTypedProperty('ipAddress'))


    def OnUnconfigure(self):
        print('Closing connection to CarMaker')
        self.JobSendTclCommand("GUI quit", tryReconnect=False)
        self.__StopCarmaker()
        # If headless true then kill "Xvfb"
        if self.GetTypedProperty('Headless'):
            self.JobSendSshCommand('pkill -u $(whoami) Xvfb', blocking=True)

        p = subprocess.Popen(["powershell.exe", "cmdkey /delete:{0}".format(self.GetTypedProperty('ipAddress'))])
         
        # close ssh connection
        self._sshClient.Close()

    def IsBroken(self):
        return False

    def JobSendTclCommand(self, tclCommand, timeout=None, tryReconnect=True):
        # formatting the string to be received by carmaker
        numberOfLines = len(tclCommand.splitlines())
        fullCommand = '{0}{1}\n'.format(numberOfLines, tclCommand)

        # debug print
        print('Sending TCL command: {0}'.format(fullCommand))

        self._socket.settimeout(timeout)
        try:
            # encoding the command to the suitable format
            self._socket.sendall(fullCommand.encode('ascii'))
            # decode the received answer
            data = self._socket.recv(1024).decode('utf8')
        except:
            return 'TIMEOUT'
        self._socket.settimeout(None)
        
        # if the tcl command is "exit" we get no answer, therefore checking it only if command is NOT exit
        if tclCommand != 'exit':
            if data[0] == 'E':  # Erstes Zeichen der Rueckgabe ist ein O (Ok) oder E (Error)
                # Reconnect if connection fails
                if not data:
                    if tryReconnect:
                        self._socket.close()
                        self.__ConnectToCarMaker(self.GetTypedProperty('ipAddress'))
                        return self.JobSendTclCommand(tclCommand, timeout=timeout, tryReconnect=False)
                        print('Could not connect to the CarMaker instance')
                    # To prevent endless loops of reconnects, if connection is completely dead
                    else:
                        raise RuntimeError('Could not re-establish TCP connection to CarMaker!')
        if tclCommand != 'exit':
            # First char of return is a O (Ok) or E (Error)
            if data[0] == 'E':
                raise RuntimeError('The evaluation of the TCL command failed: {0}'.format(data))

        # remove linebreak at end of response
        return data[1:].rstrip()

    # quality of life tooljob for quickly loading a scenario by using the send tclCommand function
    def JobLoadScenario(self, scenarioName):
        return self.JobSendTclCommand('LoadTestRun {0}'.format(scenarioName))

    # quality of life tooljob for quickly starting the simulation
    def JobStartSimulation(self):
        return self.JobSendTclCommand('StartSim')

    # stopping the simulation depending on the given mode
    def JobStopSimulation(self, stopImmediately, timeout):
        print('Stop simulation, stop immediately: {0}, timeout: {1} s'.format(stopImmediately,
                                                                            timeout))
        if not stopImmediately:
            time.sleep(2)
            # A little wait time for CarMaker after the simulation starts to get to status running
            self.JobSendTclCommand('WaitForStatus idle {0}'.format(timeout * 1000))

        return self.JobSendTclCommand('StopSim')

    # quality of life tooljob for quickly changing a parameter
    def JobChangeParameter(self, parameterName, parameterValue):
        return self.JobSendTclCommand('NamedValue set {0} {1}'.format(parameterName, parameterValue))

    # using the internal ssh client to send a ssh command to the remote machine
    def JobSendSshCommand(self, sshCommand, blocking=True):
        print('Send {0} SSH command: {1}'.format('blocking' if blocking else 'non blocking',
                                               sshCommand))
        if blocking:
            return self._sshClient.ExecCommand(sshCommand)[1].readlines()
        return self._sshClient.ExecCommand(sshCommand, False)

    # quality of life tooljob for stopping carmaker using a ssh command to kill the application and then exit the GUI
    def __StopCarmaker(self):
        print('Stopping CarMaker now')
        self.JobSendTclCommand('Application shutdown')
        time.sleep(1)
        self.JobSendTclCommand('exit')
        self._socket.close()

    def __DisplayNumberViaSSH(self):
        sshCommand = 'ps aux | grep Xorg'
        returns = self.JobSendSshCommand(sshCommand, blocking=True)
        
        for ret in returns:
            if self.GetTypedProperty('sshUsername')[0:6] in ret and "-auth .Xauthority" in ret:
                arguments = ret.split()
                displayNumber = arguments[11][1:]
                print('Ask for display: {}'.format(displayNumber))
                return displayNumber
        
    def __StartRemoteSession(self):
        p = subprocess.Popen(["powershell.exe", "cmdkey /generic:{0} /user:{1} /pass: ; mstsc /v:{0}".format(self.GetTypedProperty('ipAddress'), self.GetTypedProperty('sshUsername'))])
        
              
    # starting carmaker needs a little hack since the ssh client from ecu-test can't forward the GUI
    def __StartCarmaker(self):
        scriptPath = self.GetTypedProperty('startScriptPath')
        libPath = self.GetTypedProperty('libPath')
        carMakerProjectPath = self.GetTypedProperty('carMakerBasePath')
        print("Headless active: {}".format(self.GetTypedProperty('Headless')))
        if self.GetTypedProperty('Headless'):
            DisplNr = self.displayNumber
        else:
            DisplNr = self.__DisplayNumberViaSSH()
        
        # CarMaker cannot run headless yet, it needs its GUI. this makes CarMaker able to start on the Linux machine
        # (you need to be logged in on the machine itself, though)
        exportDisplayHack = 'export DISPLAY=:' + str(DisplNr)
        if libPath != "": libPath = libPath+"; "

        print('starting CarMaker on {0}'.format(scriptPath))

        # sending the ssh command itself to start carmaker with given parameters
        
        res = self.JobSendSshCommand('pgrep -u $(whoami) HIL.exe', blocking=True)
        print(res)
        
           
        if (len(res) == 0):
            sshCommand = "python -c 'import socket; s=socket.socket(); s.bind((\"\", 0)); print(s.getsockname()[1]); s.close()'"
            freeport = int(self.JobSendSshCommand(sshCommand, blocking=True)[0].replace("\n",""))
            print(freeport)
            self._CMcmdport = int(freeport)

            sshCommand = '{0}; {1}{2} -cmdport {3} "{4}" >> /dev/null &'.format(exportDisplayHack, libPath, scriptPath, self._CMcmdport,
                                                                      carMakerProjectPath)
            self.JobSendSshCommand(sshCommand, blocking=False)

    # connecting to carmaker with multiple tries to let it start completely
    def __ConnectToCarMaker(self, ipAddress, retries=5):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # TCP Verbindung

        if (self._CMcmdport == 0):
            sshCommand = "ss -l -p -n -t | awk 'BEGIN { \"pgrep -u $(whoami) HIL.exe\" |getline pidn } pidn != 0 && $1 == \"LISTEN\" && $4 ~ /0.0.0.0/ && $6 ~ pidn {print $4}' | cut -d \":\" -f2"            
            result = self.JobSendSshCommand(sshCommand, blocking=True)
            self._CMcmdport = int(result[0].replace("\n",""))

        print('Connecting to CarMaker GUI at {0}:{1}'.format(ipAddress, int(self._CMcmdport)))
        for retryCounter in range(retries):
            try:
                self._socket.connect((ipAddress, int(self._CMcmdport)))
                return None
            except Exception:
                time.sleep(5)
                print('Connection attempt failed, trying again...')

        raise TimeoutError('Could not connect to CarMaker!')

    # tooljob to start recording, does not work as intended: goal was saving everything by just adding one thing
    # each signal itself has to be subscribed so a lib package in ECU-TEST is used to add all needed signals
    def JobEnableRecording(self):
        print('Configure CarMaker to record.')
        self.JobSendTclCommand('OutQuantsDelAll')
        self.JobSendTclCommand('OutQuantsRestoreDefs')
        self.JobSendTclCommand('QuantSubscribe {Time}')
        self.JobSendTclCommand('SaveMode save')

    # quality of life tooljob to transfer the trace to the local machine
    def JobTransferTrace(self, recordingFileName, waitTime, retries=5):
        print('Transfer CarMaker recording to report directory.')

        # getting the folder where the file should be saved
        api = Api()
        reportFolderPath = api.TestEnvironment.ExecutionInfo.LogFolder
        localRecordingFilePath = os.path.join(reportFolderPath, recordingFileName)

        remoteBasePath = self.GetTypedProperty('carMakerBasePath')
        if not remoteBasePath.endswith('/'):
            remoteBasePath += '/'

        # if .erg is to big it is not saved in time -> use a retry counter to check again
        for retryCounter in range(retries):
            relativeRemotePath = self.JobSendTclCommand('GetLastResultFName')
            if relativeRemotePath is not "":
                break
            if waitTime:
                time.sleep(30)
            else:
                time.sleep(2)
            print('File still not saved, trying again...')
        # actually copying the file from the remote side to the local folder
        print('Name of the erg file on linux side: ' + relativeRemotePath)
        remoteFilePath = remoteBasePath + relativeRemotePath
        print('Transfer from {0} to {1}'.format(remoteFilePath, localRecordingFilePath))
        if relativeRemotePath is not "":
            self._sshClient.DownloadFileOrFolder(remoteFilePath,
                                                localRecordingFilePath)  # Copy .erg-File
            self._sshClient.DownloadFileOrFolder(remoteFilePath + '.info',
                                                localRecordingFilePath + '.info')  # Copy .erg.info-File
        # returns the path where the file is now stored
        return localRecordingFilePath

    # explicit tooljob to start CarMaker
    def JobStartCarmaker(self):
        self.__StartCarmaker()
        self.__ConnectToCarMaker(self.GetTypedProperty('ipAddress'))

    # explicit tooljob to stop CarMaker
    def JobStopCarmaker(self):
        self.__StopCarmaker()

    # tooljob to transfer the folder in the given path to the CarMaker machine and into the specified project
    def JobTransferScenarios(self, scenarioFolder, roadFolder):
        # get necessary properties from the testbench configuration
        carMakerProjectPath = self.GetTypedProperty('carMakerBasePath')
        ipAddress = self.GetTypedProperty('ipAddress')
        sshUsername = self.GetTypedProperty('sshUsername')
        privateKeyPath = self.GetTypedProperty('sshKeyPath')
        # now the existing scenario folder is deleted (if it exists)
        cleanupCommandTestrun = "rm -r {0}/Data/TestRun/{1}".format(carMakerProjectPath, scenarioFolder.split("/")[-1])
        print("Removing the existing scenario testrun folder: {0}".format(cleanupCommandTestrun))
        self.JobSendSshCommand(cleanupCommandTestrun)
        cleanupCommandRoad = "rm -r {0}/Data/Road/{1}".format(carMakerProjectPath, roadFolder.split("/")[-1])
        print("Removing the existing scenario road folder: {0}".format(cleanupCommandRoad))
        self.JobSendSshCommand(cleanupCommandRoad)
        # build the command to transfer the scenarios into the specified CarMaker project
        transferCommandTestrun = "scp -i {0} -r {1} {2}@{3}:{4}/Data/TestRun".format(privateKeyPath, scenarioFolder,
                                                                              sshUsername, ipAddress,
                                                                              carMakerProjectPath)
        # execute the scp command
        print("Executing scp command: {0}".format(transferCommandTestrun))
        os.system(transferCommandTestrun)
        # build the next command to transfer the topologies into the specified CarMaker project
        transferCommandRoad = "scp -i {0} -r {1} {2}@{3}:{4}/Data/Road".format(privateKeyPath, roadFolder,
                                                                                     sshUsername, ipAddress,
                                                                                     carMakerProjectPath)
        print("Executing scp command: {0}".format(transferCommandRoad))
        os.system(transferCommandRoad)
        pass

    # quality of life tooljob to transfer a file to the local machine
    def JobTransferFile(self, filePath):
        print('Transfer a file to the report directory.')

        # getting the folder where the file should be saved
        api = Api()
        reportFolderPath = api.TestEnvironment.ExecutionInfo.LogFolder
        localFilePath = os.path.join(reportFolderPath, filePath.split("/")[-1])

        # actually copying the file from the remote side to the local folder
        print('Path of the file on linux side: ' + filePath)
        print('Transfer from {0} to {1}'.format(filePath, localFilePath))
        if filePath is not "":
            self._sshClient.DownloadFileOrFolder(filePath,
                                                localFilePath)  # Copy the file
        # returns the path where the file is now stored
        return localFilePath