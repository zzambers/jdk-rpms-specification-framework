import testcases.utils.process_utils


def rpmbuildEval(macro):
    return testcases.utils.process_utils.processToString(['rpmbuild', '--eval', '%{' + macro + '}'])


def listFilesInPackage(rpmFile):
    return testcases.utils.process_utils.processAsStrings(['rpm', '-qlp', rpmFile])



def _isScripletLine(scriplet, line):
    return line.startswith(scriplet + " " + ScripletStarterFinisher.scriptlet)

class ScripletStarterFinisher:
    #hard to say when rpm uses uninstall or jsut un or install or just "nothing"
    allScriplets = [
        'pretrans',
        'preinstall',
        'postinstall',
        'triggerinstall',
        'triggeuninstall',
        'preuninstall',
        'postuninstall',
        'triggerpostuninstall',
        'posttrans'
    ]

    scriptlet = "scriptlet"

    def __init__(self, id):
        self.id = id;

    def start(self, line):
        return _isScripletLine(self.id, line)

    def stop(self, line):
        for scriptlet in  ScripletStarterFinisher.allScriplets:
            if _isScripletLine(scriptlet, line):
                return False #stop
        return True #continue

def getSrciplet(rpmFile, scripletId):
    sf = ScripletStarterFinisher(scripletId)
    return testcases.utils.process_utils.processAsStrings(['rpm', '-qp', '--scripts', rpmFile], sf.start, sf.stop, False)
