PLUGIN = "plugin"
JAVA = "java"
JAVAC = "javac"
HEADLESS = "headless"
DEVEL = "devel"
DEFAULT = "default"
CONTROL_PANEL = "ControlPanel"
LIBJAVAPLUGIN = "libjavaplugin.so"
LIBNSSCKBI_SO = "libnssckbi.so"
JAVAFXPACKAGER = "javafxpackager"
POLICYTOOL = "policytool"
JAVAFX = "javafx"
JAVADOC = "javadoc"
MAN_DIR = "/usr/share/man/man1"
WAS_NOT_FOUND = "was not found"
JAVA_RMI_CGI = "java-rmi.cgi"
ICED_TEA_PLUGIN_SO = "IcedTeaPlugin.so"
JMC_INI = "jmc.ini"
JVM_DIR = "/usr/lib/jvm"
SDK_DIRECTORY = "/bin"
JRE_DIRECTORY = "/jre/bin"
JCONTROL = "jcontrol"
JAVAWS = "javaws"
ITWEB_SETTINGS = "itweb-settings"
USR_BIN = "/usr/bin"
JRE = "jre"
SDK = "java_sdk"
OJDK8 = "ojdk8"
OJDK8JFX = "ojdk8JFX"
OJDK8DEBUG = "ojdk8debug"
TECHPREVIEWS = ["11"]


# exports jre binaries
def get_exports_slaves_jre():
    return ["jre_exports"]


# exports sdk binaries
def get_exports_slaves_sdk():
    return ["java_sdk_exports"]

def get_ibm_k_bins():
    return ["klist", "kinit", "ktab"]


def get_ibm_ikey_bins():
    return ["ikeycmd", "ikeyman"]


def get_ibm_folders():
    return ["classic", "j9vm"]


def oracle_exclude_list():
    return [JMC_INI]


def get_ibm_exclude_list():
    return get_ibm_k_bins() + get_ibm_folders() + get_ibm_ikey_bins()


def get_plugin_binaries():
        return [JCONTROL, CONTROL_PANEL, JAVAWS]


def get_openjfx_binaries():
    return ["javapackager", "javafxpackager"]


def subpackages_without_alternatives():
    return ["accessibility", "debuginfo", "demo", "src", "accessibility" + DEBUG_SUFFIX,
            "src" + DEBUG_SUFFIX, "demo" + DEBUG_SUFFIX, "headless-debuginfo", "devel-debuginfo", "demo-debuginfo",
            "debug-debuginfo", "devel" + DEBUG_SUFFIX + "-debuginfo", "debugsource",
            "headless" + DEBUG_SUFFIX + "-debuginfo",
            "demo" + DEBUG_SUFFIX + "-debuginfo", "jdbc"]


def get_javadoc_dirs():
    return [JAVADOC, JAVADOC + DEBUG_SUFFIX, "javadoc-zip" + DEBUG_SUFFIX, "javadoc-zip"]


# slowdebug/debug suffixes in various jdk are not trivial task to do, this is very bad hack and can not stay this way
def identify_debug_suffix():
    import config.runtime_config as conf
    import config.global_config as gc
    rpms = conf.RuntimeConfig().getRpmList()
    version = rpms.getMajorVersionSimplified()
    dist = rpms.getDist()
    if int(version) < 9 or rpms.getDist() == gc.ITW or(rpms.getOs() == gc.RHEL and rpms.getOsVersionMajor() == 7):
        return "-debug"
    else:
        return "-slowdebug"


DEBUG_SUFFIX = identify_debug_suffix()
