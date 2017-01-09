from testcases.alternativesTests.binaries_test_methods import DEFAULT, DEVEL, EXPORTS_DIR, \
    HEADLESS, JRE_LOCATION, SDK_LOCATION, DEBUG_SUFFIX, BinarySlaveTestMethods


class OpenJdk6(BinarySlaveTestMethods):
    def _get_jre_sdk_locations(self):
        return [[DEFAULT], [DEVEL]]

    def _get_slave_pkgs(self):
        return self._get_jre_sdk_locations()

    def _get_target(self):
        target = self.rpms.getSrpm().strip(".src.rpm").strip("rpms/")
        unnecessary_part = target.split("-")[-1]
        target = target.strip("-" + unnecessary_part)
        return target

    def _get_exports_directory(self, target):
        directory = EXPORTS_DIR + target
        return directory

    def _get_policytool_location(self):
        return [[DEFAULT, DEVEL], [DEVEL]]

    def _get_alternative_exports_target(self, target):
        target = target.replace("-" + self.rpms.getVersion(), "")
        return target


class OpenJdk6PowBeArchAndX86(OpenJdk6):
    def _get_target(self):
        target = super()._get_target()
        target = target + "." + self._get_arch()
        return target


class OpenJdk7(OpenJdk6PowBeArchAndX86):
    def _get_jre_sdk_locations(self):
        locations = super()._get_jre_sdk_locations()
        locations[JRE_LOCATION].append(HEADLESS)
        return locations

    def _get_slave_pkgs(self):
        return [[HEADLESS], [DEVEL]]

    def _get_target(self):
        target = self.rpms.getSrpm().strip(".src.rpm").strip("rpms/") + "." + self._get_arch()
        return target

    def _get_exports_directory(self, target):
        newtarg = target.replace("java", "jre")
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
