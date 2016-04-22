import sys

import utils.pkg_name_split as split
import utils.rpmbuild_utils as rpmuts
from utils.core.configuration_specific import JdkConfiguration

import config.runtime_config
import utils.core.base_xtest
from outputControl import logging_access as la


class ITW(JdkConfiguration):
    def checkJreObsolete(self, obsoletes=None):
        self._document("Itw obsolete should be aligned to jres' plugins/javawss")
        # todo - do when doing other plugins
        pass

class Openjdk8Fedora(JdkConfiguration):

    jreRequiredObsolete=[
        "java-1.7.0-openjdk",
        "java-1.5.0-gcj",
        "sinjdoc"
    ]
    def checkJreObsolete(self, obsoletes=None):
        self._document("jre OpenJdk8 in Fedora must obsolate: " +",".join(Openjdk8Fedora.jreRequiredObsolete))
        obsoleteJdk7 = 0
        for obsolete in obsoletes:
            if obsolete in Openjdk8Fedora.jreRequiredObsolete:
                obsoleteJdk7 += 1
        assert obsoleteJdk7 == len(Openjdk8Fedora.jreRequiredObsolete)


class JdkRhel(JdkConfiguration):
    jreExceptionsObsolete = [
        "java-1.5.0-gcj",
        "sinjdoc"
    ]
    def checkJreObsolete(self, obsoletes=None):
        self._document("Jdks in rhel must NOT obsolete anything. Possible exceptions: " +",".join(JdkRhel.jreExceptionsObsolete))
        assert len(set(obsoletes)-set(JdkRhel.jreExceptionsObsolete)) == 0


class ObsolateTest(utils.core.base_xtest.BaseTest):


    def test_jreobsolete(self):
        rpms = self.getBuild()
        for pkg in rpms:
            if (split.get_subpackage_only(pkg) == ''):
                self.csch.checkJreObsolete(rpmuts.listOfVersionlessObsoletes(pkg))

    def setCSCH(self):
        if config.runtime_config.RuntimeConfig().getRpmList().isItw() :
            self.csch = ITW()
            return
        if config.runtime_config.RuntimeConfig().getRpmList().isFedora():
            self.csch = Openjdk8Fedora()
        else:
            self.csch = JdkRhel()


def testAll():
    return ObsolateTest().execute_tests()


def documentAll():
    la.LoggingAccess().stdout("Jdk obsolates are rhel/fedora techpreview/released depndent.")
    return ObsolateTest().execute_special_docs()


def main(argv):
    utils.core.base_xtest.defaultMain(argv, documentAll, testAll)


if __name__ == "__main__":
    main(sys.argv[1:])
