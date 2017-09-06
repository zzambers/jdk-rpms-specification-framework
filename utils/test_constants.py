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


def get_plugin_binaries():
    return [JCONTROL, CONTROL_PANEL, JAVAWS]

# same goes for debug pairs
DEFAULT_BINARIES = []
DEVEL_BINARIES = ['appletviewer', 'idlj', 'jar', 'jarsigner', 'javac', 'javadoc', 'javah', 'javap', 'jcmd', 'jconsole',
                  'jdb', 'jdeprscan', 'jdeps', 'jhsdb', 'jimage', 'jinfo', 'jlink', 'jmap', 'jmod', 'jps', 'jrunscript',
                  'jshell', 'jstack', 'jstat', 'jstatd', 'rmic', 'schemagen', 'serialver', 'wsgen', 'wsimport', 'xjc']
HEADLESS_BINARIES = ["appletviewer",  "idlj",  "java",  "jjs",  "jrunscript",  "keytool",  "orbd",  "pack200",
                     "rmid",  "rmiregistry",  "servertool",  "tnameserv",  "unpack200"]


def get_binaries_as_dict():
    return {DEFAULT: DEFAULT_BINARIES,
            DEVEL: DEVEL_BINARIES,
            HEADLESS: HEADLESS_BINARIES,
            DEFAULT + DEBUG_SUFFIX: DEFAULT_BINARIES,
            DEVEL + DEBUG_SUFFIX: DEVEL_BINARIES,
            HEADLESS + DEBUG_SUFFIX: HEADLESS_BINARIES
            }


def get_openjfx_binaries():
    return ["javapackager", "javafxpackager"]


def subpackages_without_alternatives():
    return ["accessibility", "debuginfo", "demo", "src", "accessibility-debug",
            "src-debug", "demo-debug", "headless-debuginfo", "devel-debuginfo", "demo-debuginfo",
            "debug-debuginfo", "devel-debug-debuginfo", "debugsource", "headless-debug-debuginfo",
            "demo-debug-debuginfo"]
