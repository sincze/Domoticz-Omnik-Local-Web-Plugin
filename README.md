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

## Parameters

| Parameter | Value |
| :--- | :--- |
| **IP address** | IP of the Inverter eg. 192.168.1.100 |
| **Inverter Username** | Username of the Inverter portal eg. admin |
| **Inverter Password** | Password of the Inverter portal |
| **Protocol** |	For Omnik inverters this is usually HTTP |
| **Debug** | default is 0 |

## Acknowledgements

* Special thanks for all the hard work of [Dnpwwo](https://github.com/dnpwwo), for the examples and fixing the HTTP GET error.
* Domoticz team

