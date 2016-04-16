from subprocess import Popen, PIPE

import outputControl.logging_access



def processToString(args):
    outputControl.logging_access.LoggingAccess().log("executing: " + str(args))
    proc = Popen(args, stdout=PIPE)
    out, err = proc.communicate()
    output = out.decode('utf-8').strip()  # utf-8 works in your case
    outputControl.logging_access.LoggingAccess().log("got: " + output)
    return output