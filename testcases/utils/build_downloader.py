"""In time of writing this library, the koji python library was not  compatible with python3, so legacy approach was chosen"""

import io
import ntpath
import os
import subprocess

import shutil
import urllib3

import config.runtime_config
import config.global_config as gc
import testcases.utils.pkg_name_split as split
from outputControl import logging_access as la
from testcases.utils import rpm_list

BREW = "brew"
KOJI = "koji"


def getBuild(nvr):
    target = _checkDest(config.runtime_config.RuntimeConfig().getPkgsDir())
    command = _getCommand(nvr)
    la.LoggingAccess().log("using " + command);
    packages = _getBuildInfo(command, nvr)
    if len(packages) == 0:
        raise Exception("No pkgs to download. Verify build or archs")
    la.LoggingAccess().log("going to download " + str(len(packages)) + " rpms")
    _downloadBrewKojiBuilds(packages, target)
    return True


def _downloadBrewKojiBuilds(pkgs, targetDir):
    for i, pkg in enumerate(pkgs):
        mainUrl = _getMainUrl(pkg)
        url = "unknonw_service"
        if KOJI in pkg:
            url = mainUrl + pkg.replace("/mnt/koji/", "/")
        if BREW in pkg:
            url = mainUrl + pkg.replace("/mnt/redhat/", "/")
        la.LoggingAccess().log("downloading " + str(i + 1) + "/" + str(len(pkgs)) + " - " + url)
        targetFile = targetDir + "/" + ntpath.basename(pkg)
        http = urllib3.PoolManager()
        with http.request('GET', url, preload_content=False) as r, open(targetFile, 'wb') as out_file:
            shutil.copyfileobj(r, out_file)


def _getBuildInfo(cmd, nvr):
    rpms = []
    runningRpms = False
    proc = subprocess.Popen([cmd, 'buildinfo', nvr], stdout=subprocess.PIPE)
    for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
        line = line.strip()
        if runningRpms:
            if _isArchValid(line):
                rpms.append(line)
        else:
            if line == "RPMs:":
                runningRpms = True
            else:
                la.LoggingAccess().log(line)
    return rpms


def _checkDest(dir):
    absOne = os.path.abspath(dir)
    if not os.path.exists(absOne):
        la.LoggingAccess().log("Creating: " + absOne)
        os.mkdir(absOne)
    if not os.path.isdir(absOne):
        raise Exception(absOne + " Must bean drectory, is not")
    if not os.listdir(absOne) == []:
        raise Exception(absOne + " Is not empty, please fix")
    la.LoggingAccess().log("Using as download target: " + absOne)
    return absOne


def _isArchValid(rpmLine):
    for arch in gc.getAllArchs():
        if "/" + arch + "/" in rpmLine or "." + arch + "." in rpmLine:
            return True
    return False


def _getCommand(nvr):
    os = _getOs(nvr + ".fakeArch")
    if rpm_list.isRhel(os):
        return BREW
    if rpm_list.isFedora(os):
        return KOJI
    raise Exception("Unknown os - " + os)


def _getMainUrl(path_rpm):
    rpm = ntpath.basename(path_rpm)
    os = _getOs(rpm)
    if rpm_list.isRhel(os):
        return "http://download.devel.redhat.com/"
    if rpm_list.isFedora(os):
        return "http://koji.fedoraproject.org"
    raise Exception("Unknown os - " + os)


def _getOs(rpm):
    os = split.get_dist(rpm)
    la.LoggingAccess().log("in " + rpm + " recognized " + os)
    return os
