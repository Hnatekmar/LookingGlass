"""Tests for the schema module."""

from app.schema import Label, AnnotationResponse


def test_label_creation():
    """Test creating a Label with valid coordinates."""
    label = Label(x1=0.1, y1=0.2, x2=0.8, y2=0.9, text="Hello")
    assert label.x1 == 0.1
    assert label.y1 == 0.2
    assert label.x2 == 0.8
    assert label.y2 == 0.9
    assert label.text == "Hello"


def test_label_coordinate_range():
    """Test label with edge coordinate values."""
    label = Label(x1=0.0, y1=0.0, x2=1.0, y2=1.0, text="Full image")
    assert label.x1 == 0.0
    assert label.y2 == 1.0


def test_label_empty_text():
    """Test label with empty text string."""
    label = Label(x1=0.0, y1=0.0, x2=0.5, y2=0.5, text="")
    assert label.text == ""


def test_annotation_response_empty():
    """Test annotation response with empty labels list."""
    response = AnnotationResponse(labels=[])
    assert response.labels == []


def test_annotation_response_multiple_labels():
    """Test annotation response with multiple labels."""
    labels = [
        Label(x1=0.0, y1=0.0, x2=0.3, y2=0.2, text="First"),
        Label(x1=0.5, y1=0.0, x2=0.8, y2=0.2, text="Second"),
        Label(x1=0.0, y1=0.5, x2=0.4, y2=0.7, text="Third"),
    ]
    response = AnnotationResponse(labels=labels)
    assert len(response.labels) == 3
    assert response.labels[0].text == "First"
    assert response.labels[1].text == "Second"
    assert response.labels[2].text == "Third"


def test_label_defaults():
    """Test that Label doesn't have unexpected defaults (all fields required)."""
    import pytest
    # All fields should be required
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        Label()  # Missing required fields
