import sys
import outputControl.logging_access as la
import config.global_config as gc
import config.runtime_config as rc
import utils.process_utils as pu
import utils.pkg_name_split as pkgsplit
import utils.core.base_xtest as bt

###
import utils.core.configuration_specific as cs
import utils.test_constants as tc
import utils.pkg_name_split as ns
import utils.test_utils as tu
import utils.mock.mock_executor as mexe
from outputControl import dom_objects as do


class NonITW(cs.JdkConfiguration):
    def __init__(self, this):
        super().__init__()
        self.rpms = rc.RuntimeConfig().getRpmList()
        self.this=this
        self.passed = 0
        self.failed = 0

    def _get_artificial_provides(self, filename):
            output, error, res = pu.executeShell("rpm -q --provides rpms/" + filename)
            lines = output.split("\n")
            provides_dict = {}
            for line in lines:
                if "=" in line and "debuginfo(build" not in line:
                    actual_line = line.split("=")
                    provides_dict[actual_line[0].strip()] = actual_line[1].strip()
            return provides_dict

    def check_artificial_provides(self, this):
        files = self.rpms.files
        documentation = ""
        files = [x.replace("rpms/", "") for x in files]
        if not self.documenting:
            files = [x for x in files if tu.validate_arch_for_rpms(this.current_arch) == ns.get_arch(x)]
        for filename in files:
            filename = filename.split("/")[-1]
            expected_provides = self._get_expected_artificial_provides(filename)
            documentation += make_rpm_readable(filename) + " should have these and no other provides: " + ", ".join(list(expected_provides.keys())) + "\n"
            if self.documenting:
                continue
            actual_provides = self._get_artificial_provides(filename)
            missing_provides = []
            for provide in expected_provides:
                if not tu.passed_or_failed(self, provide in actual_provides,
                                           make_rpm_readable(filename) + " is missing provide: " + provide):
                    missing_provides.append(provide)
                else:
                    tu.passed_or_failed(self, expected_provides[provide] == actual_provides[provide],
                                        "wrong version for provide " + provide + " in " + make_rpm_readable(filename))
                    actual_provides.pop(provide)
            if missing_provides:
                la.LoggingAccess().log("missing provide in {}: ".format(make_rpm_readable(filename)) +
                                       str(list(missing_provides)), la.Verbosity.TEST)
            tu.passed_or_failed(self, len(actual_provides) == 0, "found extra provides in rpm " + make_rpm_readable(filename) + ": " +
                                       str(list(actual_provides.keys())))
        self._document(documentation)
        return self.passed, self.failed

    def _get_expected_artificial_provides(self, filename):
        name, java_ver, vendor, pkg, version, end = ns._hyphen_split(filename)
        arch = tu.validate_arch_for_provides(ns.get_arch(filename))
        # have to look at this with Jvanek/list through provides myself in future
        if "src" in end:
            provides = Empty(name, java_ver, vendor, pkg, version, end, arch, filename)
        elif tu.is_rolling(filename):
            if "debuginfo" in pkg or "debugsource" in pkg:
                provides = DebugInfoRolling(name, java_ver, vendor, pkg, version, end, arch, filename)
            elif "headless" in pkg or (not tu.has_headless_pkg() and self._is_pkg_default(pkg)):
                provides = HeadlessRolling(name, java_ver, vendor, pkg, version, end, arch, filename)
            elif self._is_pkg_default(pkg):
                provides = JreRolling(name, java_ver, vendor, pkg, version, end, arch, filename)
            elif "devel" in pkg:
                provides = SdkRolling(name, java_ver, vendor, pkg, version, end, arch, filename)
            elif "javadoc-zip" in pkg:
                provides = JavaDocZipRolling(name, java_ver, vendor, pkg, version, end, arch, filename)
            elif "javadoc" in pkg:
                provides = JavaDocRolling(name, java_ver, vendor, pkg, version, end, arch, filename)
            else:
                provides = DefaultRolling(name, java_ver, vendor, pkg, version, end, arch, filename)
        elif "debuginfo" in pkg or "debugsource" in pkg or "jdbc" in pkg:
            provides = DebugInfo(name, java_ver, vendor, pkg, version, end, arch, filename)
        elif java_ver not in tc.TECHPREVIEWS:
            if "openjfx" in pkg:
                provides = OpenJfx(name, java_ver, vendor, pkg, version, end, arch, filename)
            elif "headless" in pkg or (not tu.has_headless_pkg() and self._is_pkg_default(pkg)):
                provides = Headless(name, java_ver, vendor, pkg, version, end, arch, filename)
            elif self._is_pkg_default(pkg):
                provides = Jre(name, java_ver, vendor, pkg, version, end, arch, filename)
            elif "devel" in pkg:
                provides = Sdk(name, java_ver, vendor, pkg, version, end, arch, filename)
            elif "javadoc-zip" in pkg:
                provides = JavaDocZip(name, java_ver, vendor, pkg, version, end, arch, filename)
            elif "javadoc" in pkg:
                provides = JavaDoc(name, java_ver, vendor, pkg, version, end, arch, filename)
            elif "webstart" in pkg:
                provides = Webstart(name, java_ver, vendor, pkg, version, end, arch, filename)
            else:
                provides = Default(name, java_ver, vendor, pkg, version, end, arch, filename)
        else:
            if "headless" in pkg or (not tu.has_headless_pkg() and self._is_pkg_default(pkg)):
                provides = HeadlessTechPreview(name, java_ver, vendor, pkg, version, end, arch, filename)
            elif self._is_pkg_default(pkg):
                provides = JreTechPreview(name, java_ver, vendor, pkg, version, end, arch, filename)
            elif "devel" in pkg:
                provides = SdkTechPreview(name, java_ver, vendor, pkg, version, end, arch, filename)
            elif "javadoc-zip" in pkg:
                provides = JavaDocZipTechPreview(name, java_ver, vendor, pkg, version, end, arch, filename)
            elif "javadoc" in pkg:
                provides = JavaDocTechPreview(name, java_ver, vendor, pkg, version, end, arch, filename)
            elif "static" in pkg:
                provides = DebugInfo(name, java_ver, vendor, pkg, version, end, arch, filename)
            else:
                provides = DefaultTechPreview(name, java_ver, vendor, pkg, version, end, arch, filename)
        return provides.get_expected_artificial_provides()

    def cross_check_artificial_provides(self, this):
        files = self.rpms.files
        self._document("according to Jvanek every provide should be provided only once per set of rpms with exception "
                       + "of javadoc-zip having common provides with javadoc")
        files = [x.replace("rpms/", "") for x in files if tu.validate_arch_for_rpms(this.current_arch) in x]
        if files:
            la.LoggingAccess().log("  Testing VersionRelease: " + ns.get_version_full(files[0]), la.Verbosity.TEST)
        for i in range(len(files) - 1):
            actual_provides = self._get_artificial_provides(files[i])
            for j in range(i + 1, len(files)):
                if ns.get_arch(files[i]) == ns.get_arch(files[j]):
                    if ("zip" in files[i] and "javadoc" in files[j]) or ("zip" in files[j] and "javadoc" in files[i]):
                        continue
                    compared_provides = self._get_artificial_provides(files[j])
                    provides_intersection = [provide for provide in actual_provides if provide in compared_provides]
                    tu.passed_or_failed(self, not(len(provides_intersection)),
                                               "{} and {} have common provides: {}".format(make_rpm_readable(files[i]),
                                                                                           make_rpm_readable(files[j]),
                                                                                           ", ".join(provides_intersection)))
        return

    def ghost_test(self, this):
        if self.documenting:
            self._document("Currently the ghosts are hardcoded as the only ghost is \"classes.jsa\" file. This will probably change with ojdk11 as system jdk.")
            return 0, 0
        files = self.rpms.files
        files = [x.replace("rpms/", "") for x in files]
        files = [x for x in files if tu.validate_arch_for_rpms(this.current_arch) == ns.get_arch(x)]
        return self._check_ghosts(files)

    def _check_ghosts(self, files):
        expected_ghosts = {}
        actual_ghosts = {}
        for file in files:
            pkg = tu.rename_default_subpkg(ns.get_subpackage_only(file))
            expected_ghosts[pkg] = self._get_expected_ghosts_for_file(file)
            actual_ghosts[pkg] = self._get_actual_ghosts(file)
        for key in expected_ghosts.keys():
            current_expected = expected_ghosts[key]
            current_actual = actual_ghosts[key]
            unexpected_ghosts = current_actual.difference(current_expected)
            missing_ghosts = current_expected.difference(current_actual)
            if not not current_expected:
                la.LoggingAccess().log("Ghosts expected in " + key + " package: " + str(current_expected))
            if not not current_actual:
                la.LoggingAccess().log("Ghosts acutally in " + key + " package: " + str(current_actual))
            tu.passed_or_failed(self, not unexpected_ghosts, "Unexpected (in rpm -q but not in alternatives) ghosts found: " + str(unexpected_ghosts), "No extra ghosts.")
            tu.passed_or_failed(self, not missing_ghosts, "Ghosts missing (in alternatives but not in rpm -q): " + str(missing_ghosts), "No missing ghosts.")
        return self.passed, self.failed

    def _get_actual_ghosts(self, filename):
        output, error, res = pu.executeShell("rpm -q -l rpms/" + filename)
        allfiles = set(output.split("\n"))
        output, error, res = pu.executeShell("rpm -q -l --noghost rpms/" + filename)
        withoutghosts = set(output.split("\n"))
        ghosts = allfiles.difference(withoutghosts)
        return ghosts

    def _get_expected_ghosts_for_file(self, file):
        return set()

    #doesnt work, needs further investigation once ojdk11 is system jdk
    def _get_expected_ghosts2(self, files):
        mexe.DefaultMock().provideCleanUsefullRoot()
        expected_ghosts = {}
        all_masters_so_far = set(mexe.DefaultMock().get_default_masters())
        for filename in files:
            pkg = tu.rename_default_subpkg(ns.get_subpackage_only(filename))
            mexe.DefaultMock().postinstall_exception_checked("rpms/" + filename)
            current_masters = set(mexe.DefaultMock().get_default_masters())
            expected_ghosts[pkg] = current_masters.difference(all_masters_so_far)
            for master in expected_ghosts[pkg]:
                o, i = mexe.DefaultMock().executeCommand(["ll", master])
                la.LoggingAccess().log(o)
            all_masters_so_far.union(current_masters)
        return expected_ghosts


    def _is_pkg_default(self, pkg):
        return pkg == "" or pkg == "debug" or pkg == "slowdebug"

    GHOSTS = {tc.DEVEL:[], tc.HEADLESS:[], tc.JAVADOC:[], tc.JAVADOCZIP:[]}

###


class ITWeb(NonITW):
    def _get_expected_artificial_provides(self, filename):
        name, java_ver, vendor, pkg, version, end = ns._hyphen_split(filename)
        arch = tu.validate_arch_for_provides(ns.get_arch(filename))
        if pkg == "":
            provides = ITWebDefault(name, java_ver, vendor, pkg, version, end, arch, filename)
        else:
            provides = ITWebNonDefault(name, java_ver, vendor, pkg, version, end, arch, filename)
        return provides.get_expected_artificial_provides()

    def _get_artificial_provides(self, filename):
        provides = super(ITWeb, self)._get_artificial_provides(filename)
        toremove = [x for x in provides.keys() if x.startswith("mvn")]
        for x in toremove:
            provides.pop(x)
        return provides


class Ojdk8(NonITW):
    pass


class Ojdk8JIT(Ojdk8):
    def _get_expected_ghosts_for_file(self, file):
        ghosts = super(Ojdk8JIT, self)._get_expected_ghosts_for_file(file)
        arch = ns.get_arch(file)
        if "headless" in file and not "info" in file:
            nvra = ns.get_nvra(file)
            archinstall = ns.get_arch_install(file)
            debugsuffix = ""
            for suffix in tc.get_debug_suffixes():
                if suffix in file:
                    debugsuffix = suffix
                    break
            if arch == "i686":
                nvra = nvra.replace(arch, archinstall)
            ghosts.add("/usr/lib/jvm/" + nvra + debugsuffix + "/jre/lib/" + archinstall + "/client/classes.jsa")
            ghosts.add("/usr/lib/jvm/" + nvra + debugsuffix + "/jre/lib/" + archinstall + "/server/classes.jsa")
        return ghosts


class Ojdk11(NonITW):
    pass


class Ojdk11JIT(Ojdk11):
    def _get_expected_ghosts_for_file(self, file):
        ghosts = super(Ojdk11JIT, self)._get_expected_ghosts_for_file(file)
        arch = ns.get_arch(file)
        if "headless" in file and not "info" in file:
            nvra = ns.get_nvra(file)
            archinstall = ns.get_arch_install(file)
            debugsuffix = ""
            for suffix in tc.get_debug_suffixes():
                if suffix in file:
                    debugsuffix = suffix
                    break
            if arch == "i686" or arch == "armv7hl":
                nvra = nvra.replace(arch, archinstall)
            ghosts.add("/usr/lib/jvm/" + nvra + debugsuffix + "/lib/server/classes.jsa")
        return ghosts


class Ojdklatest(Ojdk11):
    pass


class OjdklatestJIT(Ojdklatest):
    def _get_expected_ghosts_for_file(self, file):
        ghosts = super(Ojdklatest, self)._get_expected_ghosts_for_file(file)
        arch = ns.get_arch(file)
        if "headless" in file and not "info" in file:
            nvra = ns.get_nvra(file)
            archinstall = ns.get_arch_install(file)
            debugsuffix = ""
            for suffix in tc.get_debug_suffixes():
                if suffix in file:
                    debugsuffix = suffix
                    break
            if arch == "i686" or arch == "armv7hl":
                nvra = nvra.replace(arch, archinstall)
            ghosts.add("/usr/lib/jvm/" + nvra + debugsuffix + "/lib/server/classes.jsa")
            ghosts.add("/usr/lib/jvm/" + nvra + debugsuffix + "/lib/client/classes.jsa")
        return ghosts

class ProvidesTest(bt.BaseTest):
    """ Framework class that runs the testcase. """
    instance=None

    def __init__(self):
        super().__init__()
        self.list_of_failed_tests = []

    def test_artificial_provides(self):
        self.csch.cross_check_artificial_provides(self)
        self.csch.check_artificial_provides(self)
        return self.csch.ghost_test(self)

    def setCSCH(self):
        ProvidesTest.instance=self
        rpms = rc.RuntimeConfig().getRpmList()
        if rc.RuntimeConfig().getRpmList().getJava() == gc.ITW:
            self.log("Set ItwVersionCheck")
            #set ITW when finished
            self.csch = ITWeb(ProvidesTest.instance)
        else:
            arch = self.getCurrentArch()
            if int(rpms.getMajorVersionSimplified()) == 8:
                if tc.is_arch_jitarch(arch) and "ppc" not in arch:
                    self.csch = Ojdk8JIT(ProvidesTest.instance)
                    return
                else:
                    self.csch = Ojdk8(ProvidesTest.instance)
                    return
            if int(rpms.getMajorVersionSimplified()) == 11:
                if (arch == "armv7hl" or tc.is_arch_jitarch(arch)) and "ppc" not in arch:
                    self.csch = Ojdk11JIT(ProvidesTest.instance)
                    return
                else:
                    self.csch = Ojdk11(ProvidesTest.instance)
                    return
            if int(rpms.getMajorVersionSimplified()) > 11:
                if (arch in ["armv7hl", "s390x"] or tc.is_arch_jitarch(arch)) and "ppc" not in arch:
                    self.csch = OjdklatestJIT(ProvidesTest.instance)
                    return
                else:
                    self.csch = Ojdklatest(ProvidesTest.instance)

            self.log("Set OthersVersionCheck")
            self.csch = NonITW(ProvidesTest.instance)


class Empty:
    def __init__(self, name, java_ver, vendor, pkg, version, end, arch, filename):
        self.expected_provides = {}

    def get_expected_artificial_provides(self):
        return self.expected_provides

    def convert_to_rolling(self):
        keys = list(self.expected_provides.keys())
        for key in keys:
            print(key)
            splitted = key.split("-", 2)
            if len(splitted) > 2 and splitted[1].isdigit():
                self.expected_provides[splitted[0] + "-" + ("openjdk" if "openjdk" not in splitted[2] else "") +
                                       (("-" + splitted[2]) if (len(splitted) > 2) else "")] = self.expected_provides.pop(key)

class DebugInfo(Empty):
    def __init__(self, name, java_ver, vendor, pkg, version, end, arch, filename):
        super(DebugInfo, self).__init__(name, java_ver, vendor, pkg, version, end, arch, filename)
        self.expected_provides[("{}-{}-{}".format(name, java_ver, vendor) + (("-" + pkg) if pkg else pkg) +
                                "({})".format(arch))] = ns.get_version_full(filename)
        self.expected_provides[("{}-{}-{}".format(name, java_ver, vendor) + (("-" + pkg) if pkg else pkg))] = \
            ns.get_version_full(filename)


class DefaultTechPreview(DebugInfo):
    def __init__(self, name, java_ver, vendor, pkg, version, end, arch, filename):
        super(DefaultTechPreview, self).__init__(name, java_ver, vendor, pkg, version, end, arch, filename)
        self.expected_provides[(name + "-" + java_ver + (("-" + pkg) if pkg else pkg))] = ns.get_version_full(filename)


class SdkTechPreview(DefaultTechPreview):
    def __init__(self, name, java_ver, vendor, pkg, version, end, arch, filename):
        super(SdkTechPreview, self).__init__(name, java_ver, vendor, pkg, version, end, arch, filename)
        pkg = pkg.replace("devel", "")
        self.expected_provides[(name + "-sdk" + "-" + java_ver + pkg)] = ns.get_version_full(filename)
        self.expected_provides[(name + "-sdk" + "-" + java_ver + "-" + vendor + pkg)] = \
            ns.get_version_full(filename)


class JreTechPreview(DefaultTechPreview):
    def __init__(self, name, java_ver, vendor, pkg, version, end, arch, filename):
        super(JreTechPreview, self).__init__(name, java_ver, vendor, pkg, version, end, arch, filename)
        self.expected_provides[("jre" + "-" + java_ver + (("-" + pkg) if pkg else pkg))] = ns.get_version_full(filename)
        self.expected_provides[("jre" + "-" + java_ver + "-" + vendor + (("-" + pkg) if pkg else pkg))] = \
            ns.get_version_full(filename)


class Default(DefaultTechPreview):
    def __init__(self, name, java_ver, vendor, pkg, version, end, arch, filename):
        super(Default, self).__init__(name, java_ver, vendor, pkg, version, end, arch, filename)
        self.expected_provides[(name + (("-" + pkg) if pkg else pkg))] = ns.get_version_full(filename)
        self.expected_provides[(name + "-" + vendor + (("-" + pkg) if pkg else pkg))] = \
            ns.get_version_full(filename)


class Sdk(Default):
    def __init__(self, name, java_ver, vendor, pkg, version, end, arch, filename):
        super(Sdk, self).__init__(name, java_ver, vendor, pkg, version, end, arch, filename)
        pkg = pkg.replace("devel", "")
        self.expected_provides[(name + "-sdk" + pkg)] = ns.get_version_full(filename)
        self.expected_provides[(name + "-sdk-" + vendor + pkg)] = \
            ns.get_version_full(filename)
        self.expected_provides[(name + "-sdk-" + java_ver + pkg)] = ns.get_version_full(filename)
        self.expected_provides[(name + "-sdk-" + java_ver + "-" + vendor + pkg)] = \
            ns.get_version_full(filename)


class Jre(Default):
    def __init__(self, name, java_ver, vendor, pkg, version, end, arch, filename):
        super(Jre, self).__init__(name, java_ver, vendor, pkg, version, end, arch, filename)
        self.expected_provides["jre" + (("-" + pkg) if pkg else pkg)] = ns.get_version_full(filename)
        self.expected_provides["jre" + "-" + vendor + (("-" + pkg) if pkg else pkg)] = \
            ns.get_version_full(filename)
        self.expected_provides[("jre" + "-" + java_ver + (("-" + pkg) if pkg else pkg))] = ns.get_version_full(filename)
        self.expected_provides[("jre" + "-" + java_ver + "-" + vendor + (("-" + pkg) if pkg else pkg))] = \
            ns.get_version_full(filename)


class HeadlessTechPreview(JreTechPreview):
    def __init__(self, name, java_ver, vendor, pkg, version, end, arch, filename):
        super(HeadlessTechPreview, self).__init__(name, java_ver, vendor, pkg, version, end, arch, filename)
        self.expected_provides["config({})".format("-".join([name, java_ver, vendor, pkg]))] = \
            ns.get_version_full(filename)


class Headless(Jre):
    def __init__(self, name, java_ver, vendor, pkg, version, end, arch, filename):
        super(Headless, self).__init__(name, java_ver, vendor, pkg, version, end, arch, filename)
        self.expected_provides["config({})".format("-".join([name, java_ver, vendor, pkg]))] = \
            ns.get_version_full(filename)


class OpenJfx(DebugInfo):
    def __init__(self, name, java_ver, vendor, pkg, version, end, arch, filename):
        super(OpenJfx, self).__init__(name, java_ver, vendor, pkg, version, end, arch, filename)
        pkg = pkg.replace("openjfx", "")
        self.expected_provides[("javafx" + pkg)] = ns.get_version_full(filename)


class JavaDoc(Default):
    def __init__(self, name, java_ver, vendor, pkg, version, end, arch, filename):
        super(JavaDoc, self).__init__(name, java_ver, vendor, pkg, version, end, arch, filename)

class JavaDocTechPreview(DefaultTechPreview):
    def __init__(self, name, java_ver, vendor, pkg, version, end, arch, filename):
        super(JavaDocTechPreview, self).__init__(name, java_ver, vendor, pkg, version, end, arch, filename)


class JavaDocZipTechPreview(Empty):
    def __init__(self, name, java_ver, vendor, pkg, version, end, arch, filename):
        super(JavaDocZipTechPreview, self).__init__(name, java_ver, vendor, pkg, version, end, arch, filename)
        self.expected_provides["-".join([name, java_ver, pkg.replace("-zip", "")])] = ns.get_version_full(filename)
        self.expected_provides["-".join([name, java_ver, vendor, pkg.replace("-zip", "")])] = ns.get_version_full(filename)
        self.expected_provides["-".join([name, java_ver, vendor, pkg])] = ns.get_version_full(filename)
        self.expected_provides["-".join([name, java_ver, vendor, pkg]) + ("({})".format(arch) if (arch != "noarch") else "")] = ns.get_version_full(filename)


class JavaDocZip(JavaDocZipTechPreview):
    def __init__(self, name, java_ver, vendor, pkg, version, end, arch, filename):
        super(JavaDocZip, self).__init__(name, java_ver, vendor, pkg, version, end, arch, filename)
        self.expected_provides["-".join([name, pkg.replace("-zip", "")])] = ns.get_version_full(filename)



class DebugInfoRolling(Empty):
    def __init__(self, name, java_ver, vendor, pkg, version, end, arch, filename):
        super(DebugInfoRolling, self).__init__(name, java_ver, vendor, pkg, version, end, arch, filename)
        self.expected_provides[("{}-{}-{}".format(name, java_ver, vendor) + (("-" + pkg) if pkg else pkg) +
                                "({})".format(arch))] = ns.get_version_full(filename)
        self.expected_provides[("{}-{}-{}".format(name, java_ver, vendor) + (("-" + pkg) if pkg else pkg))] = \
            ns.get_version_full(filename)


class DefaultRolling(DebugInfoRolling):
    def __init__(self, name, java_ver, vendor, pkg, version, end, arch, filename):
        super(DefaultRolling, self).__init__(name, java_ver, vendor, pkg, version, end, arch, filename)
        self.expected_provides[(name + "-" + ns.simplify_full_version(version) + (("-" + pkg) if pkg else pkg))] = ns.get_version_full(filename)
        self.expected_provides[(name + "-" + ns.simplify_full_version(version) + "-" + vendor + (("-" + pkg) if pkg else pkg))] = \
            ns.get_version_full(filename)


class SdkRolling(DefaultRolling):
    def __init__(self, name, java_ver, vendor, pkg, version, end, arch, filename):
        super(SdkRolling, self).__init__(name, java_ver, vendor, pkg, version, end, arch, filename)
        pkg = pkg.replace("devel", "")
        self.expected_provides[(name + "-sdk" + "-" + ns.simplify_full_version(version) + pkg)] = ns.get_version_full(filename)
        self.expected_provides[(name + "-sdk" + "-" + ns.simplify_full_version(version) + "-" + vendor + pkg)] = \
            ns.get_version_full(filename)


class JreRolling(DefaultRolling):
    def __init__(self, name, java_ver, vendor, pkg, version, end, arch, filename):
        super(JreRolling, self).__init__(name, java_ver, vendor, pkg, version, end, arch, filename)
        self.expected_provides[("jre" + "-" + ns.simplify_full_version(version) + (("-" + pkg) if pkg else pkg))] = ns.get_version_full(filename)
        self.expected_provides[("jre" + "-" + ns.simplify_full_version(version) + "-" + vendor + (("-" + pkg) if pkg else pkg))] = \
            ns.get_version_full(filename)


class HeadlessRolling(JreRolling):
    def __init__(self, name, java_ver, vendor, pkg, version, end, arch, filename):
        super(HeadlessRolling, self).__init__(name, java_ver, vendor, pkg, version, end, arch, filename)
        self.expected_provides["config({})".format("-".join([name, java_ver, vendor, pkg]))] = \
            ns.get_version_full(filename)


class JavaDocRolling(DefaultRolling):
    def __init__(self, name, java_ver, vendor, pkg, version, end, arch, filename):
        super(JavaDocRolling, self).__init__(name, java_ver, vendor, pkg, version, end, arch, filename)


class JavaDocZipRolling(JavaDocRolling):
    def __init__(self, name, java_ver, vendor, pkg, version, end, arch, filename):
        super(JavaDocZipRolling, self).__init__(name, java_ver, vendor, pkg, version, end, arch, filename)
        for provide in list(self.expected_provides):
            if "(" not in provide and java_ver not in provide:
                self.expected_provides[(provide.replace("-zip", ""))] = ns.get_version_full(filename)
                self.expected_provides.pop(provide)


class Webstart(DebugInfo):
    def __init__(self, name, java_ver, vendor, pkg, version, end, arch, filename):
        super(Webstart, self).__init__(name, java_ver, vendor, pkg, version, end, arch, filename)
        self.expected_provides["config({})".format("-".join([name, java_ver, vendor, pkg]))] = ns.get_version_full(filename)

class ITWebNonDefault(Empty):
    def __init__(self,  name, java_ver, vendor, pkg, version, end, arch, filename):
        super(ITWebNonDefault, self).__init__(name, java_ver, vendor, pkg, version, end, arch, filename)
        self.expected_provides[name + (("-" + pkg) if pkg else pkg)] = ns.get_version_full(filename)
        self.expected_provides[name + (("-" + pkg) if pkg else pkg) +
                               "({})".format(tu.validate_arch_for_provides(arch))] = ns.get_version_full(filename)

#itw default provides also java plugin and ws versions hardcoded for now as well as version of the java
class ITWebDefault(ITWebNonDefault):
    def __init__(self,  name, java_ver, vendor, pkg, version, end, arch, filename):
        super(ITWebDefault, self).__init__(name, java_ver, vendor, pkg, version, end, arch, filename)
        ver = "1:1.8.0"
        self.expected_provides["java-1.8.0-openjdk-plugin"] = ver
        self.expected_provides["java-plugin"] = ver
        self.expected_provides["javaws"] = ver


def make_rpm_readable(name):
    return ns.get_package_name(name) + "." + ns.get_arch(name)


def testAll():
    return ProvidesTest().execute_tests()


def documentAll():
    la.LoggingAccess().stdout("Provides")
    return ProvidesTest().execute_special_docs()

def main(argv):
    bt.defaultMain(argv, documentAll, testAll)


if __name__ == "__main__":
    main(sys.argv[1:])


