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
from config.global_config import get_32b_arch_identifiers_in_scriptlets as get_id


class BasePackages(JdkConfiguration):
    rpms = rc.RuntimeConfig().getRpmList()

    def _get_arch(self):
        return PostinstallScriptTest.instance.getCurrentArch()

    def _generate_masters(self):
        return {}

    def _get_vendor(self):
        return self.rpms.getVendor()

    def _get_version(self):
        v = self.rpms.getMajorVersion()
        if self._get_vendor() == gc.IBM and self.rpms.getMajorVersionSimplified() == "7":
            v = "1.7.0"
        return v

    def _get_masters_arch_copy(self, master):
        master = master + "." + str(get_id(self._get_arch()))
        return master

    def _add_plugin(self, masters):
        # plugin package should be present on intel, ppc and x86_64 arches, or on ppc64 arch when java version is 8
        if (get_id(self._get_arch()) in (gc.getIx86archs() + gc.getPpc32Arch() + gc.getX86_64Arch())) or \
                (get_id(self._get_arch()) in gc.getPower64BeAchs() and self.rpms.getMajorVersionSimplified() == "8"):
            plugin = "libjavaplugin.so"

             # oracle packages do have plugin subpackage with postinstall script, but it does not have any masters
            if self.rpms.getVendor == gc.SUN:
                p = []

            # master name contains arch only on x86_64 arch or when java version is 8 (except Oracle 8 intel arch)
            elif get_id(self._get_arch()) in gc.getX86_64Arch() or\
                    (self.rpms.getMajorVersionSimplified() == "8" and self.rpms.getVendor() != gc.ORACLE) :
                p = [self._get_masters_arch_copy(plugin)]

            else:
                p = [plugin]
            masters["plugin"] = p
        return masters

    def _add_local_policy(self):
        policy = "jce_" + self._get_version() + "_" + self._get_vendor() + "_local_policy"

        # local policy master name does not contain arch only on java version 6 on some specific architectures
        if self.rpms.getMajorVersionSimplified() == "6" and\
           get_id(self._get_arch()) not in (gc.getPower64BeAchs() + gc.getS390xArch() + gc.getX86_64Arch()):

            return policy
        else:
            return self._get_masters_arch_copy(policy)


class CheckPostinstallScript(BasePackages):
    def document_all(self, arg):
        doc = ["Subpackages should contain following masters: "]
        masters = self._generate_masters()
        keys = masters.keys()
        for k in keys:
            whitespace = "    - "
            if self._get_vendor() == gc.ITW:
                name = self._get_vendor() + " " + k
            elif "default" in k:
                name = self.rpms.getMajorPackage() + " " + k
            else:
                name = k
            doc.append(whitespace + name + " package: " + ", ".join(masters[k]))

        self._document("\n".join(doc))

    def _check_post_in_script(self, pkgs):
        passed = []
        failed = []

        # skipped should contain only subpackages that does not have postscript
        skipped = []

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

            PostinstallScriptTest.instance.log("Searching for " + rbu.POSTINSTALL + " in " + os.path.basename(pkg))
            PostinstallScriptTest.instance.log("Checking master for " + os.path.basename(pkg))

            try:
                DefaultMock().install_postscript(pkg)
            except utils.mock.mock_execution_exception.MockExecutionException:
                PostinstallScriptTest.instance.log(rbu.POSTINSTALL + " not found in " + os.path.basename(pkg) +
                                                   " . Test for master and postinstall script was skipped.")
                skipped.append(_subpackage)
                continue

            pkg_masters = DefaultMock().get_masters()

            for m in _default_masters:
                pkg_masters.remove(m)

            actual_masters[_subpackage] = pkg_masters

        PostinstallScriptTest.instance.log("Postinstall not present in packages: " + str(skipped) + ".")
        PostinstallScriptTest.instance.log("Postinstall expected in " + str(len(expected_masters)) +
                                           " : " + ", ".join(expected_masters))
        PostinstallScriptTest.instance.log("Postinstall present in " + str(len(actual_masters)) + " : " +
                                           ", ".join(actual_masters))

        assert set(expected_masters.keys()) == set(actual_masters.keys())

        for subpkg in expected_masters.keys():
            PostinstallScriptTest.instance.log("Expected masters for " + subpkg + " : " +
                                               ", ".join(sorted(expected_masters[subpkg])))
            PostinstallScriptTest.instance.log("Presented masters for " + subpkg + " : " +
                                               ", ".join(sorted(actual_masters[subpkg])))

        for e in expected_masters.keys():
            if sorted(expected_masters[e]) == sorted(actual_masters[e]):
                passed.append(e)
            else:
                failed.append(e)

        PostinstallScriptTest.instance.log("Master test was successful for: " + ", ".join(passed))
        PostinstallScriptTest.instance.log("Master test failed for: " + ", ".join(failed))

        assert(len(failed) == 0)


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


class IcedTeaWeb(CheckPostinstallScript):
    def _generate_masters(self):
        masters = super()._generate_masters()
        masters["default"] = self._get_masters_arch_copy("libjavaplugin.so")
        return masters


class ProprietaryJava6(OpenJdk6):
    def _generate_masters(self):
        masters = super(ProprietaryJava6, self)._generate_masters()
        masters["default"].append(self._add_local_policy())
        masters = self._add_plugin(masters)
        masters.pop("javadoc")
        return masters

class ProprietaryJava7and8Base(ProprietaryJava6):
    def _generate_masters(self):
        masters = super(ProprietaryJava7and8Base, self)._generate_masters()
        masters["devel"].append("java_sdk_" + self._get_version() + "_" + self._get_vendor())
        masters["default"].append("jre_" + self._get_version() + "_" + self._get_vendor())
        return masters


class Oracle7Plugin(ProprietaryJava7and8Base):
    def _generate_masters(self):
        masters = super(Oracle7Plugin, self)._generate_masters()
        masters["javafx"] = ["javafxpackager"]
        return masters


class PostinstallScriptTest(bt.BaseTest):
    instance = None

    def test_contains_postscript(self):
        pkgs = self.getBuild()
        self.csch._check_post_in_script(pkgs)

    def setCSCH(self):
        PostinstallScriptTest.instance = self
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

        elif rpms.getVendor() == gc.ITW:
            self.csch = IcedTeaWeb()
            return

        elif rpms.getVendor() == gc.IBM:
            if rpms.getMajorVersionSimplified() == "6":
                self.csch = ProprietaryJava6()
                return

            elif rpms.getMajorVersionSimplified() == "7":
                self.csch = ProprietaryJava7and8Base()
                return

            elif rpms.getMajorVersionSimplified() == "8":
                self.csch = ProprietaryJava7and8Base()
                return

            else:
                raise ex.UnknownJavaVersionException("Unknown IBM java version.")

        elif rpms.getVendor() == gc.ORACLE or rpms.getVendor() == gc.SUN:
            if rpms.getMajorVersionSimplified() == "6":
                self.csch = ProprietaryJava6()
                return
            elif rpms.getMajorVersionSimplified() == "7":
                self.csch = Oracle7Plugin()
                return
            elif rpms.getMajorVersionSimplified() == "8":
                self.csch = Oracle7Plugin()
                return
            else:
                raise ex.UnknownJavaVersionException("Unknown Oracle java version.")

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

