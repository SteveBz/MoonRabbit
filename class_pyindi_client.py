# for logging
import sys
import time
import logging

# import the PyIndi module
import PyIndi


# The IndiClient class which inherits from the module PyIndi.BaseClient class
# Note that all INDI constants are accessible from the module as PyIndi.CONSTANTNAME
class IndiClient(PyIndi.BaseClient):
    def __init__(self):
        super(IndiClient, self).__init__()
        self.logger = logging.getLogger("IndiClient")
        self.logger.info("creating an instance of IndiClient")

    def newDevice(self, d):
        """Emmited when a new device is created from INDI server."""
        self.logger.info(f"new device {d.getDeviceName()}")

    def removeDevice(self, d):
        """Emmited when a device is deleted from INDI server."""
        self.logger.info(f"remove device {d.getDeviceName()}")

    def newProperty(self, p):
        """Emmited when a new property is created for an INDI driver."""
        self.logger.info(
            f"new property {p.getName()} as {p.getTypeAsString()} for device {p.getDeviceName()}"
        )

    def updateProperty(self, p):
        """Emmited when a new property value arrives from INDI server."""
        self.logger.info(
            f"update property {p.getName()} as {p.getTypeAsString()} for device {p.getDeviceName()}"
        )

    def removeProperty(self, p):
        """Emmited when a property is deleted for an INDI driver."""
        self.logger.info(
            f"remove property {p.getName()} as {p.getTypeAsString()} for device {p.getDeviceName()}"
        )

    def newMessage(self, d, m):
        """Emmited when a new message arrives from INDI server."""
        self.logger.info(f"new Message {d.messageQueue(m)}")

    def serverConnected(self):
        """Emmited when the server is connected."""
        self.logger.info(f"Server connected ({self.getHost()}:{self.getPort()})")

    def serverDisconnected(self, code):
        """Emmited when the server gets disconnected."""
        self.logger.info(
            f"Server disconnected (exit code = {code},{self.getHost()}:{self.getPort()})"
        )
