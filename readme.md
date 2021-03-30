# Intro

Generally speaking, the main purpose of JSF is staticaly analyse openjdk RPMS and check whether those match expected state. Majority of the rules is hardcoded in the relevant python scripts.
The framework is capable of testing multiple architectures during a single run by iterating every run the same number of times as the number of architectures provided in the rpm set.
# Initial setup

**Step 1.** - Get your favorite Python IDE, I personally develop in Pycharm community edition.

**Step 2.** - Fork this repository and clone it.

```
git clone https://github.com/your_username/jdk-rpms-specification-framework.git
```

**Step 3.** - Download rpms. The test looks for the rpms in the \*/jdk-rpms-specification-framework/rpms/ directory.
- rpms are usually downlaoded directly from
            -  koji-like systems. Eg: https://koji.fedoraproject.org/koji/packageinfo?packageID=28488
            - bodhi like udpates. eg: https://bodhi.fedoraproject.org/updates/FEDORA-2021-8dab50bea8
            Those two exampel salwatys ends in build, like eg: https://koji.fedoraproject.org/koji/buildinfo?buildID=1724813
          Also:
           rpm based systems allows to download-only throough package manager liek dnf or yum
           or eg Fedora have fedpkg, which can download the task or build by its number (see the BuildID above)

**Step 4.** - Run tests. Tests are runnable both via the main method as well as via running their own respective main as "standalone" python script. The framework will most probably need dependencies (namely koji and mock for starters) installed and will fail during the first run.

For arguments and additional wisdom, feel free to check the old readme:
 https://github.com/andrlos/jdk-rpms-specification-framework/blob/master/readme-old

# Getting started:

To get familiar with the framework try to run subpackages run on a complete set of rpms. You can download the complete set by running main function with parameter
```
-b java_version
```
where instead of *"java_version"* you put any name of package set available on koji.fedoraproject.com.
Sadly the --download-only parameter has not been yet implemented, so you either have to kill it after the download is finished (you can track the progress in *verbose_log_file.log*)or let the whole suite finish (won't take longer that 2 hours if you don't have the mock package installed yet).

