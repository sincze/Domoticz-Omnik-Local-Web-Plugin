# Domoticz-Omnik-Local-Web-Plugin
A Domoticz Python Plugin that can read data from the local inverter webinterface.
Some people were unable to use the magic-packet solution due to the serial number, others did not want to retrieve data from the webportal.

![devices](https://github.com/sincze/Domoticz-Omnik-Local-Web-Plugin/blob/master/plugin_preview.png)

## ONLY TESTED FOR Raspberry Pi

With Python version 3.5 & Domoticz V4.11034 (beta)



## Installation

Assuming that domoticz directory is installed in your home directory.

```bash
cd ~/domoticz/plugins
git clone https://github.com/sincze/Domoticz-Omnik-Local-Web-Plugin
cd Domoticz-Omnik-Local-Web-Plugin

# restart domoticz:
sudo /etc/init.d/domoticz.sh restart
```
## Known issues

None at the moment

## Updating

Like other plugins, in the Domoticz-Omnik-Local-Web-Plugin directory:
```bash
git pull
sudo /etc/init.d/domoticz.sh restart
```
## Omnik Variables (ATTENTION)

Omnik inverters store the data in different values. Check ```http://inverter-ip/js/status.js``` to see where yours are.

Example:
```
var webData="NLDN**2017******,NL1-V1.0-0118-4,V2.0-0028,omnik4000tl ,4000,584,345,33734,,4,";
var myDeviceArray=new Array(); myDeviceArray[0]="AANN3020,V5.04Build230,V4.13Build253,Omnik3000tl,3000,1313,685,9429,,1,";
```
In the plugin select "webData" as shown in first line or "myDeviceArray" as in second example. 
![parameters](https://user-images.githubusercontent.com/5776333/63643206-d2466400-c6cb-11e9-90a1-718a0c570fc3.png)

## Parameters

| Parameter | Value |
| :--- | :--- |
| **IP address** | IP of the Inverter eg. 192.168.1.100 |
| **Inverter Username** | Username of the Inverter portal eg. admin |
| **Inverter Password** | Password of the Inverter portal |
| **Protocol** |	For Omnik inverters this is usually HTTP |
| **Inverter** |	Omnik devices store data in different variables, select yours here |
| **Debug** | default is 0 |

## Acknowledgements

* Special thanks for all the hard work of [Dnpwwo](https://github.com/dnpwwo), for the examples and fixing the HTTP GET error.
* menno99 and @smartcontrol19 for testing.
* Domoticz team

