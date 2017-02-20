from testcases.alternativesTests.binaries_test_methods import DEFAULT, DEVEL, EXPORTS_DIR, \
    HEADLESS, JRE_LOCATION, SDK_LOCATION, DEBUG_SUFFIX, POLICYTOOL, PLUGIN, BinarySlaveTestMethods, \
    BINARIES, JAVA, JAVAC, LIBJAVAPLUGIN, NOT_PRESENT_IN, SUBPACKAGE, \
    SLAVES, CAN_NOT_BE_IN, MUST_BE_IN, BINARY, SLAVE, BECAUSE_THIS_ARCH_HAS_NO, CONTROL_PANEL, JAVAWS, JCONTROL
import utils.pkg_name_split as pkgsplit
from utils.mock.mock_executor import DefaultMock


class OpenJdk6(BinarySlaveTestMethods):
    def _get_jre_sdk_locations(self):
        return [[DEFAULT], [DEVEL]]

    def _get_slave_pkgs(self):
        return self._get_jre_sdk_locations()

    def _get_target(self, name):
        target = self._get_32bit_id_in_nvra(pkgsplit.get_nvra(name))
        unnecessary_part = target.split("-")[-1]
        target = target.replace("-" + unnecessary_part, "")
        return target

    def _get_exports_directory(self, target):
        directory = EXPORTS_DIR + target
        return directory

    def _get_policytool_location(self):
        return [[DEFAULT, DEVEL], [DEVEL]]

    def _get_alternative_exports_target(self, target):
        target = target.replace("-" + self.rpms.getVersion(), "")
        return target

    # checks policytool in default pkg and merge default pkg with headless in JDK 8 for further check
    def check_policytool_for_jdk(self, pkg_binaries):
        policytool_location = self._get_policytool_location()
        self._document("{} is a special case of binary and slave.".format(POLICYTOOL) +
                       "\n - {} binary must be present in {} "
                       "subpackages.".format(POLICYTOOL, " and ".join(self._get_policytool_location()[JRE_LOCATION])) +
                       "\n - {} slave must be present in {} "
                       "subpackages.".format(POLICYTOOL, " and ".join( policytool_location[1])))
        def_debug_pkg = None
        def_pkg = None

        for loc in policytool_location[JRE_LOCATION]:
            if POLICYTOOL not in pkg_binaries[loc]:
                self.failed_tests.append(POLICYTOOL + NOT_PRESENT_IN + SUBPACKAGE + BINARIES)
                self.binaries_test.log(POLICYTOOL + NOT_PRESENT_IN + SUBPACKAGE + BINARIES)

            if DEFAULT in loc:
                if HEADLESS in pkg_binaries.keys():
                    if pkg_binaries[loc] != [POLICYTOOL]:
                        self.failed_tests.append(DEFAULT + " " + SUBPACKAGE + "should contain only {},"
                                                 " but contains: ".format(POLICYTOOL) + ", ".join(pkg_binaries[loc]))
                        self.binaries_test.log(POLICYTOOL + " " + SUBPACKAGE + "should contain only {}, "
                                               "but contains: ".format(POLICYTOOL) +
                                               ",".join(pkg_binaries[loc]))
                    if DEBUG_SUFFIX in loc:
                        def_debug_pkg = pkg_binaries.pop(loc)
                    else:
                        def_pkg = pkg_binaries.pop(loc)
                else:
                    pkg_binaries[loc].remove(POLICYTOOL)

        if HEADLESS in policytool_location[SDK_LOCATION]:
            if def_pkg is not None:
                pkg_binaries[HEADLESS] += def_pkg
            if def_debug_pkg is not None:
                pkg_binaries[HEADLESS + DEBUG_SUFFIX] += def_debug_pkg

        return pkg_binaries


class OpenJdk6PowBeArchAndX86(OpenJdk6):
    def _get_target(self, name):
        target = super()._get_target(name)
        target = target + "." + self._get_arch()
        return target


class OpenJdk7(OpenJdk6PowBeArchAndX86):
    def _get_jre_sdk_locations(self):
        locations = super()._get_jre_sdk_locations()
        locations[JRE_LOCATION].append(HEADLESS)
        return locations

    def _get_slave_pkgs(self):
        return [[HEADLESS], [DEVEL]]

    def _get_target(self, name):
        return self._get_32bit_id_in_nvra(pkgsplit.get_nvra(name))

    def _get_exports_directory(self, target):
        newtarg = target.replace(JAVA, "jre")
        directory = EXPORTS_DIR + newtarg
        return directory

    def _get_alternative_exports_target(self, target):
        return target


class OpenJdk8(OpenJdk7):
    def _get_policytool_location(self):
        return [[DEFAULT, DEVEL], [HEADLESS]]


class OpenJdk8Intel(OpenJdk8):
    def _get_jre_sdk_locations(self):
        locations = super()._get_jre_sdk_locations()
        locations[JRE_LOCATION] += [HEADLESS + DEBUG_SUFFIX, DEFAULT + DEBUG_SUFFIX]
        locations[SDK_LOCATION].append(DEVEL + DEBUG_SUFFIX)
        return locations

    def _get_slave_pkgs(self):
        locations = super()._get_slave_pkgs()
        locations[JRE_LOCATION].append(HEADLESS + DEBUG_SUFFIX)
        locations[SDK_LOCATION].append(DEVEL + DEBUG_SUFFIX)
        return locations

    def _get_policytool_location(self):
        locations = super()._get_policytool_location()
        locations[JRE_LOCATION] += [DEFAULT + DEBUG_SUFFIX, DEVEL + DEBUG_SUFFIX]
        locations[SDK_LOCATION].append(HEADLESS + DEBUG_SUFFIX)
        return locations


class IbmBaseMethods(BinarySlaveTestMethods):
    # classic and j9vm are folders, not binaries
    def _clean_bin_dir_for_ibm(self, binaries):
        cleaned_bins = []
        for bin in binaries:
            if bin == "classic":
                continue
            elif bin == "j9vm":
                continue
            else:
                cleaned_bins.append(bin)
        return cleaned_bins

    def _get_jre_sdk_locations(self):
        return [[DEFAULT], [DEVEL]]

    def _get_slave_pkgs(self):
        return self._get_jre_sdk_locations()

    def _get_target(self, name):
        return self._get_32bit_id_in_nvra(pkgsplit.get_nvra(name))

    def _get_exports_directory(self, target):
        directory = EXPORTS_DIR + target
        return directory

    def doc_and_clean_no_slave_binaries(self, pkg_binaries):
        lcs = self._get_jre_sdk_locations()
        notbinaries = ["klist", "kinit", "ktab"]
        notinsdk = ["ikeycmd", "ikeyman"]

        docs = "{} are binaries present in {} subpackages. They are not present in {} " \
               "subpackage. They got no slaves in alternatives.".format(" and ".join(notbinaries),
                                                                        "".join(lcs[JRE_LOCATION]),
                                                                        "".join(lcs[SDK_LOCATION]))
        docs += "\n - {} are binaries, that are present in {} subpackage, but are not present in {} subpackage" \
                " binaries. They also do not have slaves in alternatives.".format(" and ".join(notinsdk),
                                                                                  "".join(lcs[JRE_LOCATION]),
                                                                                  "".join(lcs[SDK_LOCATION]))

        self._document(docs)

        for subpackage in lcs[JRE_LOCATION]:
            for binary in notbinaries + notinsdk:
                if binary not in pkg_binaries[subpackage]:
                    self.failed_tests.append(binary + MUST_BE_IN + str(subpackage))
                    self.binaries_test.log(binary + NOT_PRESENT_IN + str(subpackage) + " " + SUBPACKAGE + BINARIES)
                else:
                    pkg_binaries[subpackage].remove(binary)
        return pkg_binaries

    def document_plugin_and_related_binaries(self, pkg_binaries, installed_slaves = None):
        lcs = self._get_jre_sdk_locations()
        locs = lcs[JRE_LOCATION] + lcs[SDK_LOCATION]
        bins = [JCONTROL, CONTROL_PANEL, JAVAWS]
        self._document("{} are binaries replacing {} subpackage. They are present in {} subpackages and their slaves"
                       " are in {} subpackages.".format(" and ".join(bins), PLUGIN, " and ".join(locs)
                                                        , "".join(lcs[JRE_LOCATION])))
        for b in bins:
            for location in lcs[JRE_LOCATION]:
                if b not in pkg_binaries[location]:
                    self.failed_tests.append(b + NOT_PRESENT_IN + str(location) + " " + BINARIES)
                    self.binaries_test.log( b + MUST_BE_IN + str(location) + " " + SUBPACKAGE + BINARIES + 
                                            BECAUSE_THIS_ARCH_HAS_NO + PLUGIN + " " + SUBPACKAGE)
                if b not in installed_slaves[location]:
                    self.failed_tests.append(b + NOT_PRESENT_IN + str(location) + " " + SLAVES)
                    self.binaries_test.log( b + MUST_BE_IN + str(location) + " " + SUBPACKAGE + SLAVES + 
                                            BECAUSE_THIS_ARCH_HAS_NO + PLUGIN + " " + SUBPACKAGE)
            for location in lcs[SDK_LOCATION]:
                if b not in pkg_binaries[location]:
                    self.failed_tests.append(b + NOT_PRESENT_IN + str(location) + " " + BINARIES)
                    self.binaries_test.log( b + MUST_BE_IN + str(location) + " " + SUBPACKAGE + BINARIES + 
                                            BECAUSE_THIS_ARCH_HAS_NO + PLUGIN + " " + SUBPACKAGE)
        return

    def exports_dir_check(self, dirs, exports_target = None, _subpkg = None):
        self._document("IBM java does not have export directory for {} subpackage.".format(DEVEL) +
                       "\n - Exports slaves point at {} directory. ".format(EXPORTS_DIR))
        if _subpkg == DEVEL:
            return
        exports_check = DefaultMock().execute_ls(EXPORTS_DIR)
        if exports_check[1] != 0:
            dirs.append(("Exports directory does not exist: " + exports_target, 2))
        elif exports_target not in exports_check[0]:
            dirs.append((exports_target + " not present in " + EXPORTS_DIR, 2))
        else:
            dirs.append(exports_check)
        return



class IbmWithPluginSubpkg(IbmBaseMethods):
    def document_plugin_and_related_binaries(self, pkg_binaries, installed_slaves = None):
        lcs = self._get_jre_sdk_locations()
        bins = [JCONTROL, CONTROL_PANEL, JAVAWS]
        self._document("{} are binaries related with {}. They are present and have slaves only in {} "
                       "subpackages.".format(" and ".join(bins), PLUGIN, PLUGIN))
        for b in bins:
            if b not in pkg_binaries[PLUGIN]:
                self.binaries_test.log(b + MUST_BE_IN + PLUGIN + " " + SUBPACKAGE + BINARIES)
                self.failed_tests.append(b + NOT_PRESENT_IN + PLUGIN + " " + SUBPACKAGE + BINARIES)
            if b not in installed_slaves[PLUGIN]:
                self.binaries_test.log(b + MUST_BE_IN + PLUGIN + " " + SUBPACKAGE + SLAVES)
                self.failed_tests.append(b + NOT_PRESENT_IN + PLUGIN + " " + SUBPACKAGE + SLAVES)

        for l in lcs[SDK_LOCATION] + lcs[JRE_LOCATION]:
            for b in bins:
                if b in pkg_binaries[l]:
                    self.failed_tests.append(b + " " + BINARY + CAN_NOT_BE_IN + str(l))
                    self.binaries_test.log(b + " " + BINARY + CAN_NOT_BE_IN + str(l) + ", it " + MUST_BE_IN +
                                           PLUGIN + " " + SUBPACKAGE)
                    pkg_binaries[l].remove(b)
                if b in installed_slaves[l]:
                    self.failed_tests.append( b + " " + SLAVE + CAN_NOT_BE_IN + str(l))
                    self.binaries_test.log(b + " " + SLAVE + CAN_NOT_BE_IN + str(l)+ ", it" + MUST_BE_IN +
                                           PLUGIN + " " + SUBPACKAGE)
                    installed_slaves[l].remove(b)
        return

    def _has_plugin_subpkg(self):
        return [PLUGIN]

    def _get_checked_masters(self):
        masters = super()._get_checked_masters()
        masters.append(LIBJAVAPLUGIN)
        return masters


class IbmS390Archs(IbmBaseMethods):
    def document_plugin_and_related_binaries(self, pkg_binaries, installed_slaves = None):
        lcs = self._get_jre_sdk_locations()
        bins = [JCONTROL, CONTROL_PANEL, JAVAWS]
        self._document("{} are not present in binaries in any subpackage. This architecture "
                       "also has no {} subpackages.".format(" and ".join(bins), PLUGIN))

        for b in bins:
            for l in lcs[JRE_LOCATION]:
                if b in pkg_binaries[l]:
                    self.failed_tests.append(b + " " + BINARY + CAN_NOT_BE_IN + str(lcs[JRE_LOCATION]))
                    self.binaries_test.log(b + " " + BINARY + CAN_NOT_BE_IN + str(lcs[JRE_LOCATION]))

                if b in installed_slaves[l]:
                    self.failed_tests.append(b + " " + SLAVE + CAN_NOT_BE_IN + str(lcs[JRE_LOCATION]))
                    self.binaries_test.log(b + " " + SLAVE + CAN_NOT_BE_IN + str(lcs[JRE_LOCATION]))

            for l in lcs[SDK_LOCATION]:
                if b in pkg_binaries[l]:
                    self.failed_tests.append(b + " " + BINARY + CAN_NOT_BE_IN + str(lcs[SDK_LOCATION]))
                    self.binaries_test.log(b + " " + BINARY + CAN_NOT_BE_IN + str(lcs[SDK_LOCATION]))
        return


class IbmArchMasterPlugin(IbmWithPluginSubpkg):
    def _get_checked_masters(self):
        return [JAVA, JAVAC, LIBJAVAPLUGIN + "." + self._get_arch()]
