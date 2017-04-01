# Static-UPnP
Static UPnP responds to upnp search requests with staticlly configures responses.
This can be usefull to make devices available on other subnets, or to make devices available that are not responding to search requests.


# Installation
```
git clone https://github.com/nigelb/Static-UPnP.git
cd Static-UPnP
pip install .
````
Or if you want static_upnp to automatically get the IP addresses to bind to from your network interfaces:
```
pip install .[interfaces]
```

# Examples

## Chromecast

This example demonstrates how to make a chrome cast available on another subnet.
This demonstration assumes that the Chromecast's IP address is able to be determined by resolving the `Chromecast` hostname.
```
cd Static-UPnP
static_upnp --config-dir examples/Chromecast
```
If the Chromecast's IP address cannot be resolved you can set it by changing [examples/Chromecast/StaticUPnP_StaticServices.py](/nigelb/Static-UPnP/blob/master/examples/Chromecast/StaticUPnP_StaticServices.py#L60) line 60. For example if the Chromecast's IP address is 10.0.0.20 then change line 60 from:

```python
chromecast_ip = socket.gethostbyname_ex("Chromecast")[2][0]
```
to:

```python
chromecast_ip = "10.0.0.20",
```
