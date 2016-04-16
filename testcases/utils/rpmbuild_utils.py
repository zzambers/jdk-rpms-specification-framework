from testcases.utils import process_utils

def rpmbuildEval(macro):
    return process_utils.processToString(['rpmbuild', '--eval', '%{' + macro + '}'])