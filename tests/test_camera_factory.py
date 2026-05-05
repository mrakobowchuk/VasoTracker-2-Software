"""
Tests for vasotracker_2/cameras/camera_factory.py and camera_base.py

Covers:
  - CameraBase subclass registration via __init_subclass__
  - CameraFactory lookup (happy path and missing-name error)
  - CameraBase.set_exposure  — numpy integer conversion
  - CameraBase.image_ready   — delegates to mmc
  - CameraBase.start/stop_acquisition state flag
  - CameraBase.get_camera_dims
"""

import sys
import os
import types
import unittest.mock as mock

# Stub out tkinter and pymmcore_plus before anything else imports them,
# because cameras.py has top-level imports of both.
for _mod in ("tkinter", "tkinter.messagebox", "tkinter.filedialog"):
    if _mod not in sys.modules:
        sys.modules[_mod] = types.ModuleType(_mod)

# Provide a minimal pymmcore_plus stub if the real package is missing
if "pymmcore_plus" not in sys.modules:
    _pm = types.ModuleType("pymmcore_plus")
    _pm.CMMCorePlus = object
    _pm.find_micromanager = lambda: None
    sys.modules["pymmcore_plus"] = _pm

# Stub tifffile
if "tifffile" not in sys.modules:
    sys.modules["tifffile"] = types.ModuleType("tifffile")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pytest

from vasotracker_2.cameras.camera_base import CameraBase
from vasotracker_2.cameras.camera_factory import CameraFactory



# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mmc():
    """Return a MagicMock that stands in for a CMMCorePlus instance."""
    mmc = mock.MagicMock()
    mmc.getRemainingImageCount.return_value = 0
    mmc.isSequenceRunning.return_value = False
    mmc.getImageWidth.return_value = 640
    mmc.getImageHeight.return_value = 480
    return mmc


def _make_base(mmc=None):
    """Instantiate a concrete CameraBase-derived class for testing."""
    if mmc is None:
        mmc = _make_mmc()

    # Create a minimal concrete subclass in-test, using a unique name so it
    # doesn't collide with production classes already in the registry.
    class _TestCamera(CameraBase, camera_name="_pytest_test_camera"):
        pass

    state = mock.MagicMock()
    config = mock.MagicMock()
    return _TestCamera(mmc, state, config)


# ---------------------------------------------------------------------------
# CameraBase subclass registration
# ---------------------------------------------------------------------------

class TestCameraBaseRegistry:

    def test_subclass_registers_under_lower_case_name(self):
        # Unique name to avoid conflicts
        class MyTestCam(CameraBase, camera_name="MyTestCam_Registry"):
            pass

        assert "mytestcam_registry" in CameraBase._registry

    def test_subclass_stores_camera_name_attribute(self):
        class AnotherCam(CameraBase, camera_name="AnotherCam_Test"):
            pass

        assert AnotherCam.camera_name == "AnotherCam_Test"

    def test_multiple_subclasses_registered_independently(self):
        class CamA(CameraBase, camera_name="_TestCamA"):
            pass

        class CamB(CameraBase, camera_name="_TestCamB"):
            pass

        assert "_testcama" in CameraBase._registry
        assert "_testcamb" in CameraBase._registry


# ---------------------------------------------------------------------------
# CameraFactory
# ---------------------------------------------------------------------------

class TestCameraFactory:

    def _factory_with_fake_cam(self):
        class FakeCam(CameraBase, camera_name="_pytest_factory_cam"):
            def __init__(self, mmc, state, config):
                super().__init__(mmc, state, config)

        factory = CameraFactory(CameraBase._registry)
        return factory

    def test_known_camera_is_instantiated(self):
        factory = self._factory_with_fake_cam()
        mmc = _make_mmc()
        state = mock.MagicMock()
        config = mock.MagicMock()
        cam = factory("_pytest_factory_cam", mmc, state, config)
        assert cam is not None

    def test_known_camera_case_insensitive(self):
        factory = self._factory_with_fake_cam()
        mmc = _make_mmc()
        state = mock.MagicMock()
        config = mock.MagicMock()
        cam = factory("_PYTEST_FACTORY_CAM", mmc, state, config)
        assert cam is not None

    def test_unknown_camera_raises_key_error(self):
        factory = CameraFactory(CameraBase._registry)
        with pytest.raises(KeyError, match="No camera with name"):
            factory("__nonexistent_camera__", None, None, None)

    def test_returned_instance_is_camera_base(self):
        factory = self._factory_with_fake_cam()
        mmc = _make_mmc()
        state = mock.MagicMock()
        config = mock.MagicMock()
        cam = factory("_pytest_factory_cam", mmc, state, config)
        assert isinstance(cam, CameraBase)


# ---------------------------------------------------------------------------
# CameraBase methods
# ---------------------------------------------------------------------------

class TestCameraBaseMethods:

    def test_set_exposure_calls_mmc(self):
        mmc = _make_mmc()
        cam = _make_base(mmc)
        cam.set_exposure(50)
        mmc.setExposure.assert_called_once_with(50)

    def test_set_exposure_converts_numpy_int(self):
        """numpy integer types must be converted to plain int before passing on."""
        mmc = _make_mmc()
        cam = _make_base(mmc)
        cam.set_exposure(np.int32(75))
        mmc.setExposure.assert_called_once_with(75)
        # Ensure the value passed is a Python int, not numpy int
        call_arg = mmc.setExposure.call_args[0][0]
        assert type(call_arg) is int

    def test_image_ready_true_when_images_remaining(self):
        mmc = _make_mmc()
        mmc.getRemainingImageCount.return_value = 3
        cam = _make_base(mmc)
        assert cam.image_ready() is True

    def test_image_ready_true_when_sequence_running(self):
        mmc = _make_mmc()
        mmc.getRemainingImageCount.return_value = 0
        mmc.isSequenceRunning.return_value = True
        cam = _make_base(mmc)
        assert cam.image_ready() is True

    def test_image_ready_false_when_nothing(self):
        mmc = _make_mmc()
        mmc.getRemainingImageCount.return_value = 0
        mmc.isSequenceRunning.return_value = False
        cam = _make_base(mmc)
        assert cam.image_ready() is False

    def test_start_acquisition_sets_running_flag(self):
        mmc = _make_mmc()
        cam = _make_base(mmc)
        assert cam.running is False
        cam.start_acquisition()
        assert cam.running is True

    def test_stop_acquisition_clears_running_flag(self):
        mmc = _make_mmc()
        cam = _make_base(mmc)
        cam.running = True
        cam.stop_acquisition()
        assert cam.running is False

    def test_get_camera_dims_returns_width_height(self):
        mmc = _make_mmc()
        mmc.getImageWidth.return_value = 1024
        mmc.getImageHeight.return_value = 768
        cam = _make_base(mmc)
        w, h = cam.get_camera_dims()
        assert w == 1024
        assert h == 768

    def test_get_image_delegates_to_mmc(self):
        mmc = _make_mmc()
        fake_frame = np.zeros((480, 640), dtype=np.uint8)
        mmc.getLastImage.return_value = fake_frame
        cam = _make_base(mmc)
        result = cam.get_image()
        np.testing.assert_array_equal(result, fake_frame)

    def test_is_buffer_empty_returns_count(self):
        mmc = _make_mmc()
        mmc.getRemainingImageCount.return_value = 5
        cam = _make_base(mmc)
        assert cam.is_buffer_empty() == 5

    def test_next_position_does_nothing(self):
        """Base implementation should be a no-op."""
        cam = _make_base()
        cam.next_position()  # should not raise

    def test_reset_calls_mmc_reset(self):
        mmc = _make_mmc()
        cam = _make_base(mmc)
        cam.reset()
        mmc.reset.assert_called_once()
