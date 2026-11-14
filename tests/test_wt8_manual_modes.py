"""WT8 manual jog mode tests (no physical antenna required)."""
import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PyQt5.QtWidgets import QApplication, QLabel
from wt8_ubuntu_gui import AntennaCard, WT8App
from wt8_antenna import Direction

class ManualModeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt=QApplication.instance() or QApplication([])
    def setUp(self):
        self.card=AntennaCard('East')
        self.app=SimpleNamespace()
        self.app.manual_axes={}
        self.app.manual_pending={}
        self.app.manual_modes={'East':'LATCHED'}
        self.app.sessions={'East':object()}
        self.app.cards={'East':self.card}
        self.app.source_name=QLabel('Target --')
        self.app.source_az=QLabel('--.--')
        self.app.source_el=QLabel('--.--')
        self.app.source_ha=QLabel('--')
        self.app.service_active=False
        self.app.park_active=False
        self.app.tracking_kind=''
        self.app.tracking_starting=False
        self.app.scan_thread=None
        self.app.peak_thread=None
        self.app.yfactor_active=False
        self.app.set_status=Mock()
        self.app.launch_manual_axis=Mock(side_effect=self.fake_launch)
        self.app.stop_jog=lambda name:WT8App.stop_jog(self.app,name)
        self.app.stop_manual_axis=lambda name,axis:WT8App.stop_manual_axis(self.app,name,axis)
        self.app.manual_axis=lambda d:WT8App.manual_axis(self.app,d)
        self.app.refresh_manual_display=lambda n:WT8App.refresh_manual_display(self.app,n)
    def fake_launch(self,name,axis,direction,session):
        self.app.manual_axes[(name,axis)]={'direction':direction,'stop':__import__('threading').Event()}
        self.app.refresh_manual_display(name)
    def press(self,d):
        WT8App.start_jog(self.app,'East',d.value)
    def test_latched_simultaneous_axes_and_independent_toggle(self):
        self.press(Direction.EL_UP)
        self.press(Direction.AZ_CW)
        self.assertEqual(len(self.app.manual_axes),2)
        self.assertIn('N',self.card.manual_summary.text())
        self.assertIn('E',self.card.manual_summary.text())
        self.press(Direction.EL_UP)
        self.assertTrue(self.app.manual_axes[('East','EL')]['stop'].is_set())
        self.assertFalse(self.app.manual_axes[('East','AZ')]['stop'].is_set())
    def test_reverse_stops_before_new_worker(self):
        self.press(Direction.AZ_CW)
        self.press(Direction.AZ_CCW)
        self.assertTrue(self.app.manual_axes[('East','AZ')]['stop'].is_set())
        self.assertEqual(self.app.manual_pending[('East','AZ')],Direction.AZ_CCW.value)
        self.assertEqual(self.app.launch_manual_axis.call_count,1)
    def test_momentary_release_stops_only_matching_axis(self):
        self.app.manual_modes['East']='MOMENTARY'
        self.press(Direction.EL_UP)
        self.press(Direction.AZ_CW)
        WT8App.release_jog(self.app,'East',Direction.EL_UP.value)
        self.assertTrue(self.app.manual_axes[('East','EL')]['stop'].is_set())
        self.assertFalse(self.app.manual_axes[('East','AZ')]['stop'].is_set())
    def test_released_momentary_reverse_does_not_start_later(self):
        self.app.manual_modes['East']='MOMENTARY'
        self.press(Direction.AZ_CW)
        self.press(Direction.AZ_CCW)
        WT8App.release_jog(self.app,'East',Direction.AZ_CCW.value)
        self.assertNotIn(('East','AZ'),self.app.manual_pending)

if __name__=='__main__':
    unittest.main()
