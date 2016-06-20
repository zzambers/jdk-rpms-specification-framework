from subprocess import Popen, PIPE
import io
import outputControl.logging_access


def processToString(args):
    o, e = processToStrings(args, False)
    return o

def processToStrings(args, err = True):
    o, e, r = processToStringsWithResult(args, err)
    return o, e

def processToStringsWithResult(args, err=True, cwd=None):
    proc = _exec(args, err, cwd)
    out, err = proc.communicate()
    output = out.decode('utf-8').strip()
    outpute = "";
    if err is not None:
        outpute = err.decode('utf-8').strip()
    outputControl.logging_access.LoggingAccess().log("got: " + output)
    ret = proc.wait()
    return output, outpute, ret

def processAsStrings(args, starter=None, finisher=None, initialCanRead=True, log = True):
    o, r = processAsStringsWithResult(args, starter, finisher, initialCanRead, log)
    return o;

def processAsStringsWithResult(args, starter=None, finisher=None, initialCanRead=True, log = True):
    """ read process line by line. starter and finisher are methods, which returns true/false to set read. Theirs immput is line"""
    res = []
    proc = _exec(args)
    canRead=initialCanRead
    for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
        line = line.strip()
        if log:
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
    ret = proc.wait()
    return res, ret

def _exec(args, err=False, cwd=None):
    outputControl.logging_access.LoggingAccess().log("executing: " + str(args))
    if (err):
        # args, bufsize=-1, executable=None, stdin=None, stdout=None, stderr=None, preexec_fn=None, close_fds=_PLATFORM_DEFAULT_CLOSE_FDS, shell=False, cwd=None, env=None ...
        proc = Popen(args, stdout=PIPE, stderr=PIPE, cwd=cwd)
    else:
        proc = Popen(args, stdout=PIPE)
    return proc;

def executeShell(command):
    outputControl.logging_access.LoggingAccess().log("executing shell : " + command)
    shell = Popen(command, stdin=PIPE, stderr=PIPE, shell=True)
    o, e  = shell.communicate()
    if (o is not None):
        o = o.decode('utf-8').strip()
    else:
        o=""
    if (3 is not None):
        e = e.decode('utf-8').strip()
    else:
        e = ""
    r = shell.wait()
    return o, e, r
