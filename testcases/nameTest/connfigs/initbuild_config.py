import re

import config.global_config as gc
import outputControl.logging_access as la
from utils.core.configuration_specific import JdkConfiguration



class ItwVersionCheck(JdkConfiguration):

    def checkMajorVersionSimplified(self, version=None):
        self._document("IcedTea-Web do not have any version contained in name.")
        la.LoggingAccess().log("ITW special call for checkMajorVersionSimplified")
        return version == gc.ITW

    def checkMajorVersion(self, version=None):
        self.checkMajorVersionSimplified(version)

    def checkPrefix(self, version=None):
        self._document("IcedTea-Web do not have any prefix-based name. It is just " + gc.ITW + ".")
        la.LoggingAccess().log("ITW special call for checkPrefix")
        return version == gc.ITW

    def checkVendor(self, vendor=None):
        self._document("IcedTea-Web do not have any vendor in name. It is just " + gc.ITW + ".")
        la.LoggingAccess().log("ITW special call for checkVendor")
        return vendor == gc.ITW


class OthersVersionCheck(JdkConfiguration):

    def checkMajorVersionSimplified(self, version=None):
        self._document(
            "All jdsk (except icedtea-web) have major version in name. eg: java-1.8.0-openjdk or java-9-oracle."
            " For legacy JDK (like jdk 1.6.0 or 1.7.1) the major version is included as middle number."
            " For modern jdks (jdk 9+)  the major version is just plain number. Eg.: java-9-ibm."
            " The extracted middle number *is* number")
        la.LoggingAccess().log("non itw call for checkMajorVersionSimplified")
        return re.compile("[0-9]+").match(version) and int(version) > 0

    def checkMajorVersion(self, version=None):
        self._document("The version string in middle of package name is one of: " + ",".join(
            gc.LIST_OF_POSSIBLE_VERSIONS_WITHOUT_ITW))
        return version in gc.LIST_OF_POSSIBLE_VERSIONS_WITHOUT_ITW

    def checkPrefix(self, version=None):
        self._document("prefix of each java package is " + gc.JAVA_STRING + ".")
        la.LoggingAccess().log("non itw call for checkPrefix")
        return version == gc.JAVA_STRING

    def checkVendor(self, vendor=None):
        self._document("The vendor string, suffix of package name is one of: " + ",".join(
            gc.LIST_OF_POSSIBLE_VENDORS_WITHOUT_ITW))
        la.LoggingAccess().log("non itw call for checkVendor")
        return vendor in gc.LIST_OF_POSSIBLE_VENDORS_WITHOUT_ITW