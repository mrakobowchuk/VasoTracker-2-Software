"""
Tests for vasotracker_2/config.py

Covers:
  - Default field values for every dataclass (AcquisitionSettings,
    AnalysisSettings, GraphAxisSettings, MemorySettings, ServoSettings,
    PressureControlSettings, TisDcamSettings, ProxyCameraSettings,
    RegistrationSettings, Config)
  - Config.from_file  — round-trip with a real TOML file
  - Config.save       — writes to disk, readable back via toml.load
  - Config.set_values — propagates sub-config values into a mock state
  - Config.from_state — reads values from a mock state
"""

import sys
import os
import tempfile
import types

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import toml
import unittest.mock as mock

from vasotracker_2.config import (
    AcquisitionSettings,
    AnalysisSettings,
    GraphAxisSettings,
    MemorySettings,
    ServoSettings,
    PressureControlSettings,
    TisDcamSettings,
    ProxyCameraSettings,
    RegistrationSettings,
    Config,
)


# ---------------------------------------------------------------------------
# Default values
# ---------------------------------------------------------------------------

class TestDefaultValues:

    def test_acquisition_defaults(self):
        a = AcquisitionSettings()
        assert a.pixel_world_scale == 1.0
        assert a.exposure == 50
        assert a.pixel_clock == 10
        assert a.recording_interval == 300.0
        assert a.target_fps == 10.0

    def test_analysis_defaults(self):
        a = AnalysisSettings()
        assert a.num_lines == 10
        assert a.smooth == 21
        assert a.integration == 20
        assert a.threshold == 5.5
        assert a.num_threads == 1

    def test_graph_axis_defaults(self):
        g = GraphAxisSettings()
        assert g.x_min == -1200.0
        assert g.x_max == 0.0
        assert g.y_min1 == 50.0
        assert g.y_max1 == 250.0
        assert g.y_min2 == 25.0
        assert g.y_max2 == 200.0

    def test_memory_defaults(self):
        m = MemorySettings()
        assert m.num_plot_points == 500000
        assert m.num_data_points == 500000

    def test_servo_defaults(self):
        s = ServoSettings()
        assert s.device == "Dev1"
        assert s.ao_channel == "ao1"

    def test_pressure_control_defaults(self):
        p = PressureControlSettings()
        assert p.default_pressure == 20.0
        assert p.start_pressure == 20.0
        assert p.stop_pressure == 100.0
        assert p.pressure_interval == 20.0
        assert p.time_interval == 300.0

    def test_tis_dcam_defaults(self):
        t = TisDcamSettings()
        assert t.property_gain == 240

    def test_proxy_camera_defaults(self):
        p = ProxyCameraSettings()
        assert p.max_frame == 300

    def test_registration_defaults(self):
        r = RegistrationSettings()
        assert r.register_flag == 0
        assert r.neveragain_flag == 0

    def test_config_defaults(self):
        c = Config()
        assert isinstance(c.acquisition, AcquisitionSettings)
        assert isinstance(c.analysis, AnalysisSettings)
        assert isinstance(c.servo, ServoSettings)
        assert isinstance(c.graph_axes, GraphAxisSettings)
        assert isinstance(c.memory, MemorySettings)
        assert isinstance(c.pressure_control, PressureControlSettings)
        assert isinstance(c.TIS_DCAM, TisDcamSettings)
        assert isinstance(c.proxy_camera, ProxyCameraSettings)
        assert isinstance(c.registration, RegistrationSettings)
        assert c.path is None


# ---------------------------------------------------------------------------
# Config.from_file and Config.save (round-trip)
# ---------------------------------------------------------------------------

class TestConfigRoundTrip:

    def _write_minimal_toml(self, path):
        data = {
            "acquisition": {
                "pixel_world_scale": 2.5,
                "exposure": 100,
                "pixel_clock": 20,
                "recording_interval": 600.0,
                "target_fps": 25.0,
            },
            "analysis": {
                "num_lines": 8,
                "smooth": 15,
                "integration": 10,
                "threshold": 4.0,
                "num_threads": 2,
            },
            "graph_axes": {
                "x_min": -600.0,
                "x_max": 0.0,
                "y_min1": 60.0,
                "y_max1": 300.0,
                "y_min2": 30.0,
                "y_max2": 250.0,
            },
            "memory": {
                "num_plot_points": 100000,
                "num_data_points": 100000,
            },
            "servo": {"device": "Dev2", "ao_channel": "ao0"},
            "pressure_control": {
                "default_pressure": 30.0,
                "time_interval": 120.0,
                "start_pressure": 30.0,
                "stop_pressure": 80.0,
                "pressure_interval": 10.0,
            },
            "TIS_DCAM": {"property_gain": 100},
            "proxy_camera": {
                "path_template": "data/{:04d}.tif",
                "max_frame": 100,
            },
            "registration": {"register_flag": 0, "neveragain_flag": 0},
        }
        with open(path, "w") as f:
            toml.dump(data, f)
        return data

    def test_from_file_reads_acquisition(self):
        with tempfile.NamedTemporaryFile(suffix=".toml", delete=False) as f:
            path = f.name
        try:
            self._write_minimal_toml(path)
            cfg = Config.from_file(path)
            assert cfg.acquisition.pixel_world_scale == pytest.approx(2.5)
            assert cfg.acquisition.exposure == 100
        finally:
            os.unlink(path)

    def test_from_file_sets_path(self):
        with tempfile.NamedTemporaryFile(suffix=".toml", delete=False) as f:
            path = f.name
        try:
            self._write_minimal_toml(path)
            cfg = Config.from_file(path)
            assert cfg.path == path
        finally:
            os.unlink(path)

    def test_from_file_reads_nested_sections(self):
        with tempfile.NamedTemporaryFile(suffix=".toml", delete=False) as f:
            path = f.name
        try:
            self._write_minimal_toml(path)
            cfg = Config.from_file(path)
            assert cfg.servo.device == "Dev2"
            assert cfg.analysis.num_lines == 8
            assert cfg.pressure_control.default_pressure == pytest.approx(30.0)
        finally:
            os.unlink(path)

    def test_save_creates_file(self):
        with tempfile.NamedTemporaryFile(suffix=".toml", delete=False) as f:
            path = f.name
        os.unlink(path)  # Remove so save creates it fresh
        try:
            cfg = Config()
            cfg.save(override_path=path)
            assert os.path.exists(path)
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_save_round_trip(self):
        with tempfile.NamedTemporaryFile(suffix=".toml", delete=False) as f:
            path = f.name
        os.unlink(path)
        try:
            cfg = Config()
            cfg.acquisition.exposure = 123
            cfg.servo.device = "DevX"
            cfg.save(override_path=path)

            cfg2 = Config.from_file(path)
            assert cfg2.acquisition.exposure == 123
            assert cfg2.servo.device == "DevX"
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_save_does_not_write_path_key(self):
        """The 'path' attribute must not appear in the saved TOML."""
        with tempfile.NamedTemporaryFile(suffix=".toml", delete=False) as f:
            path = f.name
        os.unlink(path)
        try:
            cfg = Config()
            cfg.save(override_path=path)
            data = toml.load(path)
            assert "path" not in data
        finally:
            if os.path.exists(path):
                os.unlink(path)


# ---------------------------------------------------------------------------
# Config.set_values
# ---------------------------------------------------------------------------

def _make_mock_state():
    """Return a nested MagicMock that mimics the VtState interface."""
    state = mock.MagicMock()
    # The mock auto-creates nested attributes, so set_values calls just work.
    return state


class TestConfigSetValues:

    def test_set_values_calls_acq_sub_config(self):
        state = _make_mock_state()
        cfg = Config()
        cfg.set_values(state)
        # AcquisitionSettings.set_values accesses state.toolbar.acq.*
        state.toolbar.acq.scale.set.assert_called_once_with(cfg.acquisition.pixel_world_scale)
        state.toolbar.acq.exposure.set.assert_called_once_with(cfg.acquisition.exposure)

    def test_set_values_calls_analysis_sub_config(self):
        state = _make_mock_state()
        cfg = Config()
        cfg.set_values(state)
        state.toolbar.analysis.num_lines.set.assert_called_once_with(cfg.analysis.num_lines)

    def test_set_values_calls_servo_sub_config(self):
        state = _make_mock_state()
        cfg = Config()
        cfg.set_values(state)
        state.toolbar.servo.device.set.assert_called_once_with(cfg.servo.device)

    def test_set_values_calls_memory_sub_config(self):
        state = _make_mock_state()
        cfg = Config()
        cfg.set_values(state)
        # MemorySettings.set_values sets state.measure.max_len
        assert state.measure.max_len == cfg.memory.num_data_points


# ---------------------------------------------------------------------------
# Config.from_state
# ---------------------------------------------------------------------------

class TestConfigFromState:

    def _make_state(self):
        state = mock.MagicMock()
        # Wire up all the .get() calls used by the from_state class methods
        state.toolbar.acq.scale.get.return_value = 3.0
        state.toolbar.acq.exposure.get.return_value = 75
        state.toolbar.acq.pixel_clock.get.return_value = 15
        state.toolbar.acq.rec_interval.get.return_value = 120.0
        state.toolbar.acq.target_fps.get.return_value = 20.0

        state.toolbar.analysis.num_lines.get.return_value = 12
        state.toolbar.analysis.smooth_factor.get.return_value = 11
        state.toolbar.analysis.thresh_factor.get.return_value = 6.0

        state.toolbar.servo.device.get.return_value = "DevTest"
        state.toolbar.servo.ao_channel.get.return_value = "ao2"

        state.toolbar.graph.x_min.get.return_value = -500.0
        state.toolbar.graph.x_max.get.return_value = 0.0
        state.toolbar.graph.y_min_od.get.return_value = 55.0
        state.toolbar.graph.y_max_od.get.return_value = 260.0
        state.toolbar.graph.y_min_id.get.return_value = 30.0

        state.toolbar.pressure_protocol.pressure_start.get.return_value = 25.0
        state.toolbar.pressure_protocol.pressure_stop.get.return_value = 90.0
        state.toolbar.pressure_protocol.pressure_intvl.get.return_value = 15.0
        state.toolbar.pressure_protocol.time_intvl.get.return_value = 200.0
        state.toolbar.servo.set_pressure = mock.MagicMock()
        state.toolbar.servo.set_pressure.get.return_value = 25.0

        state.measure.max_len = 200000

        return state

    def test_from_state_acquisition(self):
        state = self._make_state()
        cfg = Config.from_state(state)
        assert cfg.acquisition.pixel_world_scale == pytest.approx(3.0)
        assert cfg.acquisition.exposure == 75

    def test_from_state_analysis(self):
        state = self._make_state()
        cfg = Config.from_state(state)
        assert cfg.analysis.num_lines == 12

    def test_from_state_servo(self):
        state = self._make_state()
        cfg = Config.from_state(state)
        assert cfg.servo.device == "DevTest"
        assert cfg.servo.ao_channel == "ao2"

    def test_from_state_memory(self):
        state = self._make_state()
        cfg = Config.from_state(state)
        assert cfg.memory.num_data_points == 200000
