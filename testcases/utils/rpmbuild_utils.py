from testcases.utils import process_utils

def rpmbuildEval(macro):
    return process_utils.processToString(['rpmbuild', '--eval', '%{' + macro + '}'])

def listFilesInPackage(rpmFile):
    return process_utils.processAsStrings(['rpm', '-qlp', rpmFile])