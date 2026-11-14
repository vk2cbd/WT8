"""Unit tests for automatic controller disconnection after verified fixed moves."""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock
from wt8_ubuntu_gui import WT8App

class DisconnectTests(unittest.TestCase):
    def make_app(self):
        app=SimpleNamespace()
        app.emit=Mock()
        return app

    def test_closes_both_controllers_after_verification(self):
        app=self.make_app()
        east=SimpleNamespace(close=Mock())
        west=SimpleNamespace(close=Mock())
        WT8App.disconnect_completed_fixed_move(app,'Park',4,[('East',east),('West',west)])
        east.close.assert_called_once_with()
        west.close.assert_called_once_with()
        app.emit.assert_called_once()
        args=app.emit.call_args.args[1]
        self.assertEqual(args,('Park',4,['East','West'],[]))

    def test_close_failure_is_reported_and_other_controller_still_closes(self):
        app=self.make_app()
        east=SimpleNamespace(close=Mock(side_effect=OSError('serial failure')))
        west=SimpleNamespace(close=Mock())
        WT8App.disconnect_completed_fixed_move(app,'Service',5,[('East',east),('West',west)])
        west.close.assert_called_once_with()
        args=app.emit.call_args.args[1]
        self.assertEqual(args[2],['West'])
        self.assertEqual(args[3],[('East','serial failure')])

if __name__=='__main__':
    unittest.main()
