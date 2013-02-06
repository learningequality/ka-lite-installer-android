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
Crashes can be observed `adb logcat`.

Kivy logs are stored in `/mnt/sdcard/org.kalite.test/.kivy/logs` directory.
