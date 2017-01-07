# Static-UPnP
Static UPnP responds to upnp search requests with staticlly configures responses.
This can be usefull to make devices available on other subnets, or to make devices available that are not responding to search requests.


# Installation
```
git clone https://github.com/nigelb/Static-UPnP.git
cd Static-UPnP
python setup.py install
```

# Examples

## Chromecast

This example demonstrates how to make a chrome cast available on another subnet.
This demonstration assumes that the Chromecast's IP address is able to be determined by resolving the `Chromecast` hostname.
```
cd Static-UPnP
static_upnp --config-dir examples/Chromecast
```
