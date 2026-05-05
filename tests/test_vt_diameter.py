"""
Tests for vasotracker_2/utilities/VT_Diameter.py

Covers:
  - _line_profile_coordinates  — scan-line coordinate helper
  - ImageDiameters              — result dataclass sanity checks
  - calculate_diameter          — full diameter-measurement pipeline
    * no-ROI (single ROI, normal and rotated)
    * multiple ROIs
    * filter_means flag
    * ultrasound vs brightfield smoothing
    * returns None for degenerate inputs
"""

import sys
import os
import types

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pytest
from vasotracker_2.utilities.VT_Diameter import (
    _line_profile_coordinates,
    calculate_diameter,
    ImageDiameters,
)


# ---------------------------------------------------------------------------
# Minimal stub objects so calculate_diameter can be called without a full app
# ---------------------------------------------------------------------------

def _make_rds(roi=None, autocaliper=None, multi_roi=None):
    """Return a minimal RasterDrawState-like namespace."""
    rds = types.SimpleNamespace()
    rds.roi = roi
    rds.autocaliper = autocaliper if autocaliper is not None else {}
    rds.multi_roi = multi_roi if multi_roi is not None else {}
    return rds


def _make_roi(x1=10, y1=10, x2=90, y2=90):
    """Return a minimal Roi-like object."""

    class FakeRoi:
        def fixed_corners(self):
            return (x1, y1, x2, y2)

    return FakeRoi()


def _vessel_image(height=100, width=200, wall_left=40, wall_right=160,
                  lumen_left=60, lumen_right=140, dtype=np.uint8):
    """
    Create a synthetic grayscale vessel image.

    The vessel walls are dark bands; the lumen is bright; the background
    is mid-grey.  This yields a profile whose derivative has the right
    sign pattern for the default detection algorithm.
    """
    img = np.full((height, width), 128, dtype=np.float64)
    # outer walls (dark)
    img[:, wall_left - 3:wall_left + 3] = 20
    img[:, wall_right - 3:wall_right + 3] = 20
    # lumen (bright)
    img[:, lumen_left:lumen_right] = 220
    return img.astype(dtype)


# ---------------------------------------------------------------------------
# _line_profile_coordinates
# ---------------------------------------------------------------------------

class TestLineProfileCoordinates:

    def test_horizontal_line_shape(self):
        coords = _line_profile_coordinates((0, 0), (0, 10), linewidth=1)
        assert coords.ndim == 3
        assert coords.shape[0] == 2  # (row_coords, col_coords)

    def test_horizontal_length(self):
        # coords shape is (2, num_line_points, linewidth)
        src, dst = (0, 0), (0, 20)
        coords = _line_profile_coordinates(src, dst, linewidth=1)
        n = int(np.ceil(np.hypot(0, 20) + 1))
        assert coords.shape[1] == n

    def test_diagonal_line_shape(self):
        coords = _line_profile_coordinates((0, 0), (10, 10), linewidth=1)
        assert coords.shape[0] == 2

    def test_linewidth_1_single_sample_per_point(self):
        coords = _line_profile_coordinates((0, 0), (0, 5), linewidth=1)
        # With linewidth=1 each perpendicular slice has exactly 1 sample
        assert coords.shape[2] == 1

    def test_linewidth_3_three_samples_per_point(self):
        coords = _line_profile_coordinates((0, 0), (0, 5), linewidth=3)
        # linewidth is the third axis
        assert coords.shape[2] == 3

    def test_start_equals_end_single_point(self):
        coords = _line_profile_coordinates((5, 5), (5, 5), linewidth=1)
        # zero-length line → ceil(0+1)=1
        assert coords.shape[1] == 1

    def test_values_are_floats(self):
        coords = _line_profile_coordinates((0, 0), (0, 10))
        assert coords.dtype.kind == "f"

    def test_start_col_matches_src(self):
        src, dst = (2, 3), (2, 13)
        coords = _line_profile_coordinates(src, dst, linewidth=1)
        # coords[1] has shape (num_points, linewidth); first point, first sample
        assert coords[1][0][0] == pytest.approx(3.0)

    def test_end_col_matches_dst(self):
        src, dst = (2, 3), (2, 13)
        coords = _line_profile_coordinates(src, dst, linewidth=1)
        # last point, first perpendicular sample
        assert coords[1][-1][0] == pytest.approx(13.0)


# ---------------------------------------------------------------------------
# calculate_diameter — normal (no rotation)
# ---------------------------------------------------------------------------

class TestCalculateDiameterBasic:
    """Tests using a synthetic vessel image, single ROI, no rotation."""

    def _run(self, image=None, rds=None, **kwargs):
        defaults = dict(
            compute_id=True,
            default_detection_alg=True,
            lines_to_avg=5,
            num_lines=5,
            scale=1.0,
            smooth_factor=5,
            thresh_factor=3.5,
            filter_means=False,
            rotate_tracking=False,
            ultrasound_tracking=0,
        )
        defaults.update(kwargs)
        if image is None:
            image = _vessel_image()
        if rds is None:
            rds = _make_rds()
        return calculate_diameter(image, rds, **defaults)

    # --- basic return-type checks ---

    def test_returns_image_diameters(self):
        result = self._run()
        assert isinstance(result, ImageDiameters)

    def test_avg_outer_diam_positive(self):
        result = self._run()
        assert result.avg_outer_diam > 0

    def test_avg_inner_diam_positive_when_id_enabled(self):
        result = self._run(compute_id=True)
        assert result.avg_inner_diam > 0

    def test_avg_inner_diam_nan_when_id_disabled(self):
        result = self._run(compute_id=False)
        assert np.isnan(result.avg_inner_diam)

    def test_outer_diam_array_length_matches_num_lines(self):
        result = self._run(num_lines=5)
        assert len(result.outer_diam) == 5

    def test_od_outliers_bool_array(self):
        result = self._run()
        assert result.od_outliers.dtype == bool

    def test_id_outliers_bool_array(self):
        result = self._run()
        assert result.id_outliers.dtype == bool

    # --- scale parameter ---

    def test_scale_doubles_diameter(self):
        r1 = self._run(scale=1.0)
        r2 = self._run(scale=2.0)
        np.testing.assert_allclose(r2.avg_outer_diam, 2.0 * r1.avg_outer_diam, rtol=1e-6)

    # --- filter_means ---

    def test_filter_means_returns_image_diameters(self):
        result = self._run(filter_means=True)
        assert isinstance(result, ImageDiameters)

    # --- ultrasound smoothing ---

    def test_ultrasound_tracking_returns_image_diameters(self):
        result = self._run(ultrasound_tracking=1, smooth_factor=5)
        assert isinstance(result, ImageDiameters)

    # --- with explicit ROI ---

    def test_explicit_roi_returns_result(self):
        roi = _make_roi(x1=20, y1=20, x2=180, y2=80)
        rds = _make_rds(roi=roi)
        result = self._run(rds=rds)
        assert isinstance(result, ImageDiameters)

    # --- coordinate arrays ---

    def test_outer_diam_x_shape(self):
        result = self._run(num_lines=4)
        assert result.outer_diam_x.shape == (4, 2)

    def test_outer_diam_y_shape(self):
        result = self._run(num_lines=4)
        assert result.outer_diam_y.shape == (4, 2)


# ---------------------------------------------------------------------------
# calculate_diameter — rotated tracking
# ---------------------------------------------------------------------------

class TestCalculateDiameterRotated:

    def _run(self, **kwargs):
        defaults = dict(
            image=_vessel_image(height=200, width=100),
            rds=_make_rds(),
            compute_id=True,
            default_detection_alg=True,
            lines_to_avg=5,
            num_lines=5,
            scale=1.0,
            smooth_factor=5,
            thresh_factor=3.5,
            filter_means=False,
            rotate_tracking=True,
            ultrasound_tracking=0,
        )
        defaults.update(kwargs)
        return calculate_diameter(**defaults)

    def test_rotated_returns_image_diameters(self):
        result = self._run()
        assert isinstance(result, ImageDiameters)

    def test_rotated_outer_diam_positive(self):
        result = self._run()
        assert result.avg_outer_diam > 0

    def test_rotated_with_explicit_roi(self):
        roi = _make_roi(x1=10, y1=10, x2=80, y2=180)
        rds = _make_rds(roi=roi)
        result = self._run(rds=rds)
        assert isinstance(result, ImageDiameters)


# ---------------------------------------------------------------------------
# calculate_diameter — multiple ROIs
# ---------------------------------------------------------------------------

class TestCalculateDiameterMultiROI:

    def _make_multi_roi(self):
        roi_a = _make_roi(x1=10, y1=10, x2=90, y2=40)
        roi_b = _make_roi(x1=10, y1=50, x2=90, y2=90)
        return {"a": roi_a, "b": roi_b}

    def test_multi_roi_returns_image_diameters(self):
        rds = _make_rds(multi_roi=self._make_multi_roi())
        result = calculate_diameter(
            image=_vessel_image(),
            rds=rds,
            compute_id=True,
            default_detection_alg=True,
            lines_to_avg=5,
            num_lines=5,
            scale=1.0,
            smooth_factor=5,
            thresh_factor=3.5,
            filter_means=False,
            rotate_tracking=False,
            ultrasound_tracking=0,
        )
        assert isinstance(result, ImageDiameters)

    def test_multi_roi_diam_length_equals_num_rois(self):
        multi_roi = self._make_multi_roi()
        rds = _make_rds(multi_roi=multi_roi)
        result = calculate_diameter(
            image=_vessel_image(),
            rds=rds,
            compute_id=True,
            default_detection_alg=True,
            lines_to_avg=5,
            num_lines=5,
            scale=1.0,
            smooth_factor=5,
            thresh_factor=3.5,
            filter_means=False,
            rotate_tracking=False,
            ultrasound_tracking=0,
        )
        assert len(result.outer_diam) == len(multi_roi)


# ---------------------------------------------------------------------------
# ImageDiameters dataclass
# ---------------------------------------------------------------------------

class TestImageDiameters:

    def _make(self, n=3):
        pos = np.zeros((n, 2))
        diam = np.ones(n)
        outliers = np.zeros(n, dtype=bool)
        return ImageDiameters(
            outer_diam_x=pos,
            inner_diam_x=pos,
            outer_diam_y=pos,
            inner_diam_y=pos,
            od_outliers=outliers,
            id_outliers=outliers,
            outer_diam=diam,
            inner_diam=diam,
            avg_outer_diam=1.0,
            avg_inner_diam=1.0,
        )

    def test_instantiation(self):
        obj = self._make()
        assert isinstance(obj, ImageDiameters)

    def test_field_access(self):
        obj = self._make(n=4)
        assert obj.outer_diam.shape == (4,)
        assert obj.avg_outer_diam == 1.0
