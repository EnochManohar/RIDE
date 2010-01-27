import unittest
import time
import os
from robot.utils.asserts import assert_equals, assert_true

from robotide.run.runanything import _RunConfig
from robotide.run.ui import Runner
from resources import PYAPP_REFERENCE as _


SCRIPT = os.path.join(os.path.dirname(__file__), 'process_test_scripts.py')


class _TestableRunner(Runner):
    output = property(lambda self: self._window.output)
    outstr = property(lambda self: self._window.outstr)
    finished = property(lambda self: self._window.finished)
    def _get_output_window(self, notebook):
        return _FakeOutputWindow()

class _FakeOutputWindow(object):
    outstr = property(lambda self: ''.join(self.output))
    def __init__(self):
        self.output = []
    def update_output(self, output, finished):
        self.output.append(output)
        self.finished = finished


class TestRunAnything(unittest.TestCase):

    def test_run(self):
        self.runner = self._create_runner('echo test test')
        self._wait_until_finished()
        self._assert_output('test test\n')

    def _assert_output(self, output):
        assert_equals(self.runner.outstr, output)
        assert_true(self.runner.finished)

    def test_stopping(self):
        self.runner = self._create_runner('python %s output 0.8' % SCRIPT)
        time.sleep(0.1)
        self.runner.stop()
        self._sleep_and_log_output(0.5)
        assert_true(self.runner.finished)
        assert_true(self.runner.outstr.startswith('start\nrunning '))

    def test_error(self):
        self.runner = self._create_runner('invalid command')
        self._wait_until_finished()
        assert_true(self.runner.outstr)
        assert_true(self.runner.finished)

    def test_output(self):
        self.runner = self._create_runner('python %s output' % SCRIPT)
        self._sleep_and_log_output(0.5)
        length = len(self.runner.outstr)
        assert_true(length > 0)
        self._wait_until_finished()
        assert_true(len(self.runner.outstr) > length)
        assert_true(self.runner.outstr.endswith('done\n'))

    def _create_runner(self, cmd):
        runner = _TestableRunner(_RunConfig('test', cmd, ''), None)
        runner.run()
        return runner

    def _wait_until_finished(self):
        while not self.runner._process.is_finished():
            time.sleep(0.1)
        self.runner.OnTimer()

    def _sleep_and_log_output(self, amount):
        time.sleep(amount)
        self.runner.OnTimer()
