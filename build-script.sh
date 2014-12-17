#yes | rm ka-lite-android/ka-lite.zip
#yes | rm -r python-for-android
#zip kalite
python manage.py build -d ka-lite/ --out ka-lite-android
#zip kalite
ant