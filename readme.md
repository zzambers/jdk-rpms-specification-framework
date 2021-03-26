# Intro

Generally speaking, the main purpose of JSF is to help Java QE team maintain certain level of package quality, by testing sets of rpms of openjdk product. Majority of the rules is hardcoded in the relevant python scripts.
The framework is capable of testing multiple architectures during a single run by iterating every run the same number of times as the number of architectures provided in the rpm set.
# Starting up

**Step 1.** - Getting pycharm community edition.

**Step 2.** - Fork this repository.

**Step 3.** - Clone the fork to your computer.

```
git clone https://github.com/your_username/jdk-rpms-specification-framework.git
```

**Step 4.** - Download rpms. The test looks for the rpms in the \*/jdk-rpms-specification-framework/rpms/ directory.

**Step 5.** - Run tests. Tests are runnable both via the main method as well as via running their own respective main as "standalone" python script. The framework will most probably need dependencies (namely koji for starters) installed and will fail during the first run.

# Assignements:

# **First assignment** will be to get familiar with the framework. 
- First task will be to run subpackages run on a complete set of rpms. You can download the complete set by running main function with parameter
```
-b java_version
```
where instead of *"java_version"* you put any name of package set available on koji.fedoraproject.com.
Sadly the --download-only parameter has not been yet implemented, so you either have to kill it after the download is finished (you can track the progress in *verbose_log_file.log*)or let the whole suite finish (won't take longer that 2 hours if you don't have the mock package installed yet).

- Second task in this assignment will be to run separately the subpackage_tests (under nameTest directory). This should produce several failures that should be fairly easy to fix. The test consists of many classes representing individual openjdk versions (openjdk7, openjdk8, openjdk9 etc). There are many versions that are already obsolete right now and the script is unnecessarily long. Your task will be to remove the extra classes. However, beware, as almost every class is ancestor to another class, and the overall functionality must be retained. Also remove only ojdk classes. Don't touch anything *IBM*, *ITW* or *Oracle* related as even I am not sure what is still relevant over there :D . 
The versions we want to keep are: ojdk8, ojdk11 and ojdkLatest. Along with all their respective variants (OpenJdk8Debug, OpenJdk11armv7hl etc...).

- For the third task we will stay a little longer within the subpackages_test. There are several failures that can be observed when the test is run. Those should all be due to the not so recent changes in the rpm sets (those are constantly being changed). The third task will be to repair these failures within the test (remove/add expected packages in the respective classes).
