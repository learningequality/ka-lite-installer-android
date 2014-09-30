yes | rm ka-lite-android/ka-lite.zip
#yes | rm -r python-for-android
yes | rm ka-lite-android/main.pyo
yes | rm ka-lite-android/service/*.pyo
ant -Dandroid-sdk=/Users/Eli/AndroidADT/adt-bundle-mac-x86_64-20140702/sdk -Dandroid-ndk=/Users/Eli/Downloads/android-ndk-r8c -Dandroid-api=14 -Dandroid-ndkver=r8c
cd /Users/Eli/AndroidADT/adt-bundle-mac-x86_64-20140702/sdk/platform-tools 
./adb shell pm uninstall org.kalite.test
./adb install /Users/Eli/Desktop/kaliteandroid78/python-for-android/dist/default/bin/KALitetest-0.12.0-debug.apk
cd /Users/Eli/Desktop/kaliteandroid78
say -v Bells "Eli"
#./adb shell am start -n org.kalite.test/.PythonActivity