    
########################################################################################
# 	Omnik Inverter Python Plugin for Domoticz                                     	   #
#                                                                                      #
# 	MIT License                                                                        #
#                                                                                      #
#	Copyright (c) 2018 tixi                                                            #
#                                                                                      #
#	Permission is hereby granted, free of charge, to any person obtaining a copy       #
#	of this software and associated documentation files (the "Software"), to deal      #
#	in the Software without restriction, including without limitation the rights       #
#	to use, copy, modify, merge, publish, distribute, sublicense, and/or sell          #
#	copies of the Software, and to permit persons to whom the Software is              #
#	furnished to do so, subject to the following conditions:                           #
#                                                                                      #
#	The above copyright notice and this permission notice shall be included in all     #
#	copies or substantial portions of the Software.                                    #
#                                                                                      #
#	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR         #
#	IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,           #
#	FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE        #
#	AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER             #
#	LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,      #
#	OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE      #
#	SOFTWARE.                                                                          #
#                                                                                      #
#   Author: sincze                                                                     #
#                                                                                      #
#   This plugin will read the status from the running inverter via the web interface.  #
########################################################################################


"""
<plugin key="OmnikLocalWeb" name="Omnik Inverter Local" author="sincze" version="1.0.1" externallink="https://github.com/sincze/Domoticz-Omnik-Local-Web-Plugin">
    <description>
        <h2>Retrieve available Information from Local Omnik Inverter Web Page</h2><br/>
    </description>
    <params>
        <param field="Address" label="IP Address" width="200px" required="true" default="192.168.1.100"/>
        <param field="Username" label="Inverter Username" width="200px" required="true" default="admin"/>
        <param field="Password" label="Inverter Password" width="200px" required="true" password="true"/>
        <param field="Mode1" label="Protocol" width="75px">
            <options>
                <option label="HTTPS" value="443"/>
                <option label="HTTP" value="80"  default="true" />
            </options>
        </param>
        <param field="Mode2" label="Inverter" width="75px">
            <options>
                <option label="webData" value="1" default="true"/>
                <option label="myDeviceArray" value="2" />
            </options>
        </param>
        <param field="Mode6" label="Debug" width="150px">
            <options>
                <option label="None" value="0"  default="true" />
                <option label="Python Only" value="2"/>
                <option label="Basic Debugging" value="62"/>
                <option label="Basic+Messages" value="126"/>
                <option label="Connections Only" value="16"/>
                <option label="Connections+Python" value="18"/>
                <option label="Connections+Queue" value="144"/>
                <option label="All" value="-1"/>
            </options>
        </param>
    </params>
</plugin>
"""

try:
    import Domoticz
    import re               # Needed to extract data from Some JSON result
    local = False
except ImportError:
    local = True
    import fakeDomoticz as Domoticz
    from fakeDomoticz import Devices
    from fakeDomoticz import Parameters


#############################################################################
#                      Domoticz call back functions                         #
#############################################################################

class BasePlugin:
    httpConn = None
    runAgain = 6
    disconnectCount = 0
    sProtocol = "HTTP"
    dataAvailable = False
   
    def __init__(self):
        return

    def onStart(self):
        if Parameters["Mode6"] != "0":
            Domoticz.Debugging(int(Parameters["Mode6"]))
            DumpConfigToLog()

        # Check if devices need to be created
        createDevices()
        
        if (Parameters["Mode1"] == "443"): self.sProtocol = "HTTPS"
        Domoticz.Log("Plugin is started.")
        self.httpConn = Domoticz.Connection(Name=self.sProtocol+" Test", Transport="TCP/IP", Protocol=self.sProtocol, Address=Parameters["Address"], Port=Parameters["Mode1"])
        self.httpConn.Connect()

    def onStop(self):
        Domoticz.Log("onStop - Plugin is stopping.")

    def onConnect(self, Connection, Status, Description):
        if (Status == 0):
            Domoticz.Debug("Inverter connected successfully.")
            sendData = { 'Verb' : 'GET',
                         'URL'  : '/js/status.js',
                         'Headers' : { 'Content-Type': 'text/xml; charset=utf-8', \
                                       'Connection': 'keep-alive', \
                                       'Accept': 'Content-Type: text/html; charset=UTF-8', \
                                       'Host': Parameters["Address"]+":"+Parameters["Mode1"], \
                                       'User-Agent':'Domoticz/1.0' }
                       }
            Connection.Send(sendData)
            UpdateDevice(Unit=3, nValue=1, sValue="On", TimedOut=0)      # Inverter device is on

        else:
            Domoticz.Log("Failed to connect ("+str(Status)+") to: "+Parameters["Address"]+":"+Parameters["Mode1"]+" with error: "+Description)
            UpdateDevice(Unit=3, nValue=0, sValue="Off", TimedOut=0)        # Inverter device is off


    def onMessage(self, Connection, Data):
        DumpHTTPResponseToLog(Data)
        
        strData = Data["Data"].decode("utf-8", "ignore")
       
        Status = int(Data["Status"])
        LogMessage(strData)

        if (Status == 200):
            if (Parameters["Mode2"] == "1"):
                try: 
                    strData = re.search(r'(?<=webData=").*?(?=";)', strData).group(0)               # Search for the beginning of the string and the end
                    self.dataAvailable = True
                except AttributeError:
                    Domoticz.Debug("No datastring found")
            elif (Parameters["Mode2"] == "2"): 
                try: 
                    strData = re.search(r'(?<=myDeviceArray\[0\]=").*?(?=";)', strData).group(0)    # Search for the beginning of the string and the end
                    self.dataAvailable = True
                except AttributeError:
                    Domoticz.Debug("No datastring found")

            if self.dataAvailable:
                strData = strData.split(",")                                            # Split the result string in a list so we can retrieve data
                Domoticz.Debug("Received RAW Inverter Data: "+str(strData))             # Maybe error correction later if len(line.split()) == 11 / we expect 11 items
        
                current=float(strData[5])                                               # Amount in Watt
                daily=float(strData[6])                                                 # Amount in kWh of the day
                total=float(strData[7])                                                 # Total generated kWh needs to be converted to Wh
        
                Domoticz.Debug("Received Data: Current Power: "+str(current)+' W')
                Domoticz.Debug("Received Data: Daily Power: "+str(daily/100)+' kWh')
                Domoticz.Debug("Received Data: Total Power: "+str(total/10)+' kWh')
                sValue=str(current)+";"+str(total*100)                                 # String: Amount in Watt ; Total generated kWh converted to Wh
                Domoticz.Debug("Received Data: String for the sensor is: "+sValue+' !')

                UpdateDevice(Unit=1, nValue=0, sValue=sValue, TimedOut=0)
                UpdateDevice(Unit=2, nValue=0, sValue=current, TimedOut=0)
            else:
                Domoticz.Debug("No data found")

#            if ((self.disconnectCount & 1) == 1):
#                Domoticz.Log("Good Response received from Inverter, Disconnecting.")
#                self.httpConn.Disconnect()
#            else:
#                Domoticz.Log("Good Response received from Inverter, Dropping connection.")
#                self.httpConn = None
#            self.disconnectCount = self.disconnectCount + 1
        elif (Status == 400):
            Domoticz.Error("Inverter returned a Bad Request Error.")
        elif (Status == 500):
            Domoticz.Error("Inverter returned a Server Error.")
        else:
            Domoticz.Error("Inverter returned a status: "+str(Status))

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called for connection to: "+Connection.Address+":"+Connection.Port)

    def onHeartbeat(self):
        if (self.httpConn != None and (self.httpConn.Connecting() or self.httpConn.Connected())):
            Domoticz.Debug("onHeartbeat called, Connection is alive.")
        else:
            self.runAgain = self.runAgain - 1
            if self.runAgain <= 0:
                if (self.httpConn == None):
                    self.httpConn = Domoticz.Connection(Name=self.sProtocol+" Test", Transport="TCP/IP", Protocol=self.sProtocol, Address=Parameters["Address"], Port=Parameters["Mode1"])
                self.httpConn.Connect()
                self.runAgain = 6
            else:
                Domoticz.Debug("onHeartbeat called, run again in "+str(self.runAgain)+" heartbeats.")

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

# Generic helper functions
def LogMessage(Message):
    if Parameters["Mode6"] == "File":
        f = open(Parameters["HomeFolder"]+"http.html","w")
        f.write(Message)
        f.close()
        Domoticz.Log("File written")

def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return

def DumpHTTPResponseToLog(httpDict):
    if isinstance(httpDict, dict):
        Domoticz.Debug("HTTP Details ("+str(len(httpDict))+"):")
        for x in httpDict:
            if isinstance(httpDict[x], dict):
                Domoticz.Debug("--->'"+x+" ("+str(len(httpDict[x]))+"):")
                for y in httpDict[x]:
                    Domoticz.Debug("------->'" + y + "':'" + str(httpDict[x][y]) + "'")
            else:
                Domoticz.Debug("--->'" + x + "':'" + str(httpDict[x]) + "'")

def UpdateDevice(Unit, nValue, sValue, TimedOut=0, AlwaysUpdate=False):
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it 
    if (Unit in Devices):
        if (Devices[Unit].nValue != nValue) or (Devices[Unit].sValue != sValue) or (Devices[Unit].TimedOut != TimedOut):
            Devices[Unit].Update(nValue=nValue, sValue=str(sValue), TimedOut=TimedOut)
            Domoticz.Log("Update "+str(nValue)+":'"+str(sValue)+"' ("+Devices[Unit].Name+")")
    return


#############################################################################
#                       Device specific functions                           #
#############################################################################

def createDevices():

    # Images
    # Check if images are in database
    if "Omnik" not in Images:
        Domoticz.Image("Omnik.zip").Create()
        image = Images["Omnik"].ID # Get id from database
        Domoticz.Log( "Image created. ID: " + str( image ) )

    # Are there any devices?
    ###if len(Devices) != 0:
        # Could be the user deleted some devices, so do nothing
        ###return

    # Give the devices a unique unit number. This makes updating them more easy.
    # UpdateDevice() checks if the device exists before trying to update it.
    if (len(Devices) == 0):
        Domoticz.Device(Name="Inverter (kWh)", Unit=1, TypeName="kWh", Used=1).Create()
        Domoticz.Log("Inverter Device kWh created.")
        Domoticz.Device(Name="Inverter (W)", Unit=2, TypeName="Usage", Used=1).Create()
        Domoticz.Log("Inverter Device (W) created.")
        Domoticz.Device(Name="Inverter Status", Unit=3, TypeName="Switch", Used=1, Image=image).Create()
        Domoticz.Log("Inverter Device (Switch) created.")
        
