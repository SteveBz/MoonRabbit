# Moon Rabbit CO2 Sensor (Raspberry Pi, scd30, bme280, flask & python)
A Raspberry Pi powered CO2 monitoring station using Python and Flask  

![Alt text](Screenshot%202024-06-08%20091042.png)
![Alt text](Screenshot%202024-06-08%20091122.png)

If starting with blank micro SD card:
## Flash the Micro SD card with the Rapberry Pi Imager 
#Use settings: "Raspberry Pi Zero 2 W", "64 Bit", <inserted drive>

# MoonRabbit setup

## Via a keyboard, mouse and screen through the rpi0 OTG port
Connect your keyboard and mouse to the OTG port via a OTG (On-The-Go) USB hub with a micro USB plug. Connect the monitor to the mini-HDMI port and boot by plugging the power cable in.  

On first start, setup the default user name "pi" and password "RaspberryPi"

Connect to WiFi

Enable Raspberry Pi Connect if you like.

"Skip" OS Update

Restart

### Set up WiFi or Network
If WiFi not yet connected:
Connect to the WiFi using the icon at the top right of the screen.

### Set up SSH & I2C

Menu>Preferences>Praspberry Pi Configuration>Interface>SSH

Menu>Preferences>Praspberry Pi Configuration>Interface>I2C

Menu>Preferences>Praspberry Pi Configuration>Interface>VNC

Menu>Preferences>Raspberry Pi Configuration>Localisation>Locale
Menu>Preferences>Raspberry Pi Configuration>Localisation>Timezone
Menu>Preferences>Raspberry Pi Configuration>Localisation>Keyboard if necessary
Menu>Preferences>Raspberry Pi Configuration>Localisation>WiFi Country

## Via SSH


You'll need the IP address of your raspberry pi. Get it from
```
(venv) pi@raspberrypi:~ $ ifconfig | grep 192
        inet 192.168.1.61  netmask 255.255.255.0  broadcast 192.168.1.255
```
And it's the address of the format 192.168, but not ending 255, so in this case its 192.168.1.61


### Fix swap memory default
The initial default, virtual memory allocation is very small.  You need to expand it to allow many things, such as updating software.

Run swapon command
```
swapon
> NAME      TYPE  SIZE   USED PRIO
> var/swap file 100M 100M   -2
```
Swap Memory is 100 MB
```
sudo nano /etc/dphys-swapfile
```
Change swap size to 1024 MB
```
CONF_SWAPSIZE=1024
```
Use Control-s to save the changes and control-x to exit nano.
Then reboot Moon Rabbit, to apply the changes.
```
sudo reboot
```
Check swapsize again
```
swapon
> NAME      TYPE  SIZE   USED PRIO
> var/swap file 1024M 377.8M   -2
```
Swap size has changed

### Supervisord

Supervisord allows remore control of the software on the Raspberry Pi Zero 2 W from a browser on the same WiFi LAN.

Install Supervisord
```
# Update and upgrade the system packages
sudo apt-get update && sudo apt-get upgrade -y
# Install necessary packages
sudo apt-get install -y supervisor
```

# Edit Supervisor configuration to allow web interface
sudo nano /etc/supervisor/supervisord.conf
Add the following lines to enable the web interface
```
[inet_http_server]
port=*:9001
```
Use Control-s to save the changes and control-x to exit nano.
### Enable hardware interfaces in the Raspberry Pi configuration
IIC or I2C (I-squared-C, or I-two-C), is the interface that links all the sensors to the Raspberry Pi Zero 2 W

sudo nano /boot/firmware/config.txt

```
# Uncomment  or add these lines to enable the hardware interfaces

dtparam=i2c_arm=on
#dtparam=i2s=on
dtparam=spi=on

# Set I2C Clock Speed
dtparam=i2c_arm_baudrate=10000
```
Use Control-s to save the changes and control-x to exit nano.
### Install Moon Rabbit Software
```
# Clone the project repository
git clone https://github.com/SteveBz/MoonRabbit
cd MoonRabbit/
# Set up Python virtual environment and activate it
python3 -m venv venv
. venv/bin/activate
sh install.sh
```

### If you want a hotspot do the following (optional)

Optionally set up an Access Point called "MoonRabbit" with password "raspberry".  It's good practice to name them uniquely if you are collaborating with others. 

```
nmcli connection add type wifi ifname wlan0 con-name MoonRabbit autoconnect no ssid MoonRabbit
nmcli connection modify MoonRabbit 802-11-wireless.mode ap 802-11-wireless.band bg ipv4.method shared
nmcli connection modify MoonRabbit wifi-sec.key-mgmt wpa-psk
nmcli connection modify MoonRabbit wifi-sec.psk "raspberry"
```

### Test Moon Rabbit in a browser
Navigate to a browser, open two tabs and type in the following IP adresesses:
```
<your ip address>:5000
<your ip address>:9001
```
Eg, like this, substituting your address for the example.
```
192.168.1.61:5000
192.168.1.61:9001
```

# MoonRabbit Calibration

Some of the SCD30s come nicely calibrated, some are well out.  Of the two I just one was correct to about 6 ppm, and one was out by 150 ppm.

I'm working on calibration both by using a known concentration source and other means. 

Watch this space.
