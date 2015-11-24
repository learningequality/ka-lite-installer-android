Notice
===============
This installer project is abandoned. [The new installer](https://github.com/learningequality/ka-lite-android-installer-python27) adopts android-python27 and is structured in Eclipse ADT.

KA Lite Wrapper for Android
===============

Android port of KA Lite (an offline version of Khan Academy), encapsulating the Django project.
please run $ git clone —recursive https://github.com/learningequality/ka-lite-installer-android.git
to clone the submodule inside this repo

Version info
------------
*This version is only for testing.*
[Kivy](https://github.com/kivy/kivy) and
[Python for Android](https://github.com/kivy/python-for-android)
is used to build Python powered apk.


Build Requirements
------------------
See [Python for Android prerequisites](http://python-for-android.readthedocs.org/en/latest/prerequisites/).

Installed Python, Git, Apache Ant, Android SDK, and Android NDK are definitely needed.

You'll need to ensure you have the development headers for sqlite3 installed: `sudo apt-get install libsqlite3-dev`.

You also want to ensure you have ia32-libs installed. If you are running Ubuntu 14.04, you need to run the following commands in order to install it.

	sudo -i
	cd /etc/apt/sources.list.d
	echo "deb http://old-releases.ubuntu.com/ubuntu/ raring main restricted universe multiverse" >ia32-libs-raring.list
	apt-get update
	apt-get install ia32-libs
	rm /etc/apt/sources.list.d/ia32-libs-raring.list
	apt-get update
	exit
    sudo apt-get install gcc-multilib openjdk-7-jdk

Build
-----
To build the apk, first setup the environment with the following command:

	export ANDROIDAPI=<Android API version(must be 14 !!)> 
	export ANDROIDNDKVER=<Android NDK version> 
	export ANDROIDSDK=<Path to the Android SDK> 
	export ANDROIDNDK=<Path to the Android NDK(default is r8c)> 

Navigate to the ka-lite-installer-android folder, then run the build-script(this is a SHELL script file) file from that folder

After the build process finished, you should be able to find the APK inside the python-for-android/dist/default/bin folder.

Debug
-----
Crashes can be observed with `adb logcat`.

Kivy logs are stored in `/mnt/sdcard/org.kalite.test/.kivy/logs` directory.


Run without building
--------------------
To run _ka-lite-android_ without building Android application:

   * install Kivy (see [Kivy installation](http://kivy.org/docs/installation/installation.html))
   * prepare KA Lite: `ant ka-lite`
   * launch `ka-lite-android/main.py`
