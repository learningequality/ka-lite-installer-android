import sys
import os
import time
from functools import partial, wraps
from zipfile import ZipFile
import threading
import Queue
import kivy
from kivy.core.window import Window
Window.clearcolor = (1, 1, 1, 1)
kivy.require('1.0.7')
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.app import App
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.logger import Logger

import logging
logging.root = Logger

from service.main import Server

import webbrowser
from kivy.uix.progressbar import ProgressBar
from kivy.animation import Animation
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle
# import pdb
# pdb.set_trace()

class AppLayout(GridLayout):
    pass


class ServerThread(threading.Thread, Server):
    def __init__(self, app):
        super(ServerThread, self).__init__()

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
            with ZipFile('ka-lite.zip', mode="r") as z:
                z.extractall('ka-lite')
            os.remove('ka-lite.zip')
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

    def generate_keys(self):
        #from config.models import Settings
        #if Settings.get('private_key'):
        #    return 'key exists'
        self.execute_manager(self.settings, ['manage.py', 'generatekeys'])

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


class _BoxLayout(BoxLayout):
    def __init__(self, **kwargs):
        super(_BoxLayout, self).__init__(**kwargs)
        with self.canvas.before:
            Color(0.878, 0.941, 0.784)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size


class KALiteApp(App):

    server_host = '0.0.0.0'
    # choose a non-default port,
    # to avoid messing with other KA Lite installations
    server_port = '8008'

    progress_bar = None
    textinput = None

    a = 0
    serverStop = False
    ThreadNum = None
    gif_img = None

    def build(self):
        self.layout = AppLayout()

        logohoulder = _BoxLayout(orientation='horizontal')
        log_img = Image(source='horizontal-logo.png')
        #log_img.pos_hint={'x': 0, 'center_y': .5}
        logohoulder.padding = [20,10,Window.width-250,0]
        logohoulder.add_widget(log_img)

        self.layout.add_widget(logohoulder)

        #create BubbleButtons
        my_bub_btn1= Button(text='OpenBrowser', font_size=30
            , color=(0.14, 0.23, 0.25, 1), bold=True)
        my_bub_btn1.background_normal='green_button_up.png'
        my_bub_btn1.bind(on_press=self.start_webview_bubblebutton)

        my_bub_btn2= Button(text='Exit', font_size=30
            , color=(0.14, 0.23, 0.25, 1), bold=True)
        my_bub_btn2.background_normal='green_button_up.png'
        my_bub_btn2.bind(on_press=self.quit_app)

        my_bub_btn3= Button(text='thread', font_size=30
            , color=(0.14, 0.23, 0.25, 1), bold=True)
        my_bub_btn3.background_normal='green_button_up.png'
        my_bub_btn3.bind(on_press=self.getThreadNum)

        my_bub_btn4= Button(text='StopServer', font_size=30
            , color=(0.14, 0.23, 0.25, 1), bold=True)
        my_bub_btn4.background_normal='green_button_up.png'
        my_bub_btn4.bind(on_press=self.stop_server)

        my_bub_btn5= Button(text='StartServer', font_size=30
            , color=(0.14, 0.23, 0.25, 1), bold=True)
        my_bub_btn5.background_normal='green_button_up.png'
        my_bub_btn5.bind(on_press=self.start_server)


        buttonsholder = _BoxLayout(orientation='horizontal')
        buttonsholder.padding = [10,0,10,0]
        buttonsholder.add_widget(my_bub_btn1)
        buttonsholder.add_widget(my_bub_btn2)
        buttonsholder.add_widget(my_bub_btn3)
        buttonsholder.add_widget(my_bub_btn4)
        buttonsholder.add_widget(my_bub_btn5)

        self.layout.add_widget(buttonsholder)

        #image stuff
        self.img_holder = BoxLayout(orientation='vertical', size=(200,200), size_hint=(1, None))
        self.img_holder.padding = [0,80,0,10]
        self.layout.add_widget(self.img_holder)

        #thread input box
        textinputholder = BoxLayout(orientation='horizontal')
        textinputholder.padding = [200,10,200,10]

        self.textinput = TextInput(multiline=False, 
            hint_text="Enter number of threads here:")
        self.textinput.padding = [10,10,10,10]
        textinputholder.add_widget(self.textinput)

        self.progress_bar = ProgressBar()
        
        self.server_box = BoxLayout(orientation='horizontal')
        self.messages = BoxLayout(orientation='vertical')

        self.layout.add_widget(self.messages)
        self.layout.add_widget(self.server_box)
        self.layout.add_widget(textinputholder)
        self.layout.add_widget(self.progress_bar)

        return self.layout

    def on_start(self):
        self.kalite = ServerThread(self)
        # self.prepare_server()
        # self.kalite.start()

    def on_pause(self):
        return True

    def on_stop(self):
        if self.kalite.is_alive():
            self.kalite.schedule('stop_thread')
            self.kalite.join()

    def getThreadNum(self, widget):
        self.gif_img = Image(source='loading.zip',  anim_delay = 0.15)
        self.img_holder.add_widget(self.gif_img)

        self.ThreadNum = 'threads=' + self.textinput.text
        self.prepare_server()
        self.kalite.start()

    @clock_callback
    def report_activity(self, activity, message):
        assert activity in ('start', 'result')
        if activity == 'start':
            if hasattr(self, 'activity_label'):
                self.messages.remove_widget(self.activity_label)
            self.activity_label = Label(text="{0} ... ".format(message), color=(0.14, 0.23, 0.25, 1))
            self.messages.add_widget(self.activity_label)

            self.a += 6.25
            anim = Animation(value = self.a, duration = 1)
            anim.start(self.progress_bar)

        elif hasattr(self, 'activity_label'):
            self.activity_label.text = self.activity_label.text + message

            self.a += 6.25
            anim = Animation(value = self.a, duration = 1)
            anim.start(self.progress_bar)


            if self.a >= 97 and message == 'server is stopped':
                self.serverStop = True
                self.start_server(self.ThreadNum)

            if self.a >= 97 and message == 'server is running':
                anim.bind(on_complete = self.start_webview)
                self.img_holder.remove_widget(self.gif_img)

            if self.serverStop and message == 'OK':
                self.serverStop = False
                self.start_webview_button()
                self.img_holder.remove_widget(self.gif_img)

    def prepare_server(self):
        '''Schedule preparation steps to be executed in the server thread'''

        schedule = self.kalite.schedule
        schedule('extract_kalite', 'Extracting ka-lite archive')
        schedule('setup_environment', 'Setting up environment')
        schedule('python_version', 'Checking Python version')
        schedule('import_django', 'Trying to import Django')
        schedule('syncdb', 'Preparing database')
        schedule('generate_keys', 'Generating keys')
        schedule('create_superuser', 'Creating admin user')
        schedule('check_server', 'Checking server status')

    def start_server(self, threadnum):
        self.ThreadNum = 'threads=' + self.textinput.text
        description = "Run server. To see the KA Lite site, " + (
            "open  http://{}:{} in browser").format(self.server_host,
                                                    self.server_port, threadnum)
        if not self.kalite.server_is_running:
            self.kalite.schedule('start_server', description, threadnum)

    def start_webview(self, instance, widget):
        url = 'http://0.0.0.0:8008/'
        webbrowser.open(url)

    def start_webview_button(self):
        url = 'http://0.0.0.0:8008/'
        webbrowser.open(url)

    def start_webview_bubblebutton(self, widget):
        url = 'http://0.0.0.0:8008/'
        webbrowser.open(url)

    def quit_app(self, widget):
        self.stop_server(widget)
        App.get_running_app().stop()

    def stop_server(self, widget):
        if self.kalite.server_is_running:
            self.kalite.schedule('stop_server', 'Stop server')

    @clock_callback
    def start_service_part(self, threadnum):
        from android import AndroidService
        self.service = AndroidService('KA Lite', 'server is running')
        # start executing service/main.py as a service
        self.service.start(':'.join((self.server_host, self.server_port, self.ThreadNum)))

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
