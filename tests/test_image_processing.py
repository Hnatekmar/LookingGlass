"""Tests for the image processing module."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock


def test_get_image_hash():
    """Test that get_image_hash returns a consistent SHA256 hash."""
    from app.image_processing import get_image_hash

    hash1 = get_image_hash(b"test image data")
    hash2 = get_image_hash(b"test image data")
    hash3 = get_image_hash(b"different data")

    assert hash1 == hash2
    assert hash1 != hash3
    assert len(hash1) == 64  # SHA256 hex length


def test_get_image_hash_deterministic():
    """Test that the same input always produces the same hash."""
    from app.image_processing import get_image_hash

    data = b"some binary content \x00\x01\x02"
    assert get_image_hash(data) == get_image_hash(data)


@pytest.mark.asyncio
async def test_prepare_image_for_glm_ocr():
    """Test image preparation returns bytes."""
    from app.image_processing import prepare_image_for_glm_ocr

    # Create a small valid JPEG
    import io
    from PIL import Image

    img = Image.new("RGB", (100, 50), color="red")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    img_bytes = buf.getvalue()

    result = await prepare_image_for_glm_ocr(img_bytes)
    assert isinstance(result, bytes)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_prepare_image_for_glm_ocr_resizes():
    """Test that large images are resized."""
    from app.image_processing import prepare_image_for_glm_ocr
    import io
    from PIL import Image

    # Create a large image
    img = Image.new("RGB", (3000, 2000), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    img_bytes = buf.getvalue()

    result = await prepare_image_for_glm_ocr(img_bytes)
    # Should be resized
    result_img = Image.open(io.BytesIO(result))
    assert result_img.size[0] <= 1280
    assert result_img.size[1] <= 1280


@pytest.mark.asyncio
async def test_extract_labels_with_cache_hit():
    """Test cache hit returns cached annotation."""
    from app.image_processing import extract_labels_with_cache, image_annotation_cache
    from app.schema import AnnotationResponse, Label

    image_hash = "cache_hit_test"
    cache_key = f"image:{image_hash}"

    cached_response = AnnotationResponse(
        labels=[Label(x1=0.1, y1=0.1, x2=0.5, y2=0.5, text="cached")]
    )
    image_annotation_cache.set(cache_key, cached_response)

    result = await extract_labels_with_cache(
        b"test image", image_hash, cache_key
    )
    assert result.labels[0].text == "cached"
    image_annotation_cache.clear()


@pytest.mark.asyncio
async def test_extract_labels_with_cache_miss():
    """Test cache miss triggers actual extraction."""
    from app.image_processing import extract_labels_with_cache, image_annotation_cache
    from app.schema import AnnotationResponse, Label

    image_hash = "cache_miss_test"
    cache_key = f"image:{image_hash}"
    image_annotation_cache.clear()

    with patch("app.image_processing._extract_labels_from_image", new_callable=AsyncMock) as mock_extract:
        mock_extract.return_value = AnnotationResponse(
            labels=[Label(x1=0.0, y1=0.0, x2=0.5, y2=0.5, text="extracted")]
        )
        result = await extract_labels_with_cache(
            b"test image", image_hash, cache_key
        )
        assert result.labels[0].text == "extracted"
        mock_extract.assert_called_once_with(b"test image")


def test_cache_stats_accessible():
    """Test that cache stats are accessible via the cache object."""
    from app.image_processing import image_annotation_cache
    stats = image_annotation_cache.stats
    assert hasattr(stats, 'hits')
    assert hasattr(stats, 'misses')
