import unittest
from wt8_antenna import SafetyError, SafetyLimits, AntennaConfig
from wt8_service import validate_service_target

class ServiceTargetTests(unittest.TestCase):
    def setUp(self):
        self.limits=SafetyLimits(az_min=270.0,az_max=265.0,el_min=0.0,el_max=87.0,az_margin=0.5,el_margin=0.5)

    def test_default_position_is_allowed(self):
        validate_service_target(self.limits,0.0,5.0,0.2,0.2)

    def test_default_config(self):
        config=AntennaConfig(name="East",port="/dev/null")
        self.assertEqual((config.service_az,config.service_el),(0.0,5.0))

    def test_forbidden_sector(self):
        with self.assertRaises(SafetyError):
            validate_service_target(self.limits,267.0,5.0)

    def test_azimuth_limit_margin(self):
        with self.assertRaises(SafetyError):
            validate_service_target(self.limits,264.8,5.0,0.2,0.2)

    def test_lower_elevation_limit_margin(self):
        with self.assertRaises(SafetyError):
            validate_service_target(self.limits,0.0,0.6,0.2,0.2)

    def test_upper_elevation_limit_margin(self):
        with self.assertRaises(SafetyError):
            validate_service_target(self.limits,0.0,86.4,0.2,0.2)

    def test_nonfinite(self):
        for az,el in ((float("nan"),5.0),(0.0,float("inf"))):
            with self.assertRaises(SafetyError):
                validate_service_target(self.limits,az,el)

    def test_out_of_range_azimuth(self):
        with self.assertRaises(SafetyError):
            validate_service_target(self.limits,360.0,5.0)

if __name__=="__main__":
    unittest.main()
