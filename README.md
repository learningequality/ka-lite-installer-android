ka-lite-android
===============

Android port of KA Lite (an offline version of Khan Academy), encapsulating the Django project.

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

Build
-----
To build the apk, run the _ant_ with the folowing properties:

* android-sdk - Path to the Android SDK (will ask if not set)
* android-ndk - Path to the Android NDK (will ask if not set)
* android-api - Android API version (default is 14)
* android-ndkver - Android NDK version (default is r8c)

Command could look like this:

    ant -Dandroid-sdk=/path/to/android/sdk -Dandroid-ndk=/path/to/android/ndk -Dandroid-api=14 -Dandroid-ndkver=r8c


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
