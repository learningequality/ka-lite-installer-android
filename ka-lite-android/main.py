import sys
import os
import time
from functools import partial, wraps
from zipfile import ZipFile
import threading
import Queue
import kivy
kivy.require('1.0.7')
from kivy.app import App
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.logger import Logger

from kalite_ui import KaliteUI
import logging
logging.root = Logger
from service.main import Server

import webbrowser
from kivy.core.window import Window
from kivy.base import EventLoop 

# import pdb
# pdb.set_trace()

#webview stuff
from kivy.uix.widget import Widget
from kivy.clock import Clock  
from jnius import autoclass, cast
from jnius import PythonJavaClass, java_method
from android.runnable import run_on_ui_thread

from kivy.uix.button import Button
from kivy.uix.popup import Popup

WebView = autoclass('android.webkit.WebView')
Window = autoclass('android.view.Window')
WebViewClient = autoclass('android.webkit.WebViewClient')                                       
android_activity = autoclass('org.renpy.android.PythonActivity').mActivity
System = autoclass('java.lang.System')
#MyWebChromeClient = autoclass('org.eli.MyWebChromeClient')
JavaHandler = autoclass('org.eli.JavaHandler')
#SharedPreferences = autoclass('android.content.SharedPreferences')

class JavaHandle(Widget): 
    def  __init__(self, **kwargs):
        super(JavaHandle, self).__init__(**kwargs)
        #Clock.schedule_once(self.create_webview, 0)
        self.create_webview(**kwargs)

    @run_on_ui_thread   
    def create_webview(self, *args):    
        #JavaHandler.displayInLogCat("catcat create_webview")
        self.java_handle = JavaHandler()
 #       self.java_handle.generateRSA()
       # self.java_handle.initWebView()

    @run_on_ui_thread 
    def run_webview(self):
        self.java_handle.showWebView()

    @run_on_ui_thread 
    def move_content(self):
        #JavaHandler.displayInLogCat("catcat move_content")
        JavaHandler.movingFile()

    # def kill_app(self, server_is_running):
    #     try:
    #         if server_is_running:
    #             from android import AndroidService
    #             AndroidService().stop()
    #         #App.get_running_app().stop()
    #         self.java_handle.killApp()
    #     except IOError:
    #         print "cannot stop AndroidService normally"

    @run_on_ui_thread
    def go_to_previous(self, app, server_is_running):
        if self.java_handle.backPressed():
            if self.java_handle.whetherHomePage():
                self.java_handle.quitDialog()
            else:
                self.java_handle.goBack()
        else:
            self.java_handle.quitDialog()

    @run_on_ui_thread
    def quit_dialog(self):
        self.java_handle.quitDialog()

    @run_on_ui_thread 
    def show_toast(self, string):
        self.java_handle.show_toast(string)

    @run_on_ui_thread
    def reload_first_page(self):
        self.java_handle.reloadFirstPage()

    # def create_RSA(self):
    #     self.java_handle.generateRSA()

#webview stuff

class PythonSharedPreferenceChangeListener(PythonJavaClass):
    __javainterfaces__ = ['android/content/SharedPreferences$OnSharedPreferenceChangeListener']

    def __init__(self):
        super(PythonSharedPreferenceChangeListener, self).__init__()

    @java_method('(Landroid/content/SharedPreferences;Ljava/lang/String;)V')
    def onSharedPreferenceChanged(self, sharedPref, key):
        System.out.println("shshsh callback");
        if sharedPref.getInt("live", 1) == 0:
            try:
                from android import AndroidService
                AndroidService().stop()
                JavaHandler.killApp()
            except IOError:
                print "cannot stop AndroidService normally"


class ServerThread(threading.Thread, Server):
    def __init__(self, app, mwebview):
        super(ServerThread, self).__init__()
        self.web_view = mwebview

        class AppCaller(object):
            '''Execute App method in the main thread'''

            def __getattribute__(self, method_name):
                value = getattr(app, method_name)
                method = callable(value) and value
                if method:
                    def clock(*args, **kwargs):
                        Clock.schedule_once(partial(method, *args, **kwargs),
                                            0)
                    return clock
                return value

        self.app = AppCaller()
        self._stop_thread = threading.Event()
        self.activities = Queue.Queue()

        self.tmp_dir = kivy.kivy_home_dir
        self.pid_file = os.path.join(self.tmp_dir, 'wsgiserver.pid')

        try:
            import __main__
            self.project_dir = os.path.dirname(
                os.path.abspath(__main__.__file__))
        except:
            self.project_dir = os.path.abspath(os.path.curdir)

    def run(self):
        '''Execute queue while not stopped'''

        while not self._stop_thread.isSet():
            try:
                activity_name, description, args = self.activities.get(True,
                                                                       4)
            except Queue.Empty:
                pass
            else:
                activity = getattr(self, activity_name)
                if description:
                    self.app.report_activity('start', description)
                try:
                    result = activity(*args)
                except:
                    self.app.report_activity('result', 'fail')
                    with self.activities.mutex:
                        self.activities.queue.clear()
                    raise
                if description:
                    if result is None:
                        result = 'OK'
                    self.app.report_activity('result', result)

    def schedule(self, activity, description=None, *args):
        self.activities.put((activity, description, args))

    def extract_kalite(self):
        '''KA Lite code is in the ZIP archive on the first run, extract it'''

        os.chdir(self.project_dir)
        if os.path.exists('ka-lite.zip'):
            JavaHandler.unzipKaLite()
    #         with ZipFile('ka-lite.zip', mode="r") as z:
    # #jjj            z.extractall('ka-lite')
    #             z.extractall('.')   #we can change here or change Aron's code
    #         os.remove('ka-lite.zip')
        if not os.path.exists('ka-lite'):
            return 'fail'

    def python_version(self):
        import sys
        return sys.version.split()[0]

    def import_django(self):
        import django
        return django.get_version()

    def setup_environment(self):
        pj = os.path.join
        run_from_egg = sys.path[0].endswith('.zip')
        sys.path.insert(1 if run_from_egg else 0,
                        pj(self.project_dir, 'ka-lite/kalite'))
        sys.path.insert(1 if run_from_egg else 0,
                        pj(self.project_dir, 'ka-lite'))
        sys.path.insert(1, pj(self.project_dir, 'ka-lite/python-packages'))
        os.chdir(pj(self.project_dir, 'ka-lite', 'kalite'))
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kalite.settings')
        self.settings = __import__('settings')
        self.execute_manager = __import__(
            'django.core.management',
            fromlist=('execute_manager',)).execute_manager

    def syncdb(self):
        self.execute_manager(self.settings, ['manage.py', 'syncdb', '--noinput'])
        self.execute_manager(self.settings, ['manage.py', 'migrate', '--merge'])

    #cannot run on ui thread, otherwise it will not show on the schedule page.
    def schedule_reload_content(self):
        if JavaHandler.movingFile():
            return 'Loading finished'
        else:
            #JavaHandler.static_show_toast(android_activity, 'Content folder not found! App exits...')
            self.web_view.show_toast('Content folder not found! App exits...')
            time.sleep(4)
            JavaHandler.killApp()


    def generate_keys(self):
        #from config.models import Settings
        #if Settings.get('private_key'):
        #    return 'key exists'
        JavaHandler.generateRSA()
        #self.execute_manager(self.settings, ['manage.py', 'generatekeys'])

    def create_superuser(self):
        from django.contrib.auth.models import User
        if User.objects.filter(is_superuser=True).exists():
            return 'user exists'

        username = 'yoda'
        email = 'yoda@example.com'
        password = 'yoda'

        self.execute_manager(self.settings, [
                'manage.py', 'createsuperuser',
                '--noinput',
                '--user', username,
                '--email', email])
        user = User.objects.get(username__exact=username)
        user.set_password(password)
        user.save()
        return 'user "{0}" with password "{1}"'.format(username,
                                                       password)

    # def create_superuser(self):
    #     from django.contrib.auth.models import User
    #     if User.objects.filter(is_superuser=True).exists():
    #         return 'user exists'

    #     username = 'yoda'
    #     email = 'yoda@example.com'
    #     password = 'yoda'

    #     self.execute_manager(self.settings, [
    #             'manage.py', 'setup',
    #             '--noinput',
    #             '--user', username,
    #             '--password', password,
    #             '--email', email])
    #    # user = User.objects.get(username__exact=username)
    #   #  user.set_password(password)
    #   #  user.save()
    #     return 'user "{0}" with password "{1}"'.format(username,
    #                                                    password)

    def check_server(self):
        return 'server is running' if self.server_is_running else (
            'server is stopped')

    def start_server(self, threadnum):
        if super(ServerThread, self).start_server(threadnum) == 'fail':
            return 'fail'

        result = 'fail'
        for i in range(30):
            if self.server_is_running:
                result = 'OK'
                break
            else:
                time.sleep(2)
        if result == 'fail':
            self.stop_server()
        return result

    def stop_server(self):
        super(ServerThread, self).stop_server()
        result = 'fail'
        for i in range(30):
            if not self.server_is_running:
                result = 'OK'
                break
            else:
                time.sleep(2)
        return result

    def stop_thread(self):
        self._stop_thread.set()


def clock_callback(f):
    '''Decorator for Clock callbacks'''

    @wraps(f)
    def wrapper(*args, **kwargs):
        # Time diff is passed as an argument, call without it
        return f(*args[:-1], **kwargs)

    return wrapper

class KALiteApp(App):

    server_host = '0.0.0.0'
    # choose a non-default port,
    # to avoid messing with other KA Lite installations
    server_port = '8008'

    progress_tracking = 0
    server_state = False
    thread_num = 'threads=18'
    key_generated = False

    def build(self):
        self.main_ui = KaliteUI(self)
        EventLoop.window.bind(on_keyboard=self.hook_keyboard)
        self.my_webview = JavaHandle()
        self.back_pressed = System.currentTimeMillis()
   #     self.my_webview.create_RSA()
        # self.java_handle = JavaHandler()
        # self.java_handle.initWebView()

        self.pref = android_activity.getSharedPreferences("MyPref", android_activity.MODE_MULTI_PROCESS)
        self.sharedpref_listener = PythonSharedPreferenceChangeListener()
        self.pref.registerOnSharedPreferenceChangeListener(self.sharedpref_listener)

        return self.main_ui.get_root_Layout()

    def on_start(self):
        #check mySettings file
        # settings_path = self.user_data_dir
        # try:
        #     my_setting_file = open(settings_path+'/mySettings.txt', 'r')
        #     if my_setting_file.read() == "allset":
        #         self.key_generated = True
        # except IOError:
        #     print "file has not been created yet"
        if self.pref.getInt("setup", 0) == 1:
            self.key_generated = True

        self.main_ui.add_loading_gif()
        self.kalite = ServerThread(self, self.my_webview)
        self.kalite.start()
        self.prepare_server()
        #self.kalite.start()

    def hook_keyboard(self, window, key, *largs):
        if key == 27:  # BACK
            #JavaHandler.displayInLogCat("backback data: " + str(self.back_pressed) + "  |  " + str(System.currentTimeMillis()))
            if self.back_pressed + 500 > System.currentTimeMillis():
                #JavaHandler.displayInLogCat("backback in 500")
                self.my_webview.quit_dialog()
            else:
                #JavaHandler.displayInLogCat("backback else 500")
                self.my_webview.go_to_previous(App, self.kalite.server_is_running)
            #JavaHandler.displayInLogCat("backback 2 currentTimeMillis")
            self.back_pressed = System.currentTimeMillis()
            #self.my_webview.go_to_previous(App, self.kalite.server_is_running)
        return True

    def on_pause(self):
        return True

        # if self.kalite.server_is_running:
        #     #self.kalite.schedule('stop_server', 'Stop server')
        #     try:
        #         from android import AndroidService
        #         AndroidService().stop()
        #     except IOError:
        #         print "cannot stop AndroidService normally"
        # if self.kalite.is_alive():
        #     self.kalite.schedule('stop_thread')
        #     self.kalite.join()
       # return True

    @clock_callback
    def report_activity(self, activity, message):
        assert activity in ('start', 'result')
        if activity == 'start':
            if hasattr(self, 'activity_label'):
                self.main_ui.remove_messages(self.activity_label)
            self.activity_label = Label(text="{0} ... ".format(message), color=(0.14, 0.23, 0.25, 1))
            self.main_ui.add_messages(self.activity_label)

            self.progress_tracking += 7.5
            self.main_ui.start_progress_bar(self.progress_tracking)

        elif hasattr(self, 'activity_label'):
            # if hasattr(self, 'activity_label'):
            #     self.main_ui.remove_messages(self.activity_label)

            self.activity_label.text = self.activity_label.text + message

            self.progress_tracking += 7.5
            self.main_ui.start_progress_bar(self.progress_tracking)


            if self.progress_tracking >= 97 and message == 'server is stopped':
                self.server_state = True
                self.start_server(self.thread_num)

            if self.progress_tracking >= 97 and message == 'server is running':
                self.server_state = False
                self.my_webview.run_webview()
                self.main_ui.remove_loading_gif()

            if self.progress_tracking >= 97 and message == 'Loading finished':
                JavaHandler.displayInLogCat("rerere finished")
                self.server_state = False
                self.my_webview.run_webview()
                self.main_ui.remove_loading_gif()

            if self.server_state and message == 'OK' and self.progress_tracking >= 97:
                self.server_state = False
                #self.start_webview_button()
                self.my_webview.run_webview()
                self.main_ui.remove_loading_gif()

    def prepare_server(self):
        '''Schedule preparation steps to be executed in the server thread'''

        self.schedule = self.kalite.schedule
        self.schedule('extract_kalite', 'Extracting ka-lite archive')
        # self.my_webview.move_content()
        self.schedule('setup_environment', 'Setting up environment')
        #schedule('python_version', 'Checking Python version')
        self.schedule('import_django', 'Trying to import Django')
        if not self.key_generated:
    #jjj    if 2>3:
    #jjj        schedule('syncdb', 'Preparing database')
            #self.my_webview.move_content()
            self.schedule('generate_keys', 'Generating keys')
            self.schedule('create_superuser', 'Creating admin user')
            self.schedule('schedule_reload_content', 'Loading the content')
            #create a setting file
            # settings_path = self.user_data_dir
            # my_setting_file = open(settings_path+'/mySettings.txt', 'w')
            # my_setting_file.write('allset')
            # my_setting_file.close()
            self.editor = self.pref.edit()
            self.editor.putInt("setup", 1)
            self.editor.apply()
        else:
            self.progress_tracking += 45

        self.schedule('check_server', 'Checking server status')

    def start_server(self, threadnum):
        #self.thread_num = self.main_ui.get_thread_num()
        description = "Run server. To see the KA Lite site, " + (
            "open  http://{}:{} in browser").format(self.server_host,
                                                    self.server_port, threadnum)
        if not self.kalite.server_is_running:
            self.kalite.schedule('start_server', description, threadnum)

    def reload_content(self, widget):
        # self.my_webview.move_content()
        self.progress_tracking -= 30
        self.main_ui.start_progress_bar(self.progress_tracking)
        self.schedule('schedule_reload_content', 'Reloading the content')


    # def start_webview(self, instance, widget):
    #     url = 'http://0.0.0.0:8008/'
    #     webbrowser.open(url)

    # def start_webview_button(self):
    #     url = 'http://0.0.0.0:8008/'
    #     webbrowser.open(url)

    # def start_webview_bubblebutton(self, widget):
    #     self.my_webview.run_webview()
   #     self.main_ui.root_layout.add_widget(self.my_webview.run_webview()) # webview stuff
   #     url = 'http://0.0.0.0:8008/'
   #     webbrowser.open(url)

    # def stop_server(self, widget):
    #     if self.kalite.server_is_running:
    #         self.kalite.schedule('stop_server', 'Stop server')
    #     else:
    #         self.activity_label = Label(text="no running server", color=(0.14, 0.23, 0.25, 1))
    #         self.main_ui.add_messages(self.activity_label)

    @clock_callback
    def start_service_part(self, threadnum):
        from android import AndroidService
        self.service = AndroidService('KA Lite', 'server is running')
        # start executing service/main.py as a service
        self.service.start(':'.join((self.server_host, self.server_port, self.thread_num)))

    @clock_callback
    def stop_service_part(self):
        from android import AndroidService
        AndroidService().stop()


if __name__ == '__main__':
    try:
        KALiteApp().run()
    except Exception as e:
        msg = "Error: {type}{args}".format(type=type(e),
                                            args=e.args)
        Logger.exception(msg)
        raise
