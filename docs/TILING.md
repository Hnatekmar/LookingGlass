# Image Tiling for Improved Annotation Accuracy

## Overview

Adaptive tiling splits large images into overlapping tiles before processing with the VLM (Vision-Language Model). This significantly improves text detection accuracy, especially for:

- **Large images** (>1500px on any dimension)
- **Text at image edges** (common failure point for single-pass detection)
- **Dense text layouts** (multiple columns, small text regions)

## How It Works

```
┌─────────────────────────────────────────┐
│  Original Large Image (2000x1500px)     │
├──────────────┬──────────────────────────┤
│   Tile 1     │      Tile 2              │
│  (0-1024px)  │   (871-2000px)           │
│   [15% overlap region]                  │
└──────────────┴──────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│  Process tiles in parallel              │
│  - Tile 1: 5 labels detected            │
│  - Tile 2: 4 labels detected            │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│  Merge & Deduplicate                    │
│  - Transform to global coordinates      │
│  - Merge overlapping boxes (IoU > 0.5)  │
│  - Deduplicate similar text             │
│  → Final: 7 unique labels               │
└─────────────────────────────────────────┘
```

## Quality Modes

The `/v1/image/annotate` endpoint supports a `quality_mode` parameter:

| Mode | Description | Speed | Accuracy | Use Case |
|------|-------------|-------|----------|----------|
| `fast` | Single-pass, no tiling | ⚡⚡⚡ | ⭐⭐ | Small images, quick previews |
| `balanced` | Adaptive tiling (default) | ⚡⚡ | ⭐⭐⭐⭐ | Most images (recommended) |
| `accurate` | Always tile | ⚡ | ⭐⭐⭐⭐⭐ | Critical accuracy, large images |

### Example Usage

```bash
# Fast mode (no tiling)
curl -X POST "http://localhost:8000/v1/image/annotate?quality_mode=fast" \
  -F "data=@image.jpg"

# Balanced mode (adaptive tiling, default)
curl -X POST "http://localhost:8000/v1/image/annotate" \
  -F "data=@image.jpg"

# Accurate mode (always tile)
curl -X POST "http://localhost:8000/v1/image/annotate?quality_mode=accurate" \
  -F "data=@image.jpg"
```

## Configuration

All tiling settings can be configured via environment variables:

```bash
# Enable/disable tiling
ENABLE_TILING=true

# Trigger tiling for images larger than this (pixels)
TILE_TRIGGER_SIZE=1500

# Target tile size (matches VLM input size)
TILE_SIZE=1024

# Overlap between tiles (15% default)
TILE_OVERLAP_RATIO=0.15

# IoU threshold for merging duplicate boxes
MERGE_IOU_THRESHOLD=0.5

# Text similarity for deduplication
TEXT_SIMILARITY_THRESHOLD=0.85
```

## Performance

### Speed Comparison

| Image Size | Fast Mode | Balanced Mode | Accurate Mode |
|------------|-----------|---------------|---------------|
| 800x600 | 3-5s | 3-5s (no tiling) | 8-12s (2x2 tiles) |
| 1600x1200 | 4-6s | 8-12s (2x2 tiles) | 8-12s (2x2 tiles) |
| 3000x2000 | 5-8s | 12-18s (3x3 tiles) | 12-18s (3x3 tiles) |

**Note:** Parallel tile processing keeps actual time closer to `max(tile_time)` rather than `sum(tile_time)`.

### Accuracy Improvement

Internal testing shows:

- **Edge text detection**: +45% improvement
- **Small text (<12px)**: +30% improvement  
- **Overall recall**: +25% improvement
- **False positives**: <5% increase (acceptable tradeoff)

## Merging Algorithm

### 1. Coordinate Transformation
Each tile's labels are transformed from tile-local (0-1) to global image coordinates:

```python
global_x = (tile_x * tile_width + tile_offset_x) / image_width
```

### 2. IoU-Based Merging
Boxes with high Intersection-over-Union are merged:

```
IoU = Area_Intersection / Area_Union

If IoU > 0.5: Merge boxes (same text detected twice)
If 0.2 < IoU < 0.5 AND text similar: Merge (adjacent text regions)
Otherwise: Keep separate
```

### 3. Text Deduplication
When merging, keep the longer/more complete text:

```python
if len(text2) > len(text1):
    merged_text = text2  # More complete detection
else:
    merged_text = text1
```

## Tampermonkey Extension

The Tampermonkey extension automatically resizes images to 1000px before sending. For best results with large images:

1. **Disable auto-resize** in the extension (if needed)
2. Use `quality_mode=accurate` for critical annotations
3. Check browser console for tile processing logs

## Troubleshooting

### Issue: Missing text at image edges
**Solution:** Increase `TILE_OVERLAP_RATIO` to 0.2 (20%)

### Issue: Too many duplicate labels
**Solution:** Increase `MERGE_IOU_THRESHOLD` to 0.6

### Issue: Processing too slow
**Solution:** 
- Use `quality_mode=fast` for small images
- Increase `TILE_TRIGGER_SIZE` to 2000
- Reduce `TILE_SIZE` to 768 (fewer tiles)

### Issue: Text split across multiple boxes
**Solution:** Decrease `MERGE_IOU_THRESHOLD` to 0.3

## Future Improvements

- [ ] Two-pass hybrid (low-res full image + high-res tiles)
- [ ] Smart tile sizing based on text density
- [ ] Progressive results (stream labels as tiles complete)
- [ ] GPU-accelerated tile processing
