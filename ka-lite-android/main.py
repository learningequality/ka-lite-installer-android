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


class AppLayout(GridLayout):
    messages = ''
    activities = []
    server_port = '8024'

    def schedule(self, activity, description):
        self.activities.append((activity, description))

    def execute_schedule(self):

        def callback(activity, msg_widget, *args):
            time.sleep(2)
            result = activity(args)
            if result is None:
                result = 'OK'
            msg_widget.text = msg_widget.text + result
            self.execute_schedule()

        try:
            activity_name, description = self.activities.pop(0)
        except IndexError:
            pass
        else:
            activity = getattr(self, activity_name)
            msg_widget = Label(text="{0} ... ".format(description))
            self.add_widget(msg_widget)
            Clock.schedule_once(partial(callback, activity, msg_widget))

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

    def runserver(self, *args):
        self.execute_manager(self.settings, [
                'manage.py', 'runwsgiserver',
                "port={0}".format(self.server_port),
                # 'host=0.0.0.0',
                'host=127.0.0.1',
                'threads=3'])

    def run_all(self, *args):
        first_run = False
        if os.path.exists('ka-lite.zip'):
            self.schedule('extract_kalite', 'Extracting ka-lite archive')
            first_run = True
        self.schedule('setup_environment', 'Setup environment')
        self.schedule('import_django', 'Try to import Django')
        self.schedule('syncdb', 'Prepare database')
        if first_run:
            self.schedule('generatekeys', 'Gen keys')
        self.schedule('runserver',
                      "Run server. To see the KA Lite site, open " +
                      "http://127.0.0.1:{0} in browser".format(
                self.server_port))
        self.execute_schedule()


class KALiteApp(App):

    def build(self):
        layout = AppLayout()
        Clock.schedule_once(layout.run_all, 1)
        return layout

if __name__ == '__main__':
    try:
        KALiteApp().run()
    except Exception as e:
        msg = "Error: {type}{args}".format(type=type(e),
                                            args=e.args)
        print msg
        raise
