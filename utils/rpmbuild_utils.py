import outputControl.logging_access
import utils.process_utils


def rpmbuildEval(macro):
    return utils.process_utils.processToString(['rpmbuild', '--eval', '%{' + macro + '}'])


def listFilesInPackage(rpmFile):
    return utils.process_utils.processAsStrings(['rpm', '-qlp', rpmFile])


def listDocsInPackage(rpmFile):
    return utils.process_utils.processAsStrings(['rpm', '-qldp', rpmFile])


def listConfigFilesInPackage(rpmFile):
    return utils.process_utils.processAsStrings(['rpm', '-qlcp', rpmFile])


def listOfRequires(rpmFile):
    return utils.process_utils.processAsStrings(['rpm', '--requires', '-qp', rpmFile])


def listOfProvides(rpmFile):
    return utils.process_utils.processAsStrings(['rpm', '--provides', '-qp', rpmFile])


def listOfObsoletes(rpmFile):
    return utils.process_utils.processAsStrings(['rpm', '--obsoletes', '-qp', rpmFile])


def listOfVersionlessRequires(rpmFile):
    return _filterVersions(listOfRequires(rpmFile))


def listOfVersionlessProvides(rpmFile):
    return _filterVersions(listOfProvides(rpmFile))


def listOfVersionlessObsoletes(rpmFile):
    return _filterVersions(listOfObsoletes(rpmFile))


def _filterVersions(listOfStrings):
    filtered = []
    for orig in listOfStrings:
        filtered.append(orig.split()[0])
    return filtered


def _isScripletLine(scriplet, line):
    return line.startswith(scriplet + " " + ScripletStarterFinisher.scriptlet)


PRETRANS = 'pretrans'
PREINSTALL = 'preinstall'
POSTINSTALL = 'postinstall'
TGINSTALL = 'triggerinstall'
TGUNINSTALL = 'triggeuninstall'
PREUNINSTALL = 'preuninstall'
POSTUNINSTALL = 'postuninstall'
TGPOSTUNINSTALL = 'triggerpostuninstall'
POSTTRANS = 'posttrans'


def isScripletNameValid(name):
    return name in ScripletStarterFinisher.allScriplets


class ScripletStarterFinisher:
    # hard to say when rpm uses uninstall or just un or install or just "nothing"
    allScriplets = [
        PRETRANS,
        PREINSTALL,
        POSTINSTALL,
        TGINSTALL,
        TGUNINSTALL,
        PREUNINSTALL,
        POSTUNINSTALL,
        TGPOSTUNINSTALL,
        POSTTRANS
    ]

    scriptlet = "scriptlet"

    def __init__(self, iid):
        self.id = iid

    def start(self, line):
        return _isScripletLine(self.id, line)

    def stop(self, line):
        for scriptlet in ScripletStarterFinisher.allScriplets:
            if _isScripletLine(scriptlet, line):
                return False  # stop
        return True  # continue


def getSrciplet(rpmFile, scripletId):
    sf = ScripletStarterFinisher(scripletId)
    if not isScripletNameValid(scripletId):
        outputControl.logging_access.LoggingAccess().log("warning! Scriplet name " + scripletId
                                                         + " is not known. It should be one of: "
                                                         + ",".join(ScripletStarterFinisher.allScriplets))
    return utils.process_utils.processAsStrings(['rpm', '-qp', '--scripts', rpmFile], sf.start, sf.stop,
                                                False)
