import sys
import os
import time
from functools import partial
from zipfile import ZipFile
import kivy
kivy.require('1.0.7')
from kivy.uix.gridlayout import GridLayout
from kivy.app import App
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.logger import Logger
import threading


class AppLayout(GridLayout):
    pass


class ServerThread(threading.Thread):
    messages = ''
    activities = []
    server_port = '8024'

    def __init__(self, app):
        super(ServerThread, self).__init__()
        self.app = app

    def run(self):
        first_run = False
        if os.path.exists('ka-lite.zip'):
            self.schedule('extract_kalite', 'Extracting ka-lite archive')
            first_run = True
        self.schedule('setup_environment', 'Setup environment')
        self.schedule('import_django', 'Try to import Django')
        self.schedule('syncdb', 'Prepare database')
        if first_run:
            self.schedule('generatekeys', 'Generate keys')
        self.schedule('create_superuser', 'Create admin user')
        self.schedule('runserver',
                      "Run server. To see the KA Lite site, open " +
                      "http://127.0.0.1:{0} in browser".format(
                self.server_port))
        self.execute_schedule()

    def schedule(self, activity, description):
        self.activities.append((activity, description))

    def execute_schedule(self):
        try:
            activity_name, description = self.activities.pop(0)
        except IndexError:
            pass
        else:
            activity = getattr(self, activity_name)
            Clock.schedule_once(partial(self.app.report_activity,
                                        'start', description),
                                0)
            result = activity()
            if result is None:
                result = 'OK'
            Clock.schedule_once(partial(self.app.report_activity,
                                        'result', result),
                                0)
        self.execute_schedule()

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

    def runserver(self, *args):
        self.execute_manager(self.settings, [
                'manage.py', 'runwsgiserver',
                "port={0}".format(self.server_port),
                # 'host=0.0.0.0',
                'host=127.0.0.1',
                'threads=3'])


class KALiteApp(App):

    def build(self):
        self.layout = AppLayout()
        return self.layout

    def on_start(self):
        self.kalite = ServerThread(self)
        self.kalite.start()

    def report_activity(self, activity, message, *args):
        assert activity in ('start', 'result')
        if activity == 'start':
            self.activity_label = Label(text="{0} ... ".format(message))
            self.layout.add_widget(self.activity_label)
        elif hasattr(self, 'activity_label'):
            self.activity_label.text = self.activity_label.text + message


if __name__ == '__main__':
    try:
        KALiteApp().run()
    except Exception as e:
        msg = "Error: {type}{args}".format(type=type(e),
                                            args=e.args)
        Logger.exception(msg)
        raise
