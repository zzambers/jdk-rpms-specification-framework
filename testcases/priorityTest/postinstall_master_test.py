from outputControl import logging_access as la
import sys
import utils.core.base_xtest as bt
from utils.core.configuration_specific import JdkConfiguration
import utils.rpmbuild_utils as rbu
import os
import config.global_config as gc
import config.runtime_config as rc
import utils.core.unknown_java_exception as ex
import utils.pkg_name_split as pkgsplit
import utils
from utils.mock.mock_executor import DefaultMock
from utils.mock.mock_execution_exception import MockExecutionException


class BasePackages(JdkConfiguration):

    # skipped should contain only packages that does not have postscript
    skipped = []

    rpms = rc.RuntimeConfig().getRpmList()

    def _generate_masters(self):
        return {}

    def _get_vendor(self):
        return self.rpms.getVendor()

    def _get_version(self):
        return self.rpms.getMajorVersion()


class CheckPostinstallScript(BasePackages):
    def document_all(self, arg):
        doc = ["Subpackages should contain following masters: "]
        masters = self._generate_masters()
        keys = masters.keys()
        for k in keys:
            whitespace = "    - "
            if "default" in k:
                name = self.rpms.getMajorPackage() + " " + k
            else:
                name = k
            doc.append(whitespace + name + " package: " + ", ".join(masters[k]))

        self._document("\n".join(doc))

    def _check_post_in_script(self, pkgs):
        _default_masters = DefaultMock().get_default_masters()

        # correct set of masters
        expected_masters = self._generate_masters()

        # masters installed in mock
        actual_masters = {}

        for pkg in pkgs:
            _subpackage = utils.pkg_name_split.get_subpackage_only(os.path.basename(pkg))

            if _subpackage == "":
                _subpackage = "default"
            elif _subpackage == "debug":
                _subpackage = "default-debug"

            PostinstallScriptTest.logs.log("searching for " + rbu.POSTINSTALL + " in " + os.path.basename(pkg))
            PostinstallScriptTest.logs.log("Checking master for " + os.path.basename(pkg))

            try:
                DefaultMock()._install_scriptlet(pkg, rbu.POSTINSTALL)
            except utils.mock.mock_execution_exception.MockExecutionException:
                PostinstallScriptTest.logs.log(rbu.POSTINSTALL + " not found in " + os.path.basename(pkg) +
                                               " . Test for master and postinstall script was skipped.")
                self.skipped.append(_subpackage)
                continue

            pkg_masters = DefaultMock().get_masters()

            for m in _default_masters:
                pkg_masters.remove(m)

            actual_masters[_subpackage] = pkg_masters

        PostinstallScriptTest.logs.log("Postinstall not present in packages: " + str(self.skipped) + ".")
        PostinstallScriptTest.logs.log("Postinstall expected in " + str(len(expected_masters)) + " : " + ", ".join(expected_masters))
        PostinstallScriptTest.logs.log("Postinstall present in " + str(len(actual_masters)) + " : " + ", ".join(actual_masters))
        
        assert set(expected_masters.keys()) == set(actual_masters.keys())

        for subpkg in expected_masters.keys():
            PostinstallScriptTest.logs.log("Expected masters for " + subpkg + " : " +
                                           ", ".join(sorted(expected_masters[subpkg])))
            PostinstallScriptTest.logs.log("Presented masters for " + subpkg + " : " +
                                           ", ".join(sorted(actual_masters[subpkg])))

        assert set(expected_masters) == set(actual_masters)

        PostinstallScriptTest.logs.log("Master and postinstall script test was successful.")


class OpenJdk6(CheckPostinstallScript):
    def _generate_masters(self):
        masters = super(OpenJdk6, self)._generate_masters()
        masters["default"] = ['java', 'jre_' + self._get_vendor(), 'jre_' + self._get_version()]
        masters["javadoc"] = ['javadocdir']
        masters["devel"] = ['javac', 'java_sdk_' + self._get_vendor(), 'java_sdk_' + self._get_version()]
        return masters


class OpenJdk7(OpenJdk6):
    def _generate_masters(self):
        masters = super(OpenJdk7, self)._generate_masters()
        masters["headless"] = masters["default"] + ["jre_" + self._get_version() + "_" + self._get_vendor()]
        masters["default"] = []
        masters["devel"].append("java_sdk_" + self._get_version() + "_" + self._get_vendor())
        return masters


class OpenJdk8OtherArchs(OpenJdk7):
    def _generate_masters(self):
        masters = super(OpenJdk8OtherArchs, self)._generate_masters()
        masters["javadoc-debug"] = ['javadocdir']
        masters["javadoc-zip"] = ['javadoczip']
        masters["javadoc-zip-debug"] = ['javadoczip']
        return masters


class OpenJdk8Intel(OpenJdk8OtherArchs):
    def _generate_masters(self):
        masters = super(OpenJdk8Intel, self)._generate_masters()
        masters["devel-debug"] = masters["devel"]
        masters["headless-debug"] = masters["headless"]
        masters["javadoc-debug"] = masters["javadoc"]
        masters["default-debug"] = []
        return masters


class PostinstallScriptTest(bt.BaseTest):
    logs = None

    def test_contains_postscript(self):
        pkgs = self.getBuild()
        self.csch._check_post_in_script(pkgs)

    def setCSCH(self):
        PostinstallScriptTest.logs = self
        rpms = rc.RuntimeConfig().getRpmList()
        self.log("Checking post_script and master for " + rpms.getVendor())

        if rpms.getVendor() == gc.OPENJDK:
            if rpms.getMajorVersionSimplified() == "6":
                self.csch = OpenJdk6()
                return
            elif rpms.getMajorVersionSimplified() == "7":
                self.csch = OpenJdk7()
                return
            elif rpms.getMajorVersionSimplified() == "8":
                if self.getCurrentArch() in gc.getIx86archs() + gc.getX86_64Arch():
                    self.csch = OpenJdk8Intel()
                    return
                else:
                    self.csch = OpenJdk8OtherArchs()
                    return
            else:
                raise ex.UnknownJavaVersionException("Unknown JDK version.")
        else:
            raise ex.UnknownJavaVersionException("Unknown platform, java was not identified.")


def testAll():
    return PostinstallScriptTest().execute_tests()


def documentAll():
    la.LoggingAccess().stdout("Postinstall scriptlet and master conventions:")
    return PostinstallScriptTest().execute_special_docs()


def main(argv):
    utils.core.base_xtest.defaultMain(argv, documentAll, testAll)
    return PostinstallScriptTest().execute_special_docs()

if __name__ == "__main__":
    main(sys.argv[1:])

