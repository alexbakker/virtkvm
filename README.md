# virtkvm

__virtkvm__ is the poor man's KVM switch for libvirt and VFIO users. It can
attach/detach a set of USB devices to/from a libvirt virtual machine and switch
monitor inputs through DDC/CI. The toggle mechanism can be triggered with a
simple request to its HTTP server.

## Setup

After installing the package, you should create a configuration file to
specify the libvirt settings, HTTP server settings, USB device list and display
list. An example configuration file is provided here:
[example_config.yaml](example_config.yaml).

Virtkvm depends on [ddcutil](https://www.ddcutil.com/) to do the switching of
the display inputs, so that utility needs to be available in PATH.

## Usage

Virtkvm should run on the host machine and can be started as follows: 

```
usage: virtkvm [-h] --config CONFIG

The poor man's KVM switch for libvirt and VFIO users

optional arguments:
  -h, --help       show this help message and exit
  --config CONFIG  the YAML configuration file (default: None)
```

### Toggling the KVM

The KVM can be toggled with an HTTP request:

```sh
curl -X POST -H 'Content-Type: application/json' -H 'X-Secret: xxxxxxxxxxxxxxxx' -d '{"to": "host"}' http://192.168.100.1:5001/switch
```

On Windows, Powershell can be used to send a request to switch the KVM back to
the host:

```powershell
Invoke-RestMethod -Method POST -Uri "http://192.168.100.1:5000/switch" -Headers @{"X-Secret" = "xxxxxxxxxxxxxxxx"} -Body "{`"to`": `"host`"}" -ContentType "application/json"
```

You could also add this as a shortcut to your AutoHotkey script. The following
will toggle the KVM when Win+Shift+~ is pressed:

```autohotkey
#+~::
Run, PowerShell -WindowStyle Hidden "Invoke-RestMethod -Method POST -Uri 'http://192.168.100.1:5000/switch' @{'X-Secret' = 'xxxxxxxxxxxxxxxx'} -Body '{\"to\": \"host\"}' -ContentType 'application/json'"
```
