from subprocess import Popen, PIPE
import io
import outputControl.logging_access


def processToString(args):
    o, e = processToStrings(args, False)
    return o

def processToStrings(args, err = True):
    proc = _exec(args, err)
    out, err = proc.communicate()
    output = out.decode('utf-8').strip()
    outpute = "";
    if err is not None:
        outpute = err.decode('utf-8').strip()
    outputControl.logging_access.LoggingAccess().log("got: " + output)
    return output, outpute

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

def _exec(args, err=False):
    outputControl.logging_access.LoggingAccess().log("executing: " + str(args))
    if (err):
        proc = Popen(args, stdout=PIPE, stderr=PIPE)
    else:
        proc = Popen(args, stdout=PIPE)
    return proc;
