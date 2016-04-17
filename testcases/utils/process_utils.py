from subprocess import Popen, PIPE
import io
import outputControl.logging_access



def processToString(args):
    proc = _exec(args)
    out, err = proc.communicate()
    output = out.decode('utf-8').strip()  # utf-8 works in your case
    outputControl.logging_access.LoggingAccess().log("got: " + output)
    return output

def processAsStrings(args, starter=None, finisher=None, initialCanRead=True):
    """ read process line by line. starter and finisher are methods, which returns true/false to set read. Theirs immput is line"""
    res = []
    proc = _exec(args)
    canRead=initialCanRead
    for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
        line = line.strip()
        outputControl.logging_access.LoggingAccess().log("reading: "+line)
        if (canRead and finisher is not None):
            canRead = finisher(line)
            if (not canRead):
                outputControl.logging_access.LoggingAccess().log(str(finisher)+" stopped recording")
        if canRead:
            res.append(line)
        if (not canRead and starter is not None):
            canRead=starter(line)
            if canRead:
                outputControl.logging_access.LoggingAccess().log(str(starter) + " started recording")
    return res

def _exec(args):
    outputControl.logging_access.LoggingAccess().log("executing: " + str(args))
    proc = Popen(args, stdout=PIPE)
    return proc;
