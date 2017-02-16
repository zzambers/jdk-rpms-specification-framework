from collections import namedtuple
import config.global_config
import ntpath

RpmNameParts = namedtuple('RpmNameParts',
                          ['java', 'java_ver', 'vendor', 'pkg',
                           'version', 'release', 'dist', 'arch'])


def _rpmname_splithelper(name):
    parts1 = _hyphen_split(name)
    parts2 = _dot_split(name)

    return RpmNameParts(parts1[0], parts1[1], parts1[2], parts1[3], parts1[4], parts2[0], parts2[1], parts2[2])


def _hyphen_split(name):
    """Split the rpm name according to hyphens, the subpackage string
    can be also empty or contain hyphens - as in devel-debug etc."""
    gc = config.global_config
    name = name.strip()
    hyphen_parts = name.split('-')
    num_h = len(hyphen_parts)
    if (name.startswith(gc.ITW)):
        icedtea, web,  *pkg, version, whole_end = hyphen_parts
        pkg = '-'.join(pkg)
        return ([gc.ITW, gc.ITW, gc.ITW, pkg, version, whole_end])
    else:
        java, java_ver, vendor, *pkg, version, whole_end = hyphen_parts
        pkg = '-'.join(pkg)
        return ([java, java_ver, vendor, pkg, version, whole_end])


def _get_ith_part(i, name):
    name = ntpath.basename(name)
    parts = _hyphen_split(name)
    return parts[i]


def _get_ith_dotpart(i, name):
    name = ntpath.basename(name)
    parts = _dot_split(name)
    return parts[i]


def get_dottedsuffix(name):
    return _get_ith_part(5, name)


def _dot_split(name):
    name = name.strip()
    whole_end = get_dottedsuffix(name)
    period_parts = whole_end.split('.')
    without_rpm = period_parts[:-1]
    num_p = len(without_rpm)
    release = '.'.join(without_rpm[: num_p - 2])
    dist, arch = without_rpm[num_p - 2:]
    return [release, dist, arch]


def get_javaprefix(name):
    """Should be always java"""
    return _get_ith_part(0, name)


def get_major_ver(name):
    """eg 1.7.0 or 9"""
    return _get_ith_part(1, name)


def get_vendor(name):
    """eg openjdk"""
    return _get_ith_part(2, name)


def get_major_package_name(name):
    """or java-1.8.0-openjdk"""
    parts = _hyphen_split(name)
    return "-".join(parts[0:3])


def get_package_name(name):
    """ eg java-1.8.0-openjdk-devel
        or java-1.8.0-openjdk
    """
    package = get_major_package_name(name)
    subpackage = get_subpackage_only(name)
    if subpackage == "":
        return package
    else:
        return package + "-" + subpackage


def get_subpackage_only(name):
    """ eg devel-debug"""
    return _get_ith_part(3, name)


def get_minor_ver(name):
    """ eg 1.8.0.77"""
    return _get_ith_part(4, name)


def get_release(name):
    """ eg 2.b03"""
    if name.endswith(".rpm"):
        return _get_ith_dotpart(0, name)
    else:
        return _get_ith_dotpart(0, name + ".rpm")


def get_dist(name):
    """ eg fc25 or el6_7"""
    if name.endswith(".rpm"):
        return _get_ith_dotpart(1, name)
    else:
        return _get_ith_dotpart(1, name + ".rpm")


def get_arch(name):
    """ eg i686 """
    if name.endswith(".rpm"):
        return _get_ith_dotpart(2, name)
    else:
        return _get_ith_dotpart(2, name + ".rpm")


def get_nvra(name):
    """ eg java-1.8.0-openjdk-1.8.0.101-4.b13.el7.i686"""
    if name.endswith(".rpm"):
        sub = get_subpackage_only(name)
        if sub != "":
            name = name.replace("-" + sub, "")
        name = name.replace(".rpm", "")

    return name
