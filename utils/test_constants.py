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


# exports jre binaries
def get_exports_binaries_jre():
    return ["jre_exports", "jre"]


# exports sdk binaries
def get_exports_binaries_sdk():
    return ["java_sdk_exports", "java_sdk"]


def oracle_exclude_list():
    return [JMC_INI]
