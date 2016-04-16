from subprocess import Popen, PIPE
import io
import outputControl.logging_access



def processToString(args):
    proc = _exec(args)
    out, err = proc.communicate()
    output = out.decode('utf-8').strip()  # utf-8 works in your case
    outputControl.logging_access.LoggingAccess().log("got: " + output)
    return output

def processAsStrings(args):
    res = []
    proc = _exec(args)
    for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
        line = line.strip()
        outputControl.logging_access.LoggingAccess().log("reading: "+line)
        res.append(line)
    return res

def _exec(args):
    outputControl.logging_access.LoggingAccess().log("executing: " + str(args))
    proc = Popen(args, stdout=PIPE)
    return proc;
