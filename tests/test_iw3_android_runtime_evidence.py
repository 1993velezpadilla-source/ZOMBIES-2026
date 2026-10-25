import unittest

from tools.iw3_android.verify_runtime_evidence import REQUIRED, verify


def real_format_fixture():
    # Parser regression fixture only; never device or gameplay evidence.
    return "\n".join(REQUIRED) + "\n" + "\n".join((
        "IW3_JNI_LIFECYCLE_2",
        "IW3_JNI_TOUCH id=0 pressed=1 coords=0.18421052,0.2962963",
        "IW3_JNI_TOUCH id=0 pressed=0 coords=0.18421052,0.2962963",
        "IW3_JNI_LIFECYCLE_3", "IW3_JNI_LIFECYCLE_2"))


class NativeRuntimeEvidenceTests(unittest.TestCase):
    def test_complete_diagnostic_has_explicit_limits(self):
        result = verify(real_format_fixture())
        self.assertTrue(result["touch_down_and_up_read_back_from_native"])
        self.assertFalse(result["arm64_device_execution_proven"])
        self.assertFalse(result["gameplay_proven"])

    def test_every_required_native_marker_is_necessary(self):
        for marker in REQUIRED:
            with self.subTest(marker=marker), self.assertRaises(ValueError):
                verify(real_format_fixture().replace(marker, ""))

    def test_any_runtime_failure_overrides_passing_markers(self):
        for failure in ("TOUCH_NATIVE_REJECTED", "JNI_RESUME_FAILED",
                        "Fatal signal", "JNI_NATIVE_ENGINE_PROBE_FAIL"):
            with self.subTest(failure=failure), self.assertRaises(ValueError):
                verify(real_format_fixture() + "\n" + failure)

    def test_missing_release_is_not_working_touch(self):
        with self.assertRaises(ValueError):
            verify(real_format_fixture().replace("pressed=0", "pressed=1"))

    def test_wrong_pointer_or_failed_native_readback_is_rejected(self):
        for substitution in ("id=1 pressed=0", "id=0 pressed=-1"):
            with self.subTest(substitution=substitution), self.assertRaises(ValueError):
                verify(real_format_fixture().replace("id=0 pressed=0", substitution))

    def test_invalid_coordinate_is_rejected(self):
        for coord in ("nan", "inf", "-0.1", "1.1"):
            with self.subTest(coord=coord), self.assertRaises(ValueError):
                verify(real_format_fixture().replace("coords=0.18421052,", "coords=" + coord + ","))

    def test_background_and_return_are_both_required(self):
        with self.assertRaises(ValueError):
            verify(real_format_fixture().replace("IW3_JNI_LIFECYCLE_3", ""))
        with self.assertRaises(ValueError):
            verify(real_format_fixture().rsplit("IW3_JNI_LIFECYCLE_2", 1)[0])


if __name__ == "__main__":
    unittest.main()
