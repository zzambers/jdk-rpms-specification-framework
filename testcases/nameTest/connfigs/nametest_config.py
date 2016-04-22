import re

from outputControl import logging_access as la
from utils.core.configuration_specific import JdkConfiguration

JAVA_REGEX8="^java-(1\.[5-8]\.[0-9])-.*-.*-.*\..*.rpm$"
# java-1.X.0 or just 9-whatever1-whatever2-whatever3.whatever4.rpm
# w1 = vendor, w2 = version
# w3 = release, w4 = arch .rpm
CRES_JAVA_REGEXE8 = re.compile(JAVA_REGEX8)

JAVA_REGEX9="^java-([1-9][0-9]*)-.*-.*-.*\..*.rpm$"
CRES_JAVA_REGEXE9 = re.compile(JAVA_REGEX9)

ITW_REGEX="^icedtea-web-.*-.*\..*.rpm$"
CRES_ITW_REGEXE = re.compile(ITW_REGEX)

class ItwRegexCheck(JdkConfiguration):

    def checkRegex(self, name=None):
        self._document("RPM of ITW must match following regex: "+ITW_REGEX)
        la.LoggingAccess().log("ITW special call for checkRegex")
        return CRES_ITW_REGEXE.match(name)


class Jdk9RegexCheck(JdkConfiguration):

    def checkRegex(self, name=None):
        self._document("RPM of newer then 8 (except itw) must match following regex: "+JAVA_REGEX9)
        la.LoggingAccess().log("JDK 9 special call for checkRegex")
        return CRES_JAVA_REGEXE9.match(name)


class OthersRegexCheck(JdkConfiguration):

    def checkRegex(self, name=None):
        self._document("RPM of jdks older then 9 and except itw must match following regex: "+JAVA_REGEX8)
        la.LoggingAccess().log("non ITW jdk older then 9 call for checkRegex")
        return CRES_JAVA_REGEXE8.match(name)
