import sys
import os
import time
import socket
import threading
from kivy.logger import Logger
from kivy.utils import platform
import kivy
pj = os.path.join

import logging
logging.root = Logger

class ChronographThread(threading.Thread):
    timeout = 10

    def run(self):
        from chronograph.models import Job
        while not 'rest' in 'peace':
            jobs = Job.objects.due()
            if jobs.count():
                for job in jobs:
                    job.run()
            else:
                time.sleep(self.timeout)


class KALiteServer(object):

    def redirect_output(self):
        if hasattr(sys.stdout, 'close'):
            sys.stdout.close()
        if hasattr(sys.stderr, 'close'):
            sys.stderr.close()
        tmp_dir = getattr(self, 'tmp_dir', kivy.kivy_home_dir)
        sys.stdout = open(pj(tmp_dir, 'wsgiserver.stdout'), 'a', 0)
        sys.stderr = open(pj(tmp_dir, 'wsgiserver.stderr'), 'a', 0)

    def workaround(self):

        def ensure_dir(path):    
            """Create the entire directory path, if it doesn't exist already."""
            path_parts = path.split("/")
            full_path = "/"
            for part in path_parts:
                #if "." in part:
                #    raise InvalidDirectoryFormat()
                if part is not '':
                    full_path += part + "/"
                    if not os.path.exists(full_path):
                        os.makedirs(full_path)
        from fle_utils import general
        general.ensure_dir  = ensure_dir


    def setup_chronograph(self):
        if not hasattr(self, 'start_wsgiserver'):
            # monkey-patching wsgiserver, to start the chronograph thread
            from django_cherrypy_wsgiserver.management.commands import (
                runcherrypyserver)
            import cherrypy
            self.start_wsgiserver = cherrypy.quickstart

            def monkey_start_server(*args, **kwargs):
                '''
                Run a chronograph thread, then start the server.
                This function is called after the daemonization.
                '''
                self.workaround()
                self.redirect_output()
                ChronographThread().start()
                return self.start_wsgiserver(*args, **kwargs)
            cherrypy.quickstart = monkey_start_server

    def start_server(self, threadnum):
        self.setup_chronograph()
        try:
            if os.fork() == 0:
                #self.redirect_output()
                self.execute_manager(self.settings, [
                        'manage.py', 'runcherrypyserver',
                        "host={}".format(self.app.server_host),
                        "port={}".format(self.app.server_port),
                        "pidfile={}".format(self.pid_file),
                        'daemonize=True',
                        threadnum,
                        '--verbose'])
                # self.execute_manager(self.settings, [
                #         'manage.py', 'kaserve',
                #         "host={}".format(self.app.server_host),
                #         "pidfile={}".format(self.pid_file),
                #         'daemonize=true',
                #         'production=true',
                #         'threads=3'])
                sys.exit(0)
        except OSError, e:
            Logger.exception("Fork error: {type}{args}".format(type=type(e),
                                                               args=e.args))
            return 'fail'

    def stop_server(self):
        self.execute_manager(self.settings, [
                'manage.py', 'runcherrypyserver',
                'pidfile={0}'.format(self.pid_file),
                'stop'
                ])

    @property
    def server_is_running(self):
        result = False
        if os.path.exists(self.pid_file):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.connect((self.app.server_host, int(self.app.server_port)))
            except socket.error:
                pass
            else:
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
            finally:
                sock.close()
        return result


class AndroidServer(KALiteServer):

    def start_server(self, threadnum):
        self.app.start_service_part(threadnum)

    def stop_server(self):
        self.app.stop_service_part()

    @property
    def server_is_running(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((self.app.server_host, int(self.app.server_port)))
        except socket.error:
            return False
        return True

    def _start_server(self, host, port, threadnum):

        tmp_dir = kivy.kivy_home_dir
        pid_file = os.path.join(tmp_dir, 'wsgiserver.pid')

        import __main__
        project_dir = os.path.dirname(os.path.abspath(
                pj(__main__.__file__, '..')))
        sys.path.insert(1, pj(project_dir, 'ka-lite/kalite'))
        sys.path.insert(1, pj(project_dir, 'ka-lite'))
        sys.path.insert(1, pj(project_dir, 'ka-lite/python-packages'))
        os.chdir(pj(project_dir, 'ka-lite', 'kalite'))
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kalite.settings')

        self.setup_chronograph()

        import settings
        from django.core.management import execute_manager
        execute_manager(settings, [
                'manage.py', 'runcherrypyserver',
                "host={}".format(host),
                "port={}".format(port),
                # "pidfile={}".format(pid_file),
                # 'daemonize=True',
                'daemonize=False',
                threadnum])


if platform() == 'android':
    Server = AndroidServer
else:
    Server = KALiteServer


if __name__ == '__main__':
    # executed by the service part

    if platform() == 'android':
        host, port, ThreadNum = os.getenv('PYTHON_SERVICE_ARGUMENT').split(':')
        AndroidServer()._start_server(host, port, ThreadNum)
