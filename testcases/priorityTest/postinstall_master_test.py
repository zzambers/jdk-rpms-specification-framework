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
from config.global_config import get_32b_arch_identifiers_in_scriptlets as get_id
from utils.test_utils import rename_default_subpkg

JAVAFXPACKAGER = "javafxpackager"
JAVAFX = "javafx"
JAVADOCZIP = 'javadoczip'
JAVADOCDIR = 'javadocdir'
JAVADOC_ZIP = "javadoc-zip"
JAVADOC = "javadoc"
DEVEL = "devel"
DEFAULT = "default"
DEBUG_SUFFIX = "-debug"
HEADLESS = "headless"
PLUGIN = "plugin"
LIBJAVAPLUGIN = "libjavaplugin.so"


class BasePackages(JdkConfiguration):
    rpms = rc.RuntimeConfig().getRpmList()

    def _get_arch(self):
        return PostinstallScriptTest.instance.getCurrentArch()

    def _generate_masters(self):
        return {}

    def _get_vendor(self):
        return self.rpms.getVendor()

    def _get_version(self):
        return self.rpms.getMajorVersion()

    def _get_masters_arch_copy(self, master):
        master = master + "." + str(get_id(self._get_arch()))
        return master

    def _add_plugin(self):
        return [LIBJAVAPLUGIN]


class CheckPostinstallScript(BasePackages):
    def document_all(self, arg):
        doc = ["Subpackages should contain following masters: "]
        masters = self._generate_masters()
        for k in masters.keys():
            whitespace = "    - "
            if self._get_vendor() == gc.ITW:
                name = self._get_vendor() + " " + k
            elif DEFAULT in k:
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
            _subpackage = rename_default_subpkg(utils.pkg_name_split.get_subpackage_only(os.path.basename(pkg)))

            PostinstallScriptTest.instance.log("Searching for " + rbu.POSTINSTALL + " in " + os.path.basename(pkg))
            PostinstallScriptTest.instance.log("Checking master for " + os.path.basename(pkg))

            if not DefaultMock().postinstall_exception_checked(pkg):
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
        masters[DEFAULT] = ['java', 'jre_' + self._get_vendor(), 'jre_' + self._get_version()]
        masters[JAVADOC] = [JAVADOCDIR]
        masters[DEVEL] = ['javac', 'java_sdk_' + self._get_vendor(), 'java_sdk_' + self._get_version()]
        return masters


class OpenJdk7(OpenJdk6):
    def _generate_masters(self):
        masters = super(OpenJdk7, self)._generate_masters()
        masters[HEADLESS] = masters[DEFAULT] + ["jre_" + self._get_version() + "_" + self._get_vendor()]
        masters[DEFAULT] = []
        masters[DEVEL].append("java_sdk_" + self._get_version() + "_" + self._get_vendor())
        return masters


class OpenJdk8OtherArchs(OpenJdk7):
    def _generate_masters(self):
        masters = super(OpenJdk8OtherArchs, self)._generate_masters()
        masters[JAVADOC + DEBUG_SUFFIX] = [JAVADOCDIR]
        masters[JAVADOC_ZIP] = [JAVADOCZIP]
        masters[JAVADOC_ZIP + DEBUG_SUFFIX] = [JAVADOCZIP]
        return masters


class OpenJdk8Intel(OpenJdk8OtherArchs):
    def _generate_masters(self):
        masters = super(OpenJdk8Intel, self)._generate_masters()
        masters[DEVEL + DEBUG_SUFFIX] = masters[DEVEL]
        masters[HEADLESS + DEBUG_SUFFIX] = masters[HEADLESS]
        masters[JAVADOC + DEBUG_SUFFIX] = masters[JAVADOC]
        masters[DEFAULT + DEBUG_SUFFIX] = []
        return masters


class IcedTeaWeb(CheckPostinstallScript):
    def _generate_masters(self):
        masters = super()._generate_masters()
        masters[DEFAULT] = [self._get_masters_arch_copy(LIBJAVAPLUGIN)]
        return masters


class ProprietaryJava6(OpenJdk6):
    def _generate_masters(self):
        masters = super(ProprietaryJava6, self)._generate_masters()
        masters[DEFAULT].append(self._add_local_policy())
        masters[PLUGIN] = [self._add_plugin()]
        masters.pop(JAVADOC)
        return masters

    def _add_plugin(self):
        return LIBJAVAPLUGIN

    def _add_local_policy(self):
        return "jce_" + self._get_version() + "_" + self._get_vendor() + "_local_policy"

# s390x, x86, ppc64
class ProprietaryJava6WithArch(ProprietaryJava6):
    def _add_local_policy(self):
        return self._get_masters_arch_copy(super()._add_local_policy())


class Oracle6(ProprietaryJava6):
    def _add_plugin(self):
        # oracle packages do have plugin subpackage with postinstall script, but it does not have any masters
        return []


class Oracle6WithArch(Oracle6):
    def _add_local_policy(self):
        return self._get_masters_arch_copy(super()._add_local_policy())


class ProprietaryJava7and8Base(ProprietaryJava6WithArch):
    def _generate_masters(self):
        masters = super(ProprietaryJava7and8Base, self)._generate_masters()
        masters[DEVEL].append("java_sdk_" + self._get_version() + "_" + self._get_vendor())
        masters[DEFAULT].append("jre_" + self._get_version() + "_" + self._get_vendor())
        return masters


class Ibm7(ProprietaryJava7and8Base):
    def _get_version(self):
        return "1.7.0"

class Ibm7x86(Ibm7):
    def _add_plugin(self):
        return self._get_masters_arch_copy(LIBJAVAPLUGIN)


class Ibm7WithoutPlugin(Ibm7):
    def _generate_masters(self):
        masters = super()._generate_masters()
        masters.pop(PLUGIN)
        return masters


class Oracle7(ProprietaryJava7and8Base):
    def _generate_masters(self):
        masters = super(Oracle7, self)._generate_masters()
        masters[JAVAFX] = [JAVAFXPACKAGER]
        return masters


class Ibm8(ProprietaryJava7and8Base):
    def _add_plugin(self):
        return self._get_masters_arch_copy(LIBJAVAPLUGIN)


class Ibm8WithoutPlugin(Ibm8):
    def _generate_masters(self):
        masters = super()._generate_masters()
        masters.pop(PLUGIN)
        return masters


class Oracle8x86(Oracle7):
    def _add_plugin(self):
        return self._get_masters_arch_copy(LIBJAVAPLUGIN)


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
            if rpms.getMajorVersionSimplified() == "7":
                if self.getCurrentArch() in gc.getS390xArch() + gc.getS390Arch() + \
                        gc.getPower64LeAchs() + gc.getPower64BeAchs():
                    self.csch = Ibm7WithoutPlugin()
                    return
                elif self.getCurrentArch() in gc.getX86_64Arch():
                    self.csch = Ibm7x86()
                    return
                else:
                    self.csch = Ibm7()
                    return
            elif rpms.getMajorVersionSimplified() == "8":
                if self.getCurrentArch() in gc.getS390xArch() + gc.getS390Arch() + gc.getPower64LeAchs():
                    self.csch = Ibm8WithoutPlugin()
                    return
                else:
                    self.csch = Ibm8()
                    return

            else:
                raise ex.UnknownJavaVersionException("Unknown IBM java version.")

        elif rpms.getVendor() == gc.ORACLE or rpms.getVendor() == gc.SUN:
            if rpms.getMajorVersionSimplified() == "6":
                if self.getCurrentArch() in gc.getS390xArch() + gc.getX86_64Arch() + gc.getPower64BeAchs():
                    self.csch = Oracle6WithArch()
                    return
                else:
                    self.csch = Oracle6()
                    return
            elif rpms.getMajorVersionSimplified() == "7":
                self.csch = Oracle7()
                return
            elif rpms.getMajorVersionSimplified() == "8":
                if self.getCurrentArch() in gc.getX86_64Arch():
                    self.csch = Oracle8x86()
                    return
                else:
                    self.csch = Oracle7()
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

