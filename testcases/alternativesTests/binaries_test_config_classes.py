import testcases.alternativesTests.binaries_test_methods as bsm
import utils.pkg_name_split as pkgsplit
import testcases.alternativesTests.binaries_test_paths as btp
import utils.test_constants as tc
import utils.test_utils as tu
import utils.mock.mock_executor as mexe
from outputControl import dom_objects as do

# This script should contain only configuration specific implemetation of the method and overriden methods code.
# Default methods should be always placed in methods or paths files.
# Respect the class naming purpose, inheritance (if possible), and class placement (or this gets very messy)!!!


class OpenJdk6(bsm.BinarySlaveTestMethods):
    def _get_binary_directory(self, name):
        directory = super()._get_binary_directory(name)
        unnecessary_part = directory.split("-")[-1]
        directory = directory.replace("-" + unnecessary_part, "")
        return directory

    def _policytool_binary_subpackages(self):
        return self._get_subpackages_with_binaries()

    def handle_policytool(self, args=None):
        self._document(tc.POLICYTOOL + " is a binary that behaves differently than normal binaries. It has binaries in {} "
                                    "subpackages, but slaves are in {} "
                                    "subpackages.".format(" and ".join(self._policytool_binary_subpackages()),
                                                          " and ".join(self._policytool_slave_subpackages())))
        for subpackage in self._policytool_binary_subpackages():
            try:
                self.installed_binaries[subpackage].remove(tc.POLICYTOOL)
                tu.passed_or_failed(self, True, "")
            except KeyError:
                tu.passed_or_failed(self, False, tc.POLICYTOOL + " binary not present in " + subpackage)
        for subpkg in self._policytool_slave_subpackages():
            try:
                self.installed_slaves[subpkg].remove(tc.POLICYTOOL)
                tu.passed_or_failed(self, True, "")
            except KeyError:
                tu.passed_or_failed(self, False, subpkg + " - subpkg not present.")
            except ValueError:
                tu.passed_or_failed(self, False, tc.POLICYTOOL + " slave not present in " + subpkg)
        return

    def _policytool_slave_subpackages(self):
        return self._get_sdk_subpackage()


class OpenJdk6PowBeArchAndX86(OpenJdk6):
    def _get_binary_directory(self, name):
        return super()._get_binary_directory(name) + "." + self._get_arch()


class OpenJdk7(OpenJdk6):
    def _get_binary_directory(self, name):
        return super(btp.PathTest, self)._get_binary_directory(name)

    def _get_subpackages_with_binaries(self):
        return [tc.DEFAULT, tc.HEADLESS, tc.DEVEL]

    def _policytool_binary_subpackages(self):
        return [tc.DEFAULT, tc.DEVEL]

    def _policytool_slave_subpackages(self):
        return self._get_sdk_subpackage()

    def _get_jre_subpackage(self):
        return [tc.HEADLESS]


class OpenJdk8(OpenJdk7):
    def _policytool_slave_subpackages(self):
        return [tc.HEADLESS]


class OpenJdk8Debug(OpenJdk8):
    def _policytool_binary_subpackages(self):
        return super()._policytool_binary_subpackages() + [tc.DEVEL + tc.get_debug_suffix(), tc.DEFAULT + tc.get_debug_suffix()]

    def _policytool_slave_subpackages(self):
        return super()._policytool_slave_subpackages() + [tc.HEADLESS + tc.get_debug_suffix()]

    def _get_subpackages_with_binaries(self):
        return super()._get_subpackages_with_binaries() + [tc.HEADLESS + tc.get_debug_suffix(), tc.DEVEL + tc.get_debug_suffix(),
                                                           tc.DEFAULT + tc.get_debug_suffix()]

    def _get_jre_subpackage(self):
        return super()._get_jre_subpackage() + [tc.HEADLESS + tc.get_debug_suffix()]

    def _get_sdk_subpackage(self):
        return super()._get_sdk_subpackage() + [tc.DEVEL + tc.get_debug_suffix()]


class OpenJDK8JFX(OpenJdk8Debug):
    def _jfx_check(self, list_of_elements, subpackage, slave_or_bin):
        """
        OpenJFX packaging is broken by design - binaries are in ojfx-devel, links are in headless.
        This is fixed by this method and documented.
        """
        jfx_bins = tc.get_openjfx_binaries()
        for jfxbin in jfx_bins:
            try:
                list_of_elements[subpackage].remove(jfxbin)
                tu.passed_or_failed(self, True, "")
            except ValueError:
                tu.passed_or_failed(self, False, jfxbin + " " + slave_or_bin + " not found in " + subpackage)
        return

    def remove_binaries_without_slaves(self, args=None):
        for subpackage in self.installed_binaries.keys():
            if "openjfx-devel" in subpackage:
                self._jfx_check(self.installed_binaries, subpackage, "binary")
        return


class OpenJdk8NoExports(OpenJdk8):
    # if get_var() == OJDK8 else OpenJDK8JFX if get_var() == OJDK8JFX else OpenJdk8Debug

    def check_exports_slaves(self, args=None):
        return


class OpenJdk8NoExportsDebugJFX(OpenJDK8JFX):

    def check_exports_slaves(self, args=None):
        OpenJdk8NoExports.check_exports_slaves(self)
        return


class OpenJdk8NoExportsDebug(OpenJdk8Debug):
    def check_exports_slaves(self, args=None):
        OpenJdk8NoExports.check_exports_slaves(self)
        return


class OpenJdk9(OpenJdk8):

    # same goes for debug pairs
    DEFAULT_BINARIES = []
    DEVEL_BINARIES = ['appletviewer', 'idlj', 'jar', 'jarsigner', 'javac', 'javadoc', 'javah', 'javap', 'jcmd',
                      'jconsole',
                      'jdb', 'jdeprscan', 'jdeps', 'jhsdb', 'jimage', 'jinfo', 'jlink', 'jmap', 'jmod', 'jps',
                      'jrunscript',
                      'jshell', 'jstack', 'jstat', 'jstatd', 'rmic', 'schemagen', 'serialver', 'wsgen', 'wsimport',
                      'xjc']
    HEADLESS_BINARIES = ["appletviewer", "idlj", "java", "jjs", "jrunscript", "keytool", "orbd", "pack200",
                         "rmid", "rmiregistry", "servertool", "tnameserv", "unpack200"]

    def _get_binaries_as_dict(self):
        return {tc.DEFAULT: self.DEFAULT_BINARIES,
                tc.DEVEL: self.DEVEL_BINARIES,
                tc.HEADLESS: self.HEADLESS_BINARIES,
                tc.DEFAULT + tc.get_debug_suffix(): self.DEFAULT_BINARIES,
                tc.DEVEL + tc.get_debug_suffix(): self.DEVEL_BINARIES,
                tc.HEADLESS + tc.get_debug_suffix(): self.HEADLESS_BINARIES
                }

    def _get_binary_directory_path(self, name):
        return tc.JVM_DIR + "/" + tu.get_32bit_id_in_nvra(pkgsplit.get_nvra(name)) + tc.SDK_DIRECTORY

    def _check_binaries_against_hardcoded_list(self, binaries, subpackage):
        hardcoded_binaries = self._get_binaries_as_dict()
        if not tu.passed_or_failed(self, subpackage in hardcoded_binaries.keys(), "Binaries in unexpected subpackage: "
                                                                                  + subpackage):
            return
        tu.passed_or_failed(self, sorted(binaries) == sorted(hardcoded_binaries[subpackage]),
                                   "Hardcode check: binaries are not as expected. Missing binaries: {}."
                                   " Extra binaries: {}".format(tu.two_lists_diff(hardcoded_binaries[subpackage],
                                                                                  binaries),
                                                                tu.two_lists_diff(binaries,
                                                                                  hardcoded_binaries[subpackage])))
        return

    def check_exports_slaves(self, args=None):
        return

    def all_jre_in_sdk_check(self, args=None):
        return

    def _policytool_slave_subpackages(self):
        return [tc.HEADLESS]

    def _policytool_binary_subpackages(self):
        return [tc.DEFAULT]

    def document_jre_sdk(self, args=None):
        return


class OpenJdk9Debug(OpenJdk9):
    def _get_binary_directory_path(self, name):
        if tc.get_debug_suffix() in name:
            return tc.JVM_DIR + "/" + tu.get_32bit_id_in_nvra(pkgsplit.get_nvra(name)) + tc.get_debug_suffix() + tc.SDK_DIRECTORY
        else:
            return super()._get_binary_directory_path(name)

    def _policytool_binary_subpackages(self):
        return super()._policytool_binary_subpackages() + [tc.DEFAULT + tc.get_debug_suffix()]

    def _policytool_slave_subpackages(self):
        return super()._policytool_slave_subpackages() + [tc.HEADLESS + tc.get_debug_suffix()]

    def _get_subpackages_with_binaries(self):
        return super()._get_subpackages_with_binaries() + [tc.HEADLESS + tc.get_debug_suffix(), tc.DEVEL + tc.get_debug_suffix(),
                                                           tc.DEFAULT + tc.get_debug_suffix()]

    def _get_jre_subpackage(self):
        return super()._get_jre_subpackage() + [tc.HEADLESS + tc.get_debug_suffix()]

    def _get_sdk_subpackage(self):
        return super()._get_sdk_subpackage() + [tc.DEVEL + tc.get_debug_suffix()]


class OpenJdk10(OpenJdk9):
    DEFAULT_BINARIES = []
    DEVEL_BINARIES = ['appletviewer', 'idlj', 'jar', 'jarsigner', 'javac', 'javadoc', 'javap', 'jcmd',
                      'jconsole',
                      'jdb', 'jdeprscan', 'jdeps', 'jhsdb', 'jimage', 'jinfo', 'jlink', 'jmap', 'jmod', 'jps',
                      'jrunscript',
                      'jshell', 'jstack', 'jstat', 'jstatd', 'rmic', 'schemagen', 'serialver', 'wsgen', 'wsimport',
                      'xjc']
    HEADLESS_BINARIES = ["java", "jjs", "keytool", "orbd", "pack200",
                         "rmid", "rmiregistry", "servertool", "tnameserv", "unpack200"]

    def check_java_cgi(self, args=None):
        return

    def check_exports_slaves(self, args=None):
        return OpenJdk8NoExports.check_exports_slaves(self)

    def handle_policytool(self, args=None):
        self._document("From JDK 10, there is no policytool.")
        return

    def _get_subpackages_with_binaries(self):
        subpackages = super()._get_subpackages_with_binaries()
        subpackages.remove(tc.DEFAULT)
        return subpackages


class OpenJdk10Debug(OpenJdk9Debug):
    DEFAULT_BINARIES = []
    DEVEL_BINARIES = ['appletviewer', 'idlj', 'jar', 'jarsigner', 'javac', 'javadoc', 'javap', 'jcmd',
                      'jconsole',
                      'jdb', 'jdeprscan', 'jdeps', 'jhsdb', 'jimage', 'jinfo', 'jlink', 'jmap', 'jmod', 'jps',
                      'jrunscript',
                      'jshell', 'jstack', 'jstat', 'jstatd', 'rmic', 'schemagen', 'serialver', 'wsgen', 'wsimport',
                      'xjc']
    HEADLESS_BINARIES = ["java", "jjs", "keytool", "orbd", "pack200",
                         "rmid", "rmiregistry", "servertool", "tnameserv", "unpack200"]

    def _get_subpackages_with_binaries(self):
        subpackages = super()._get_subpackages_with_binaries()
        subpackages.remove(tc.DEFAULT)
        subpackages.remove(tc.DEFAULT + tc.get_debug_suffix())
        return subpackages

    def handle_policytool(self, args=None):
        self._document("From JDK 10, there is no policytool.")
        return

    def check_java_cgi(self, args=None):
        return

    def check_exports_slaves(self, args=None):
        return OpenJdk8NoExports.check_exports_slaves(self)


class OpenJdk10x64(OpenJdk10Debug):
    """
    This class has to be created due to extra jaotc binary. This binary is available only for x64 architecture Linux.
    It allows AoT compilation, for more info see http://openjdk.java.net/jeps/295
    """
    DEFAULT_BINARIES = []
    DEVEL_BINARIES = ['appletviewer', 'idlj', 'jar', 'jaotc', 'jarsigner', 'javac', 'javadoc', 'javap', 'jcmd',
                      'jconsole',
                      'jdb', 'jdeprscan', 'jdeps', 'jhsdb', 'jimage', 'jinfo', 'jlink', 'jmap', 'jmod', 'jps',
                      'jrunscript',
                      'jshell', 'jstack', 'jstat', 'jstatd', 'rmic', 'schemagen', 'serialver', 'wsgen', 'wsimport',
                      'xjc']
    HEADLESS_BINARIES = ["java", "jjs", "keytool", "pack200",
                         "rmid", "rmiregistry", "tnameserv", "unpack200"]


class OpenJdk11(OpenJdk10):
    DEFAULT_BINARIES = []
    DEVEL_BINARIES = ['jar', 'jarsigner', 'javac', 'javadoc', 'javap', 'jcmd',
                      'jconsole',
                      'jdb', 'jdeprscan', 'jdeps', 'jhsdb', 'jimage', 'jinfo', 'jlink', 'jmap', 'jmod', 'jps',
                      'jrunscript',
                      'jshell', 'jstack', 'jstat', 'jstatd', 'rmic', 'serialver']
    HEADLESS_BINARIES = ["java", "jjs", "keytool", "pack200",
                         "rmid", "rmiregistry", "unpack200"]


class OpenJdk11x64(OpenJdk10x64):
    DEFAULT_BINARIES = []
    DEVEL_BINARIES = ['jar', 'jaotc', 'jarsigner', 'javac', 'javadoc', 'javap', 'jcmd',
                      'jconsole',
                      'jdb', 'jdeprscan', 'jdeps', 'jhsdb', 'jimage', 'jinfo', 'jlink', 'jmap', 'jmod', 'jps',
                      'jrunscript',
                      'jshell', 'jstack', 'jstat', 'jstatd', 'rmic','serialver']
    HEADLESS_BINARIES = ["java", "jjs", "keytool","pack200",
                         "rmid", "rmiregistry", "unpack200"]


class OpenJdk11NoDebugNoJhsdb(OpenJdk10):
    DEFAULT_BINARIES = []
    DEVEL_BINARIES = ['jar', 'jarsigner', 'javac', 'javadoc', 'javap', 'jcmd',
                      'jconsole',
                      'jdb', 'jdeprscan', 'jdeps', 'jimage', 'jinfo', 'jlink', 'jmap', 'jmod', 'jps',
                      'jrunscript',
                      'jshell', 'jstack', 'jstat', 'jstatd', 'rmic', 'serialver']
    HEADLESS_BINARIES = ["java", "jjs", "keytool", "pack200",
                         "rmid", "rmiregistry", "unpack200"]


class OpenJdk11Debug(OpenJdk10Debug):
    DEFAULT_BINARIES = []
    DEVEL_BINARIES = ['jar', 'jarsigner', 'javac', 'javadoc', 'javap', 'jcmd',
                      'jconsole',
                      'jdb', 'jdeprscan', 'jdeps', 'jhsdb', 'jimage', 'jinfo', 'jlink', 'jmap', 'jmod', 'jps',
                      'jrunscript',
                      'jshell', 'jstack', 'jstat', 'jstatd', 'rmic','serialver']
    HEADLESS_BINARIES = ["java", "jjs", "keytool","pack200",
                         "rmid", "rmiregistry", "unpack200"]


class OpenJdk11NoJhsdb(OpenJdk11Debug):
    DEFAULT_BINARIES = []
    DEVEL_BINARIES = ['jar', 'jarsigner', 'javac', 'javadoc', 'javap', 'jcmd',
                      'jconsole',
                      'jdb', 'jdeprscan', 'jdeps', 'jimage', 'jinfo', 'jlink', 'jmap', 'jmod', 'jps',
                      'jrunscript',
                      'jshell', 'jstack', 'jstat', 'jstatd', 'rmic', 'serialver']
    HEADLESS_BINARIES = ["java", "jjs", "keytool", "pack200",
                         "rmid", "rmiregistry", "unpack200"]


class OpenJdk12(OpenJdk11):
    DEFAULT_BINARIES = []
    DEVEL_BINARIES = ['jar', 'jarsigner', 'javac', 'javadoc', 'javap', 'jcmd',
                      'jconsole',
                      'jdb', 'jdeprscan', 'jdeps', 'jhsdb', 'jimage', 'jinfo', 'jlink', 'jmap', 'jmod', 'jps',
                      'jrunscript',
                      'jshell', 'jstack', 'jstat', 'jstatd', 'rmic', 'serialver', 'jfr']
    HEADLESS_BINARIES = ["java", "jjs", "keytool", "pack200",
                         "rmid", "rmiregistry", "unpack200"]

    def remove_binaries_without_slaves(self, args=None):
        subpackage = self._get_jre_subpackage()[0]
        if "devel" in subpackage:
            self.installed_binaries[subpackage].remove("jfr")


class OpenJdk12x64(OpenJdk11x64):
    DEFAULT_BINARIES = []
    DEVEL_BINARIES = ['jar', 'jaotc', 'jarsigner', 'javac', 'javadoc', 'javap', 'jcmd',
                      'jconsole',
                      'jdb', 'jdeprscan', 'jdeps', 'jhsdb', 'jimage', 'jinfo', 'jlink', 'jmap', 'jmod', 'jps',
                      'jrunscript',
                      'jshell', 'jstack', 'jstat', 'jstatd', 'rmic', 'serialver', 'jfr']
    HEADLESS_BINARIES = ["java", "jjs", "keytool","pack200",
                         "rmid", "rmiregistry", "unpack200"]

    def remove_binaries_without_slaves(self, args=None):
        subpackage = self._get_jre_subpackage()[0]
        if "devel" in subpackage:
            self.installed_binaries[subpackage].remove("jfr")


class OpenJdk12NoDebugNoJhsdb(OpenJdk11):
    DEFAULT_BINARIES = []
    DEVEL_BINARIES = ['jar', 'jarsigner', 'javac', 'javadoc', 'javap', 'jcmd',
                      'jconsole',
                      'jdb', 'jdeprscan', 'jdeps', 'jimage', 'jinfo', 'jlink', 'jmap', 'jmod', 'jps',
                      'jrunscript',
                      'jshell', 'jstack', 'jstat', 'jstatd', 'rmic', 'serialver', 'jfr']
    HEADLESS_BINARIES = ["java", "jjs", "keytool", "pack200",
                         "rmid", "rmiregistry", "unpack200"]

    def remove_binaries_without_slaves(self, args=None):
        subpackage = self._get_jre_subpackage()[0]
        if "devel" in subpackage:
            self.installed_binaries[subpackage].remove("jfr")


class OpenJdk12Debug(OpenJdk11Debug):
    DEFAULT_BINARIES = []
    DEVEL_BINARIES = ['jar', 'jarsigner', 'javac', 'javadoc', 'javap', 'jcmd',
                      'jconsole',
                      'jdb', 'jdeprscan', 'jdeps', 'jhsdb', 'jimage', 'jinfo', 'jlink', 'jmap', 'jmod', 'jps',
                      'jrunscript',
                      'jshell', 'jstack', 'jstat', 'jstatd', 'rmic','serialver', 'jfr']
    HEADLESS_BINARIES = ["java", "jjs", "keytool","pack200",
                         "rmid", "rmiregistry", "unpack200"]

    def remove_binaries_without_slaves(self, args=None):
        subpackage = self._get_jre_subpackage()[0]
        if "devel" in subpackage:
            self.installed_binaries[subpackage].remove("jfr")


class OpenJdk12NoJhsdb(OpenJdk12Debug):
    DEFAULT_BINARIES = []
    DEVEL_BINARIES = ['jar', 'jarsigner', 'javac', 'javadoc', 'javap', 'jcmd',
                      'jconsole',
                      'jdb', 'jdeprscan', 'jdeps', 'jimage', 'jinfo', 'jlink', 'jmap', 'jmod', 'jps',
                      'jrunscript',
                      'jshell', 'jstack', 'jstat', 'jstatd', 'rmic', 'serialver', 'jfr']
    HEADLESS_BINARIES = ["java", "jjs", "keytool", "pack200",
                         "rmid", "rmiregistry", "unpack200"]


class Ibm(bsm.BinarySlaveTestMethods):
    def _policytool_slave_subpackages(self):
        return ["headless"]

    def _policytool_binary_subpackages(self):
        return [tc.DEFAULT, tc.DEVEL]

    def handle_policytool(self, args=None):
        OpenJdk6.handle_policytool(self)
        return
    # classic and j9vm are folders, not binaries
    def _remove_excludes(self):
        subpackage = self._get_jre_subpackage()[0]
        excludes = tc.get_ibm_folders()
        try:
            for e in excludes:
                self.installed_binaries[subpackage].remove(e)
        except ValueError:
            pass
        finally:
            return

    def remove_binaries_without_slaves(self, args=None):
        subpackage = self._get_jre_subpackage()[0]
        excludes = tc.get_ibm_k_bins() + tc.get_ibm_ikey_bins()
        self._document(" and ".join(excludes) + " are binaries present in {} subpackage. They are not in {} subpackage "
                                                "and have no slaves in alternatives.".format(subpackage,
                                                                                           self._get_sdk_subpackage()[0]))
        for e in excludes:
            try:
                self.installed_binaries[subpackage].remove(e)
                tu.passed_or_failed(self, True, "")
            except ValueError:
                tu.passed_or_failed(self, False, e + " not present in " + subpackage + " binaries.")
        return

    def handle_plugin_binaries(self, args=None):
        plugin_binaries = tc.get_plugin_binaries()
        ssubpackages = self._get_jre_subpackage()
        bsubpackages = self._get_jre_subpackage() + self._get_sdk_subpackage()
        self._document("{} are binaries replacing {} subpackage. They are present in {} subpackages and their slaves"
                       " are in {} subpackages.".format(" and ".join(plugin_binaries), tc.PLUGIN,
                                                        " and ".join(bsubpackages)
                                                        , "".join(ssubpackages)))
        self._check_plugin_binaries_and_slaves_are_present(bsubpackages, ssubpackages)
        return

    def _check_plugin_binaries_and_slaves_are_present(self, bsubpackages, ssubpackages):
        for pbinary in tc.get_plugin_binaries():
            for subpackage in bsubpackages:
                tu.passed_or_failed(self, pbinary in self.installed_binaries[subpackage], "Missing plugin binary " + pbinary + " in " + subpackage)
            for subpackage in ssubpackages:
                tu.passed_or_failed(self, pbinary not in self.installed_slaves[subpackage], "Missing plugin slave " + pbinary + " in " + subpackage)

    def _check_plugin_bins_and_slaves_are_not_present(self, subpackages):
        for pbinary in tc.get_plugin_binaries():
            for subpackage in subpackages:
                if not tu.passed_or_failed(self, pbinary not in self.installed_binaries[subpackage],
                                           pbinary + " should not be in " + subpackage +
                                           " because this subpackage must not contain any plugin binaries."):
                    self.installed_binaries[subpackage].remove(pbinary)
                if not tu.passed_or_failed(self, pbinary not in self.installed_slaves[subpackage],
                                           pbinary + " should not be in " + subpackage +
                                           " because this subpackage must not contain plugin slaves."):
                    self.installed_slaves[subpackage].remove(pbinary)
        return


class Ibm390Architectures(Ibm):
    def handle_plugin_binaries(self, args=None):
        plugin_binaries = tc.get_plugin_binaries()
        self._document("{} are not present in binaries in any subpackage. This architecture "
                       "also has no {} subpackages.".format(" and ".join(plugin_binaries), tc.PLUGIN))
        self._check_plugin_bins_and_slaves_are_not_present(self._get_subpackages_with_binaries())
        return


class IbmWithPluginSubpackage(Ibm):
    def _get_checked_masters(self):
        return super()._get_checked_masters() + [tc.LIBJAVAPLUGIN]

    def _get_subpackages_with_binaries(self):
        return super()._get_subpackages_with_binaries() + [tc.PLUGIN]

    def handle_plugin_binaries(self, args=None):
        plugin_binaries = tc.get_plugin_binaries()
        subpackages_without_pbins = self._get_jre_subpackage() + self._get_sdk_subpackage()
        self._document("{} are binaries related with {}. They are present and have slaves only in {} "
                       "subpackages.".format(" and ".join(plugin_binaries), tc.PLUGIN, tc.PLUGIN))
        self._check_plugin_bins_and_slaves_are_not_present(subpackages_without_pbins)
        self._check_plugin_binaries_and_slaves_are_present([tc.PLUGIN], [tc.PLUGIN])
        return


class IbmArchMasterPlugin(IbmWithPluginSubpackage):
    def _get_checked_masters(self):
        return [tc.JAVA, tc.JAVAC, tc.LIBJAVAPLUGIN + "." + self._get_arch()]


class Ibm8Rhel8(IbmArchMasterPlugin):

    def _get_exports_slaves_jre(self):
        return []

    def _get_exports_slaves_sdk(self):
        return []

    def check_java_cgi(self, args=None):
        return

    def _get_jre_subpackage(self):
        return [tc.HEADLESS]

    def _check_plugin_binaries_and_slaves_are_present(self, bsubpackages, ssubpackages):
        return

class Ibm8Rhel8S390X(Ibm390Architectures):
    def _get_exports_slaves_jre(self):
        return []

    def _get_exports_slaves_sdk(self):
        return []

    def check_java_cgi(self, args=None):
        return

    def _get_jre_subpackage(self):
        return [tc.HEADLESS]

    def _check_plugin_binaries_and_slaves_are_present(self, bsubpackages, ssubpackages):
        return


class Oracle6(IbmWithPluginSubpackage):
    def _get_binary_directory(self, name):
        path = self._get_32bit_id_in_nvra(pkgsplit.get_nvra(name))
        release = path.split("-")[-1]
        path = path.replace("-" + release, "")
        return path

    def _remove_excludes(self):
        return

    def remove_binaries_without_slaves(self, args=None):
        return

    def handle_plugin_binaries(self, args=None):
        plugin_binaries = tc.get_plugin_binaries()
        self._document("{} are no longer present in binaries in any subpackage.".format(" and ".join(plugin_binaries)))
        self._check_plugin_bins_and_slaves_are_not_present(self._get_subpackages_with_binaries())
        return

    def _get_subpackages_with_binaries(self):
        return bsm.BinarySlaveTestMethods(self.binaries_test)._get_subpackages_with_binaries()


class OracleNoArchPlugin(Oracle6):
    def _get_checked_masters(self):
        return [tc.JAVA, tc.JAVAC, tc.LIBNSSCKBI_SO]


class Oracle6ArchPlugin(Oracle6):
    def _get_checked_masters(self):
        return [tc.JAVA, tc.JAVAC, tc.LIBNSSCKBI_SO + "." + self._get_arch()]

    def _get_binary_directory(self, name):
        return super()._get_binary_directory(name) + "." + self._get_arch()


class Oracle7(Oracle6ArchPlugin):
    def _remove_excludes(self):
        exclude_list = tc.oracle_exclude_list()
        for exclude in exclude_list:
            self._document("{} is not a binary. It is present in {} subpackages binaries. It has "
                           "no slave in alternatives.".format(exclude, tc.DEVEL))
            try:
                self.installed_binaries[tc.DEVEL].remove(exclude)
                tu.passed_or_failed(self, True, "")
            except ValueError:
                tu.passed_or_failed(self, False, exclude + " not present in " + tc.DEVEL)
        return

    def _get_subpackages_with_binaries(self):
        subpackages = bsm.BinarySlaveTestMethods(self.binaries_test)._get_subpackages_with_binaries()
        subpackages.append(tc.JAVAFX)
        return subpackages

    def _get_checked_masters(self):
        masters = super()._get_checked_masters()
        masters.append(tc.JAVAFXPACKAGER)
        return masters

    def _get_binary_directory(self, name):
        return btp.PathTest(self.binaries_test)._get_binary_directory(name)


class Oracle8(Oracle7):
    def handle_plugin_binaries(self, args=None):
        return IbmWithPluginSubpackage(self.binaries_test).handle_plugin_binaries()


class Itw(bsm.BinarySlaveTestMethods):
    def check_java_cgi(self, args=None):
        return

    def all_jre_in_sdk_check(self, args=None):
        return

    def check_exports_slaves(self, args=None):
        self._document("ITW has no exports slaves.")
        return

    def _get_subpackages_with_binaries(self):
        return [tc.DEFAULT]

    def handle_plugin_binaries(self, args=None):
        self._document("ITW replaces plugin package for OpenJDK")
        return

    def document_jre_sdk(self, args=None):
        return

    def doc_extra_binary(self, args=None):
        self._document(tc.ITWEB_SETTINGS + " is an iced-tea binary. Its slave is " + tc.CONTROL_PANEL)

    def check_subdirectory_slaves(self, args=None):
        return

    def _get_all_binaries_and_slaves(self, pkgs):
        mexe.DefaultMock().provideCleanUsefullRoot()
        original_binaries = mexe.DefaultMock().execute_ls(tc.USR_BIN)[0].split("\n")
        installed_binaries, installed_slaves = super()._get_all_binaries_and_slaves(pkgs)
        installed_binaries = self._remove_links_from_usr_bin(installed_binaries)
        for subpackage in installed_binaries.keys():
            all_binaries = installed_binaries[subpackage]
            installed_binaries[subpackage] = tu.two_lists_diff(all_binaries, original_binaries)

        settings = tc.ITWEB_SETTINGS
        bins = []
        for b in installed_binaries[tc.DEFAULT]:
            bins.append(b.replace(".itweb", ""))
        installed_binaries[tc.DEFAULT] = bins
        try:
            installed_binaries[tc.DEFAULT].append(tc.CONTROL_PANEL)
            tu.passed_or_failed(self, True, "")
        except ValueError:
            tu.passed_or_failed(self, False, settings + " binary not in " + tc.DEFAULT + " subpackage")
        return installed_binaries, installed_slaves
    
    def _get_binary_directory_path(self, name):
        return tc.USR_BIN

    def _get_checked_masters(self):
        return [tc.JAVAWS + "." + tu.validate_arch_for_rpms(self._get_arch())]

    def _remove_links_from_usr_bin(self, installed_binaries):
        # perhaps doc
        links = []
        for b in installed_binaries[tc.DEFAULT]:
            if ".itweb" not in b:
                links.append(b)
        for l in links:
            installed_binaries[tc.DEFAULT].remove(l)
        return installed_binaries
