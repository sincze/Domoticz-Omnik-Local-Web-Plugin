########################################################################################
# 	Omnik Inverter Python Plugin for Domoticz                             	       #
#                                                                                      #
# 	MIT License                                                                    #
#                                                                                      #
#	Copyright (c) 2018 tixi                                                        #
#                                                                                      #
#	Permission is hereby granted, free of charge, to any person obtaining a copy   #
#	of this software and associated documentation files (the "Software"), to deal  #
#	in the Software without restriction, including without limitation the rights   #
#	to use, copy, modify, merge, publish, distribute, sublicense, and/or sell      #
#	copies of the Software, and to permit persons to whom the Software is          #
#	furnished to do so, subject to the following conditions:                       #
#                                                                                      #
#	The above copyright notice and this permission notice shall be included in all #
#	copies or substantial portions of the Software.                                #
#                                                                                      #
#	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR     #
#	IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,       #
#	FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE    #
#	AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER         #
#	LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,  #
#	OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE  #
#	SOFTWARE.                                                                      #
#                                                                                      #
#   Author: sincze                                                                     #
#                                                                                      #
#   This plugin will read the status from the running inverter via the web interface.  #
#                                                                                      #
#   V1.0.2 21-11-20 Fix issue for Domoticz 2022.2                                      #
#   V2.0.0 03-09-23 Multi Thread version                                               #
#                                                                                      #
########################################################################################

"""
<plugin key="OmnikLocalWeb2" name="Omnik Local Inverter Plugin" author="sincze" version="2.0.0" externallink="https://github.com/sincze/Domoticz-Omnik-Local-Web-Plugin">
    <description>
        <h2>Retrieve available Information from Local Omnik Inverter Web Page</h2><br/>
    </description>
    <params>
        <param field="Address" label="IP Address" width="200px" required="true" default="192.168.1.100"/>
        <param field="Mode1" label="Protocol" width="75px">
            <options>
                <option label="HTTPS" value="https"/>
                <option label="HTTP" value="http" default="true" />
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
    import threading
    import re               # Needed to extract data from Some result
    import requests
    local = False

except ImportError:
    local = True
    import fakeDomoticz as Domoticz
    from fakeDomoticz import Devices
    from fakeDomoticz import Parameters
    import threading
    import requests
    import re               # Needed to extract data from Some result


class BasePlugin:

    runAgain = 6
    url = ""
    dataAvailable = False
    inverterResponded = False

    def __init__(self):
        self.threads = []

    def onStart(self):
        if Parameters["Mode6"] == "-1":
            Domoticz.Debugging(1)
            Domoticz.Log("Debugger started, use '0.0.0.0 5678' to connect")
            import debugpy
            self.debugging=True
            self.debugpy=debugpy
            debugpy.listen(("0.0.0.0", 5678))
##            debugpy.wait_for_client()
            time.sleep(10)
            debugpy.breakpoint()
        else:
            Domoticz.Log("onStart called")
        if Parameters["Mode6"] != "0":
            Domoticz.Debugging(int(Parameters["Mode6"]))
            DumpConfigToLog()

        createDevices()

        self.url = Parameters["Mode1"] + "://" + Parameters["Address"] + "/js/status.js"
        Domoticz.Debug(f"Fetching URL {self.url}")

        thread = threading.Thread(target=self.fetch_url, args=(self.url,))
        self.threads.append(thread)
        thread.start()

    def onStop(self):
        Domoticz.Log("Plugin stopped")

    def fetch_url(self, url):
        try:
            response = requests.get(url)
            self.inverterResponded = True
            UpdateDevice(Unit=3, nValue=1, sValue="On", TimedOut=0)      # Inverter device is on
        except:
            self.inverterResponded = False
            UpdateDevice(Unit=3, nValue=1, sValue="Off", TimedOut=0)
            Domoticz.Debug(f"No Response from inverter {url}")

        try:
            if ( response.ok ) and ( self.inverterResponded ):
                strData = str(response.content)
                LogMessage(strData)

                if (Parameters["Mode2"] == "1"):
                    try:
                        strData = re.search(r'(?<=webData=").*?(?=";)', strData).group(0)               # Search for the beginning of>
                        self.dataAvailable = True
                    except AttributeError:
                        Domoticz.Debug("No datastring found")
                elif (Parameters["Mode2"] == "2"):
                    try:
                        strData = re.search(r'(?<=myDeviceArray\[0\]=").*?(?=";)', strData).group(0)    # Search for the beginning of>
                        self.dataAvailable = True
                    except AttributeError:
                        Domoticz.Debug("No datastring found")
            else:
                Domoticz.Log(f"Switching Received HTTP {response.status_code}")
        except:
            Domoticz.Log(f"Server did not respond!")

        if self.dataAvailable:
            strData = strData.split(",")                                         # Split the result string in a list so we can retrieve data
            Domoticz.Debug(f"Received RAW Inverter Data: {strData}")             # Maybe error correction later if len(line.split()) == 11 / we expect 11 items

            current=float(strData[5])                                            # Amount in Watt
            daily=float(strData[6])                                              # Amount in kWh of the day
            total=float(strData[7])                                              # Total generated kWh needs to be converted to Wh

            Domoticz.Debug(f"Received Data: Current Power: {current} W, Daily Power: {daily/100} kWh, Total Power: {total/10} kWh")

            sValue=f"{current};{(total*100)}" 
            Domoticz.Debug(f"Received Data: String for the sensor is: {sValue} !")
            UpdateDevice(Unit=1, nValue=0, sValue=sValue, TimedOut=0)
            UpdateDevice(Unit=2, nValue=0, sValue=current, TimedOut=0)
            UpdateDevice(Unit=4, nValue=0, sValue=f"{total*100}", TimedOut=0)

            if current == 0:
                UpdateDevice(Unit=3, nValue=1, sValue="Off", TimedOut=0)      # Inverter device is on
                Domoticz.Log(f"Switching Off")
        else:
            Domoticz.Debug("No Inverter data found")

    def onHeartbeat(self):
        # Check if all threads have completed
        #if all(not thread.is_alive() for thread in self.threads):
        #    Domoticz.Log("All threads have completed.")
        #    self.stop()
        self.runAgain = self.runAgain - 1
        if self.runAgain <= 0:
            Domoticz.Debug(f"onHeartbeat Fetching URL {self.url}")
            thread = threading.Thread(target=self.fetch_url, args=(self.url,))
            self.threads.append(thread)
            thread.start()
            self.runAgain = 6
        else:
            Domoticz.Debug(f"onHeartbeat called, run again in {self.runAgain} heartbeats.")

    def stop(self):
        # Cleanup and stop the plugin
        for thread in self.threads:
            thread.join()
        self.stop()

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

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
            Devices[Unit].Update(nValue=nValue, sValue=f"{sValue}", TimedOut=TimedOut)
            Domoticz.Log(f"Update {nValue};{sValue} {Devices[Unit].Name}")

    return


#############################################################################
#                     Deviceplugin  specific functions                      #
#############################################################################

def createDevices():
    # Images
    # Check if images are in database
    if "Omnik" not in Images:
        Domoticz.Image("Omnik.zip").Create()
        image = Images["Omnik"].ID # Get id from database
        Domoticz.Log(f"Image created. ID: {image}" )

    # Give the devices a unique unit number. This makes updating them more easy.
    # UpdateDevice() checks if the device exists before trying to update it.
    if (len(Devices) == 0):
        Domoticz.Device(Name="Inverter (kWh)", Unit=1, TypeName="kWh", Used=1, Image=image).Create()
        Domoticz.Log("Inverter Device kWh created.")
        Domoticz.Device(Name="Inverter (W)", Unit=2, TypeName="Usage", Used=1, Image=image).Create()
        Domoticz.Log("Inverter Device (W) created.")
        Domoticz.Device(Name="Inverter Status", Unit=3, TypeName="Switch", Used=1, Image=image).Create()
        Domoticz.Log("Inverter Device (Switch) created.")
        Domoticz.Device(Name="Inverter Generate", Unit=4, Type=113, Subtype=0, Used=1, Image=image).Create()
        Domoticz.Log("Inverter Device (Generated) created.")
