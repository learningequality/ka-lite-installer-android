import sys
import os
import time
from functools import partial
from zipfile import ZipFile
import threading
import Queue
import kivy
kivy.require('1.0.7')
from kivy.uix.gridlayout import GridLayout
from kivy.app import App
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.logger import Logger


class AppLayout(GridLayout):
    pass


class ServerThread(threading.Thread):

    def __init__(self, app):
        super(ServerThread, self).__init__()

        class AppCaller(object):
            '''Execute App method in the main thread'''

            def __getattribute__(self, method_name):
                method = getattr(app, method_name)

                def clock(*args, **kwargs):
                    Clock.schedule_once(partial(method, *args, **kwargs), 0)

                return clock

        self.app = AppCaller()
        self._stop_thread = threading.Event()
        self.activities = Queue.Queue()

        self.tmp_dir = kivy.kivy_home_dir
        self.pid_file = os.path.join(self.tmp_dir, 'wsgiserver.pid')

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
        if self.server_is_running:
            self.stop_server()

    def schedule(self, activity, description=None, *args):
        self.activities.put((activity, description, args))

    def extract_kalite(self, *args):
        z = ZipFile('ka-lite.zip', mode="r")
        z.extractall('ka-lite')
        os.remove('ka-lite.zip')

    def import_django(self, *args):
        import django
        return django.get_version()

    def setup_environment(self, *args):
        PROJECT_PATH = os.path.abspath(os.path.curdir)
        pj = os.path.join
        sys.path.insert(1, pj(PROJECT_PATH, "ka-lite/kalite"))
        sys.path.insert(1, pj(PROJECT_PATH, "ka-lite/python-packages"))
        os.chdir('ka-lite/kalite')
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
        self.settings = __import__('settings')
        self.execute_manager = __import__(
            'django.core.management',
            fromlist=('execute_manager',)).execute_manager

    def syncdb(self, *args):
        self.execute_manager(self.settings, ['manage.py', 'syncdb',
                                   '--migrate',
                                   '--noinput'])

    def generate_keys(self, *args):
        self.execute_manager(self.settings, ['manage.py', 'generatekeys'])

    def create_superuser(self, *args):
        from django.contrib.auth.models import User
        if User.objects.filter(is_superuser=True).exists():
            return 'user exists'

        username = "yoda"
        email = "yoda@example.com"
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

    def start_server(self, server_port, *args):
        stdout, stderr = sys.stdout, sys.stderr
        pj = os.path.join
        try:
            if os.fork() == 0:
                sys.stdout = open(pj(self.tmp_dir, 'wsgiserver.stdout'), 'w')
                sys.stderr = open(pj(self.tmp_dir, 'wsgiserver.stderr'), 'w')
                self.execute_manager(self.settings, [
                        'manage.py', 'runwsgiserver',
                        "port={0}".format(server_port),
                        # 'host=0.0.0.0',
                        'host=127.0.0.1',
                        'daemonize=True',
                        'pidfile={0}'.format(self.pid_file),
                        'threads=3'])
                sys.exit(0)
        except OSError, e:
            Logger.exception("Fork error: {type}{args}".format(type=type(e),
                                                               args=e.args))
            return 'fail'

        result = 'fail'
        for i in range(5):
            if self.server_is_running:
                result = 'OK'
                break
            else:
                time.sleep(2)
        if result == 'fail':
            self.stop_server()
        return result

    def stop_server(self, *args):
        self.execute_manager(self.settings, [
                'manage.py', 'runwsgiserver',
                'pidfile={0}'.format(self.pid_file),
                'stop'
                ])
        if self.server_is_running:
            return 'fail'

    @property
    def server_is_running(self):
        result = False
        if os.path.exists(self.pid_file):
            try:
                pid = int(open(self.pid_file).read())
            except ValueError:
                pass
            else:
                try:
                    os.kill(pid, 0)
                except OSError:
                    pass
                else:
                    result = True
        return result

    def stop_thread(self, *args):
        self._stop_thread.set()


class KALiteApp(App):

    server_port = '8024'

    def build(self):
        self.layout = AppLayout()
        return self.layout

    def on_start(self):
        self.kalite = ServerThread(self)
        self.prepare_server()
        self.kalite.start()

    def on_pause(self):
        return True

    def on_stop(self):
        if self.kalite.is_alive():
            self.stop_server()
            self.kalite.schedule('stop_thread')
            self.kalite.join()

    def report_activity(self, activity, message, *args):
        assert activity in ('start', 'result')
        if activity == 'start':
            self.activity_label = Label(text="{0} ... ".format(message))
            self.layout.add_widget(self.activity_label)
        elif hasattr(self, 'activity_label'):
            self.activity_label.text = self.activity_label.text + message

    def prepare_server(self):
        schedule = self.kalite.schedule
        first_run = False
        if os.path.exists('ka-lite.zip'):
            schedule('extract_kalite', 'Extracting ka-lite archive')
            first_run = True
        schedule('setup_environment', 'Setup environment')
        schedule('import_django', 'Try to import Django')
        schedule('syncdb', 'Prepare database')
        if first_run:
            schedule('generatekeys', 'Generate keys')
        schedule('create_superuser', 'Create admin user')
        schedule('check_server', 'Check server status')
        self.start_server()

    def start_server(self):
        description = "Run server. To see the KA Lite site, " + (
            "open  http://127.0.0.1:{0} in browser").format(self.server_port)
        if not self.kalite.server_is_running:
            self.kalite.schedule('start_server', description, self.server_port)

    def stop_server(self):
        if self.kalite.server_is_running:
            self.kalite.schedule('stop_server', 'Stop server')

if __name__ == '__main__':
    try:
        KALiteApp().run()
    except Exception as e:
        msg = "Error: {type}{args}".format(type=type(e),
                                            args=e.args)
        Logger.exception(msg)
        raise