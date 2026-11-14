"""Mock-based precision Park/Service regression tests (no hardware required)."""
import threading
import unittest
from types import SimpleNamespace
from wt8_antenna import SafetyError, SafetyLimits
from wt8_precision import precision_fixed_slew, PositionCancelled, position_errors

def site():
    return SimpleNamespace(az_slow_speed=10, el_slow_speed=10,
        az_stop_tolerance_degrees=0.10, el_stop_tolerance_degrees=0.10,
        az_slow_threshold_degrees=3.0, el_slow_threshold_degrees=3.0)

class FakeSession:
    def __init__(self, readings):
        self.config=SimpleNamespace(
            limits=SafetyLimits(az_min=270,az_max=265,el_min=0,el_max=87),
            az_track_speed=40,el_track_speed=40)
        self.readings=iter(readings)
        self.calls=[]
    def guarded_slew_to(self,*args,**kwargs):
        self.calls.append((args,kwargs))
    def read_position(self):
        az,el=next(self.readings)
        return SimpleNamespace(azimuth=az,elevation=el)

class PrecisionTests(unittest.TestCase):
    def test_both_approach_directions(self):
        for final in (59.91,60.09):
            with self.subTest(final=final):
                s=FakeSession([(final,80.0)])
                p=precision_fixed_slew(s,60,80,threading.Event(),site(),0.5,0.5)
                self.assertAlmostEqual(p.azimuth,final)
                self.assertFalse(s.calls[0][1]['apply_az_low_to_high_compensation'])
    def test_correction_then_success(self):
        s=FakeSession([(60.52,80),(60.06,80)])
        logs=[]
        precision_fixed_slew(s,60,80,threading.Event(),site(),0.5,0.5,
            log_callback=lambda **kw:logs.append(kw))
        self.assertEqual(len(s.calls),2)
        self.assertEqual(s.calls[1][0][2:4],(10,10))
        self.assertEqual(len(logs),2)
    def test_error_after_two_corrections(self):
        s=FakeSession([(61.04,80),(60.6,80),(60.3,80)])
        with self.assertRaises(SafetyError):
            precision_fixed_slew(s,60,80,threading.Event(),site(),0.5,0.5)
        self.assertEqual(len(s.calls),3)
    def test_stop_before_motion(self):
        stop=threading.Event();stop.set()
        s=FakeSession([])
        with self.assertRaises(PositionCancelled):
            precision_fixed_slew(s,60,80,stop,site(),0.5,0.5)
        self.assertEqual(len(s.calls),0)
    def test_unsafe_target_rejected_before_motion(self):
        s=FakeSession([])
        with self.assertRaises(SafetyError):
            precision_fixed_slew(s,266,80,threading.Event(),site(),0.5,0.5)
        self.assertEqual(len(s.calls),0)
    def test_wrapped_error(self):
        limits=SafetyLimits(az_min=270,az_max=265)
        pos=SimpleNamespace(azimuth=359.9,elevation=5)
        self.assertAlmostEqual(position_errors(limits,pos,0,5)[0],0.1)

if __name__=='__main__':
    unittest.main()
