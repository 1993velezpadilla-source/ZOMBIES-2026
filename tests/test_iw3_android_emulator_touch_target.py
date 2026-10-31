import unittest

from tools.iw3_android.parse_touch_target import select_target


class AndroidTouchTargetTests(unittest.TestCase):
    def test_quickstep_wait_uses_actual_ui_bounds_not_node_extent_scale(self):
        # Captured failure from run 40648979506: screenshot is 2280x1080,
        # while the modal's largest node ends at y=842. Scaling by that node
        # extent incorrectly moved the tap from y=710 to y=911, below Wait.
        xml = """<?xml version='1.0'?>
        <hierarchy rotation="1">
          <node text="" class="android.widget.FrameLayout" package="android"
                bounds="[333,303][1814,842]">
            <node text="Quickstep isn't responding"
                  resource-id="android:id/alertTitle"
                  class="android.widget.TextView" package="android"
                  bounds="[443,397][1704,471]" />
            <node text="Wait" resource-id="android:id/aerr_wait"
                  class="android.widget.Button" package="android"
                  bounds="[377,644][1770,776]" />
          </node>
        </hierarchy>"""
        self.assertEqual(
            select_target(xml, 2280, 1080),
            ("quickstep_anr", 1073, 710),
        )

    def test_app_target_uses_direct_display_coordinates(self):
        xml = """<hierarchy rotation="1">
          <node text="diagnostic"
                class="android.widget.TextView"
                package="org.z2026.iw3nativeprobe"
                content-desc="IW3 native diagnostic touch surface"
                bounds="[0,0][2280,1080]" />
        </hierarchy>"""
        self.assertEqual(select_target(xml, 2280, 1080), ("target", 1140, 540))

    def test_quickstep_modal_takes_priority_over_underlying_app(self):
        xml = """<hierarchy rotation="1">
          <node text="diagnostic" class="android.widget.TextView"
                package="org.z2026.iw3nativeprobe"
                content-desc="IW3 native diagnostic touch surface"
                bounds="[0,0][2280,1080]" />
          <node text="Quickstep isn't responding" class="android.widget.TextView"
                package="android" bounds="[443,397][1704,471]" />
          <node text="Wait" resource-id="android:id/aerr_wait"
                class="android.widget.Button" package="android"
                bounds="[377,644][1770,776]" />
        </hierarchy>"""
        self.assertEqual(
            select_target(xml, 2280, 1080),
            ("quickstep_anr", 1073, 710),
        )

    def test_out_of_frame_button_is_not_tapped(self):
        xml = """<hierarchy rotation="1">
          <node text="Quickstep isn't responding" class="android.widget.TextView"
                package="android" bounds="[443,397][1704,471]" />
          <node text="Wait" resource-id="android:id/aerr_wait"
                class="android.widget.Button" package="android"
                bounds="[377,1100][1770,1200]" />
        </hierarchy>"""
        self.assertEqual(select_target(xml, 2280, 1080), ("retry", 0, 0))

    def test_missing_target_requests_retry(self):
        self.assertEqual(
            select_target("<hierarchy><node bounds='[0,0][1,1]'/></hierarchy>",
                          2280, 1080),
            ("retry", 0, 0),
        )

    def test_nonpositive_screenshot_dimensions_are_rejected(self):
        with self.assertRaises(ValueError):
            select_target("<hierarchy/>", 0, 1080)


if __name__ == "__main__":
    unittest.main()
