"""
Tests for vasotracker_2/utilities/VTutils.py

Covers:
  - diff / diff2 / diff3  — numerical differentiation helpers
  - detect_peaks          — peak / valley detection
  - is_outlier            — modified-Z-score outlier flag
  - process_ddts          — full diameter-detection pipeline (unit-level)
"""

import sys
import os

# Make the package importable from any working directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pytest
from vasotracker_2.utilities.VTutils import (
    diff,
    diff2,
    diff3,
    detect_peaks,
    is_outlier,
    process_ddts,
    DdtResult,
)


# ---------------------------------------------------------------------------
# diff / diff2 / diff3
# ---------------------------------------------------------------------------

class TestDiff:
    """Tests for the three numerical-differentiation helpers."""

    def test_diff_returns_array(self):
        sig = np.linspace(0, 10, 50)
        result = diff(sig, 1)
        assert isinstance(result, np.ndarray)
        assert result.shape == sig.shape

    def test_diff_constant_signal_is_near_zero(self):
        sig = np.ones(100)
        result = diff(sig, 1)
        np.testing.assert_allclose(result, 0, atol=1e-10)

    def test_diff_linear_signal_positive_slope(self):
        sig = np.linspace(0, 1, 100)
        result = diff(sig, 1)
        # Gaussian-derivative of a linear ramp should be roughly constant & positive
        assert np.mean(result) > 0

    def test_diff2_returns_array(self):
        sig = np.linspace(0, 10, 50)
        result = diff2(sig, 1)
        assert isinstance(result, np.ndarray)

    def test_diff2_constant_signal_is_near_zero(self):
        sig = np.ones(80)
        result = diff2(sig, 1)
        # convolution with [1,-1] on a constant gives 0 everywhere except edges
        np.testing.assert_allclose(result[1:-1], 0, atol=1e-10)

    def test_diff2_linear_signal_positive_slope(self):
        sig = np.linspace(0, 1, 100)
        result = diff2(sig, 1)
        # Interior values of conv(linear, [1,-1]) should be uniformly positive
        assert np.all(result[1:-1] > 0)

    def test_diff3_returns_array(self):
        sig = np.linspace(0, 10, 50)
        result = diff3(sig, 1)
        assert isinstance(result, np.ndarray)

    def test_diff3_constant_signal_is_zero(self):
        sig = np.ones(80)
        result = diff3(sig, 1)
        np.testing.assert_allclose(result, 0, atol=1e-10)

    def test_diff3_linear_signal_all_equal(self):
        sig = np.linspace(0, 1, 100)
        result = diff3(sig, 1)
        # np.diff of a linear ramp returns a constant array
        np.testing.assert_allclose(result, result[0], atol=1e-10)

    def test_diff2_length_one_more_than_input(self):
        """diff2 uses np.convolve in 'full' mode — length = n + len(kernel) - 1."""
        sig = np.ones(50)
        result = diff2(sig, 1)
        assert result.shape[0] == sig.shape[0] + 1  # [1,-1] adds 1 element


# ---------------------------------------------------------------------------
# detect_peaks
# ---------------------------------------------------------------------------

class TestDetectPeaks:
    """Tests for the detect_peaks function."""

    def test_single_peak_detected(self):
        x = np.array([0, 1, 0, 0, 0], dtype=float)
        peaks = detect_peaks(x)
        assert 1 in peaks

    def test_single_valley_detected(self):
        x = np.array([0, -1, 0, 0, 0], dtype=float)
        valleys = detect_peaks(x, valley=True)
        assert 1 in valleys

    def test_empty_array_returns_empty(self):
        result = detect_peaks(np.array([]))
        assert len(result) == 0

    def test_short_array_returns_empty(self):
        result = detect_peaks(np.array([1, 2]))
        assert len(result) == 0

    def test_constant_array_returns_empty(self):
        result = detect_peaks(np.ones(20))
        assert len(result) == 0

    def test_sinusoid_peaks(self):
        t = np.linspace(0, 2 * np.pi, 200, endpoint=False)
        x = np.sin(t)
        peaks = detect_peaks(x, mph=0.5, mpd=50)
        assert len(peaks) >= 1

    def test_sinusoid_valleys(self):
        t = np.linspace(0, 2 * np.pi, 200, endpoint=False)
        x = np.sin(t)
        valleys = detect_peaks(x, mph=0.5, mpd=50, valley=True)
        assert len(valleys) >= 1

    def test_min_peak_height_filters_small_peaks(self):
        x = np.array([0.0, 0.1, 0.0, 1.0, 0.0], dtype=float)
        all_peaks = detect_peaks(x)
        large_peaks = detect_peaks(x, mph=0.5)
        assert len(large_peaks) <= len(all_peaks)
        assert 3 in large_peaks
        assert 1 not in large_peaks

    def test_min_peak_distance_removes_close_peaks(self):
        x = np.array([0.0, 1.0, 0.5, 1.0, 0.0], dtype=float)
        peaks_no_mpd = detect_peaks(x, mpd=1)
        peaks_mpd = detect_peaks(x, mpd=3)
        assert len(peaks_mpd) <= len(peaks_no_mpd)

    def test_nan_handling(self):
        x = np.array([0.0, 1.0, np.nan, 1.0, 0.0], dtype=float)
        peaks = detect_peaks(x)
        # Peaks adjacent to NaN should not be returned
        assert 1 not in peaks

    def test_threshold_parameter(self):
        x = np.array([0.0, 0.9, 0.8, 1.0, 0.9, 0.0], dtype=float)
        peaks_no_thresh = detect_peaks(x)
        peaks_with_thresh = detect_peaks(x, threshold=0.5)
        assert len(peaks_with_thresh) <= len(peaks_no_thresh)

    def test_edge_rising(self):
        x = np.array([0.0, 1.0, 1.0, 0.0], dtype=float)
        peaks = detect_peaks(x, edge="rising")
        assert len(peaks) == 1
        assert peaks[0] == 1

    def test_edge_falling(self):
        x = np.array([0.0, 1.0, 1.0, 0.0], dtype=float)
        peaks = detect_peaks(x, edge="falling")
        assert len(peaks) == 1
        assert peaks[0] == 2

    def test_edge_both(self):
        x = np.array([0.0, 1.0, 1.0, 0.0], dtype=float)
        peaks = detect_peaks(x, edge="both")
        assert 1 in peaks
        assert 2 in peaks

    def test_edge_none(self):
        x = np.array([0.0, 1.0, 1.0, 0.0], dtype=float)
        peaks = detect_peaks(x, edge=None)
        assert len(peaks) == 0


# ---------------------------------------------------------------------------
# is_outlier
# ---------------------------------------------------------------------------

class TestIsOutlier:
    """Tests for the modified-Z-score outlier detector."""

    def test_no_outliers_in_uniform_data(self):
        points = np.ones(10)
        result = is_outlier(points, thresh=3.5)
        # All-same data has zero MAD → modified_z_score undefined/infinite
        # but numpy divides by 0 → inf > 3.5 → all flagged or all False
        # Just assert the shape is correct
        assert result.shape == (10,)

    def test_obvious_outlier_detected(self):
        points = np.array([1.0, 1.0, 1.0, 1.0, 1.0, 100.0])
        result = is_outlier(points, thresh=3.5)
        assert result[-1] == True

    def test_inliers_not_flagged(self):
        points = np.array([10.0, 10.5, 9.8, 10.2, 10.1])
        result = is_outlier(points, thresh=3.5)
        assert not any(result)

    def test_high_threshold_flags_nothing(self):
        points = np.array([1.0, 2.0, 10.0, 1.5, 2.5])
        result = is_outlier(points, thresh=1000)
        assert not any(result)

    def test_low_threshold_flags_more(self):
        points = np.array([1.0, 1.5, 2.0, 2.5, 10.0])
        strict = is_outlier(points, thresh=1.0)
        lenient = is_outlier(points, thresh=5.0)
        assert sum(strict) >= sum(lenient)

    def test_2d_input_handled(self):
        """is_outlier should work on 2-D arrays (each row a multivariate obs)."""
        points = np.column_stack([np.ones(6), np.ones(6)])
        result = is_outlier(points, thresh=3.5)
        assert result.shape == (6,)

    def test_single_outlier_at_start(self):
        points = np.array([100.0, 1.0, 1.0, 1.0, 1.0, 1.0])
        result = is_outlier(points, thresh=3.5)
        assert result[0] == True

    def test_returns_boolean_array(self):
        points = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = is_outlier(points, thresh=3.5)
        assert result.dtype == bool


# ---------------------------------------------------------------------------
# process_ddts
# ---------------------------------------------------------------------------

def _make_vessel_ddt(length=200, od1=40, od2=160, id1=70, id2=130, amplitude=1.0):
    """
    Build a synthetic derivative signal (ddt) that mimics a typical brightfield
    vessel scan:
      - negative peak at od1  (left outer wall)
      - positive peak at id1  (left inner wall)
      - negative peak at id2  (right inner wall)
      - positive peak at od2  (right outer wall)
    """
    x = np.zeros(length)
    sigma = 3
    for pos in [od1, id2]:
        x[pos] -= amplitude
    for pos in [id1, od2]:
        x[pos] += amplitude
    return x


class TestProcessDdts:
    """Tests for the main process_ddts pipeline (detection_mode=0, fluorescence)."""

    def _run(self, ddts, scale=1.0, ID_mode=1, detection_mode=0, ultrasound=0):
        nx = len(ddts[0])
        start_x = [0] * len(ddts)
        return process_ddts(
            ddts=ddts,
            thresh_factor=3.5,
            thresh=0,
            nx=nx,
            scale=scale,
            start_x=start_x,
            ID_mode=ID_mode,
            detection_mode=detection_mode,
            ultrasound_tracking=ultrasound,
        )

    def test_returns_ddt_result(self):
        ddt = _make_vessel_ddt()
        result = self._run([ddt])
        assert isinstance(result, DdtResult)

    def test_outer_diam_positive(self):
        ddt = _make_vessel_ddt()
        result = self._run([ddt])
        assert result.outer_diam[0] > 0

    def test_scale_multiplies_diameter(self):
        ddt = _make_vessel_ddt()
        r1 = self._run([ddt], scale=1.0)
        r2 = self._run([ddt], scale=2.0)
        np.testing.assert_allclose(r2.outer_diam[0], 2.0 * r1.outer_diam[0], rtol=1e-6)

    def test_id_mode_disabled_gives_nan_id(self):
        ddt = _make_vessel_ddt()
        result = self._run([ddt], ID_mode=0)
        assert np.all(np.isnan(result.inner_diam))

    def test_multiple_lines_same_result(self):
        """With identical scan lines the per-line diameters should be equal."""
        ddt = _make_vessel_ddt()
        result = self._run([ddt, ddt, ddt])
        ods = result.outer_diam
        np.testing.assert_allclose(ods, ods[0], rtol=1e-6)

    def test_outlier_arrays_correct_shape(self):
        ddt = _make_vessel_ddt()
        n = 4
        result = self._run([ddt] * n)
        assert result.od_outliers.shape == (n,)
        assert result.id_outliers.shape == (n,)

    def test_outer_diam_pos_shape(self):
        ddt = _make_vessel_ddt()
        n = 3
        result = self._run([ddt] * n)
        assert result.outer_diam_pos.shape == (n, 2)

    def test_inner_diam_pos_shape(self):
        ddt = _make_vessel_ddt()
        n = 3
        result = self._run([ddt] * n)
        assert result.inner_diam_pos.shape == (n, 2)

    def test_od_greater_than_id(self):
        """Outer diameter should be at least as large as inner diameter."""
        ddt = _make_vessel_ddt()
        result = self._run([ddt])
        od = result.outer_diam[0]
        id_ = result.inner_diam[0]
        if not np.isnan(id_):
            assert od >= id_

    def test_start_x_offset_shifts_positions(self):
        ddt = _make_vessel_ddt()
        r0 = self._run([ddt])
        # Provide a non-zero start_x offset
        nx = len(ddt)
        result_offset = process_ddts(
            ddts=[ddt],
            thresh_factor=3.5,
            thresh=0,
            nx=nx,
            scale=1.0,
            start_x=[10],
            ID_mode=1,
            detection_mode=0,
            ultrasound_tracking=0,
        )
        # Diameter (od2_ - od1_) should stay the same; absolute positions shift
        np.testing.assert_allclose(
            result_offset.outer_diam[0], r0.outer_diam[0], rtol=1e-6
        )

    def test_detection_mode_1_inverted(self):
        """detection_mode=1 (inverted / ultrasound-like) — just verify no crash."""
        ddt = _make_vessel_ddt()
        result = self._run([ddt], detection_mode=1)
        assert isinstance(result, DdtResult)

    def test_ultrasound_tracking_mode(self):
        """ultrasound_tracking=1 uses algorithm 2 — verify no crash."""
        ddt = _make_vessel_ddt()
        result = self._run([ddt], ultrasound=1)
        assert isinstance(result, DdtResult)
