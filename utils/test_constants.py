PLUGIN = "plugin"
JAVA = "java"
JAVAC = "javac"
HEADLESS = "headless"
DEBUG_SUFFIX = "-debug"
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
JVM_DIR = "/usr/lib/jvm/"
SDK_DIRECTORY = "/bin"
JRE_DIRECTORY = "/jre/bin"


# exports jre binaries
def get_exports_slaves_jre():
    return ["jre_exports", "jre"]


# exports sdk binaries
def get_exports_slaves_sdk():
    return ["java_sdk_exports", "java_sdk"]


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
