from QueryLake.operation_classes.ray_chandra_class import (
    BALANCED_PROFILE_MAX_IMAGE_PIXELS,
    QUALITY_PROFILE_MAX_IMAGE_PIXELS,
    SPEED_PROFILE_MAX_IMAGE_PIXELS,
    resolve_pdf_render_scale,
    resolve_profile_max_image_pixels,
)


def test_resolve_profile_max_image_pixels_defaults():
    assert resolve_profile_max_image_pixels("speed") == SPEED_PROFILE_MAX_IMAGE_PIXELS
    assert resolve_profile_max_image_pixels("balanced") == BALANCED_PROFILE_MAX_IMAGE_PIXELS
    assert resolve_profile_max_image_pixels("quality") == QUALITY_PROFILE_MAX_IMAGE_PIXELS
    assert resolve_profile_max_image_pixels("unknown") == BALANCED_PROFILE_MAX_IMAGE_PIXELS


def test_resolve_pdf_render_scale_caps_speed_lane():
    scale = resolve_pdf_render_scale(612.0, 792.0, dpi=144, max_image_pixels=SPEED_PROFILE_MAX_IMAGE_PIXELS)
    assert scale < (144.0 / 72.0)
    rendered_pixels = (612.0 * scale) * (792.0 * scale)
    assert rendered_pixels <= SPEED_PROFILE_MAX_IMAGE_PIXELS * 1.001


def test_resolve_pdf_render_scale_caps_balanced_but_leaves_quality_at_base_dpi():
    base_scale = 144.0 / 72.0
    balanced_scale = resolve_pdf_render_scale(
        612.0,
        792.0,
        dpi=144,
        max_image_pixels=BALANCED_PROFILE_MAX_IMAGE_PIXELS,
    )
    quality_scale = resolve_pdf_render_scale(
        612.0,
        792.0,
        dpi=144,
        max_image_pixels=QUALITY_PROFILE_MAX_IMAGE_PIXELS,
    )
    assert 1.0 < balanced_scale < base_scale
    assert quality_scale == base_scale
