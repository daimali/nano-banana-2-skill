---
name: nano-banana-2-generator
description: |
  Generate and edit high-quality images using Nano Banana 2 (Gemini 3.1 Flash Image),
  Google DeepMind's next-generation image model with world knowledge, multi-language text rendering,
  character/object consistency, and configurable thinking levels.
  Use this skill when the user wants to create images, edit photos, replace backgrounds,
  maintain character consistency across images, render text in images (especially Chinese),
  generate infographics, translate/localize image text, or create any kind of visual content.
  Also use when the user mentions posters, book covers, product photos, storyboards,
  social media graphics, concept art, data visualization, or any visual design task
  that benefits from character/object consistency or accurate text rendering.
---

# Nano Banana 2 (nano-banana-2-bltcy) Image Generation

## When to use

Use this skill when the user wants to:
- Create images, pictures, photos, or artwork
- Design posters, banners, covers, or social media graphics
- Generate avatars, profile pictures, or icons
- Create wallpapers (desktop or mobile)
- Produce illustrations, concept art, or drawings
- Make product photos or mockups
- **Edit existing images** (background replacement, style transfer, localized editing)
- **Maintain character consistency** across multiple images (up to 5 characters)
- **Maintain object consistency** across multiple images (up to 14 objects)
- **Render accurate text** in images (Chinese, English, and other languages)
- **Translate/localize text** within images
- **Generate infographics** or data visualizations
- **Create storyboards** with consistent characters

## Prerequisites

- **API Key**: The user must have an API Key from the platform.
  - If the user has not provided an API key, ask them to provide one.
  - Tell them they can get an API key at **https://www.moodmax.cn** → top-right corner → **Settings**.
- **Credits**: Each generation consumes credits; failed generations do not deduct credits

## Skill Version

**Current skill version**: `1.0.0`

The API returns a `skillVersion` field in every response. The script automatically compares the local skill version with the API version:

- **Major version mismatch** (e.g., API `2.x.x` vs skill `1.x.x`): A warning is printed — **you must upgrade** the skill files.
- **Minor version mismatch** (e.g., API `1.2.x` vs skill `1.1.x`): A warning is printed — **recommend upgrading** for new features.
- **Patch version mismatch**: No warning — compatible.

When an upgrade is required, re-download the latest skill files from:
**https://github.com/daimali/nano-banana2-skill.git**

## How it works

Image generation is an **asynchronous** process with two steps:

1. **Create task** -> returns a `taskId`
2. **Poll for result** -> returns image URL when complete

```
Step 1: POST /open_api/v2/create-task -> taskId
Step 2: Wait 3-5 seconds
Step 3: POST /open_api/v2/query-task -> status
         ├─ "completed" -> get image URL
         ├─ "processing" -> wait 3s, back to Step 3
         └─ "failed" -> report error
```

Polling: every 3 seconds, up to 100 times (~5 min timeout).

Note: The API returns `status="processing"` until the image is both generated **and** transferred to OSS. The task is only considered `completed` when the final URL is ready. No need to handle `url: null` — just keep polling until `status="completed"`.

## Tool: Generate Image

**Execute the bundled Python script** `scripts/generate_image.py` directly:

```bash
python scripts/generate_image.py \
  --api-key "YOUR_API_KEY" \
  --prompt "A serene Japanese garden with cherry blossoms, watercolor style" \
  --size 16:9 \
  --n 1 \
  --thinking-level high \
  --verbose
```

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--api-key` | string | Yes | API key |
| `--prompt` | string | Yes | Image description (supports Chinese and English) |
| `--size` | string | No | Aspect ratio or resolution. Default: `16:9` |
| `--n` | integer | No | Number of images. Default: `1`, Max: `4` |
| `--thinking-level` | string | No | Thinking/reasoning depth. Options: `minimal`, `high`, `dynamic`. Default: `high` |
| `--reference-images` | string | No | Comma-separated URLs of reference images for character/object consistency |
| `--verbose` | boolean | No | Show progress logs |

**Size options**:

| Ratio | Best for |
|-------|----------|
| 1:1 | Avatars, icons, social media |
| 16:9 | Landscape posters, desktop wallpapers |
| 9:16 | Mobile wallpapers, portrait posters |
| 4:3 | Product photos, PPT images |
| 3:2 | Photography, landscapes |
| 2:3 | Book covers, portrait illustrations |
| 21:9 | Ultra-wide wallpapers |
| 9:21 | Ultra-tall posters |
| 4:1 | Panoramic banners |
| 1:4 | Vertical banners |
| 8:1 | Ultra-wide strips |
| 1:8 | Ultra-tall strips |

**Thinking level options**:

| Level | Description | Best for |
|-------|-------------|----------|
| `minimal` | Fastest generation, basic prompt following | Quick drafts, simple scenes |
| `high` | Balanced speed and quality, good prompt adherence | Most use cases, general image generation |
| `dynamic` | Deepest reasoning, best for complex prompts | Complex scenes, infographics, text rendering, precise composition |

**Response**:
```json
{
  "taskId": 12345,
  "status": "completed",
  "progress": 100,
  "outputFiles": [
    {
      "url": "https://cdn.example.com/images/abc123.jpg",
      "type": "image/jpeg"
    }
  ]
}
```

**Or use the Python functions directly** in your code:

```python
from scripts.generate_image import generate_image

result = generate_image(
    api_key="YOUR_API_KEY",
    prompt="一个温馨的中式茶馆，窗外竹影摇曳，水墨画风格",
    size="16:9",
    n=1,
    thinking_level="high",
    verbose=True
)
print(result["outputFiles"][0]["url"])
```

## Unique Features of Nano Banana 2

### 1. Character Consistency (up to 5 characters)

Provide reference images of characters to maintain their appearance across multiple generations:

```python
from scripts.generate_image import generate_image

result = generate_image(
    api_key="YOUR_API_KEY",
    prompt="A young woman in a red dress standing in front of the Eiffel Tower, golden hour",
    size="9:16",
    reference_images=["https://example.com/character-ref.jpg"],
    thinking_level="high"
)
```

### 2. Multi-language Text Rendering

Nano Banana 2 excels at rendering accurate text in images, including Chinese characters:

```python
result = generate_image(
    api_key="YOUR_API_KEY",
    prompt='A coffee shop menu board with text "今日特调 拿铁 ¥28" written in elegant calligraphy, warm lighting',
    thinking_level="dynamic"
)
```

### 3. Image Text Translation/Localization

Translate text within an image while preserving the visual style:

```python
result = generate_image(
    api_key="YOUR_API_KEY",
    prompt="Translate the text in this image to Japanese, keeping the same visual style and layout",
    reference_images=["https://example.com/ad-with-english-text.jpg"],
    thinking_level="dynamic"
)
```

### 4. Infographics and Data Visualization

Convert notes and data into professional diagrams and infographics:

```python
result = generate_image(
    api_key="YOUR_API_KEY",
    prompt="Create an infographic showing global renewable energy growth from 2020-2025, with bar charts and icons for solar, wind, and hydro power",
    size="9:16",
    thinking_level="dynamic"
)
```

### 5. Background Replacement

Replace backgrounds while keeping the subject consistent:

```python
result = generate_image(
    api_key="YOUR_API_KEY",
    prompt="Change the background to a tropical beach with palm trees at sunset",
    reference_images=["https://example.com/portrait-photo.jpg"],
    thinking_level="high"
)
```

## API Reference (for custom integration)

### Create task

```python
from scripts.generate_image import create_task

task = create_task(
    api_key="YOUR_API_KEY",
    prompt="A serene mountain lake at sunset",
    size="1:1",
    n=1,
    thinking_level="high",
    reference_images=["https://example.com/ref.jpg"]
)
# Returns: {"taskId": 12345, "taskCode": "T2025...", "status": "submitted"}
```

### Query task

```python
from scripts.generate_image import query_task

result = query_task(api_key="YOUR_API_KEY", task_id=12345)
# Returns: {"taskId": 12345, "status": "completed", "outputFiles": [...]}
```

## Prompt writing guide

**Best structure**:
```
[Subject] + [Scene/Environment] + [Lighting] + [Art style] + [Quality level]
```

**Examples**:

- **Landscape**: `A serene mountain lake at sunset, golden light reflecting on water, surrounded by pine trees and distant snow-capped peaks, photorealistic, 4K quality`
- **Portrait**: `Portrait of a young Asian woman with long black hair, wearing a white dress, standing in a sunflower field, soft natural lighting, bokeh background, professional photography`
- **Product**: `A sleek minimalist wireless headphone, matte black finish, placed on a white marble surface, soft studio lighting, product photography, high detail`
- **Text rendering**: `A coffee shop sign with text "MORNING BREW" in elegant gold letters on a dark green background, vintage style, warm lighting`
- **Infographic**: `An infographic about ocean pollution, showing statistics with icons of fish, plastic bottles, and waves, clean modern design, blue color scheme`
- **Chinese text**: `一副春节对联，红底金字，上联"万事如意福临门"，下联"一帆风顺年年好"，传统书法风格`

**Tips**:
- Supports **both Chinese and English** prompts — Chinese text rendering is a core strength
- For text in images, use `thinking_level="dynamic"` for best accuracy
- Be specific and detailed about text content, font style, and placement
- Include art style keywords (photorealistic, watercolor, flat illustration, anime)
- Use `reference_images` when character or object consistency is needed

## Error codes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | Success | Proceed |
| -1 | General error | Check `message` field |
| 401 | Invalid API Key | Verify API key |
| 403 | No permission | Check permissions |
| 404 | Task not found | Verify taskId |
| 429 | Too many requests | Slow down |
| 500 | Server error | Retry later |

## Important notes

- Image generation takes **10-30 seconds** (faster with `minimal` thinking level). Always poll — never assume it's ready immediately.
- Image URLs expire after **7 days** — download promptly.
- The user must have an **API Key** configured.
- Failed generations **do not deduct credits**.
- Maximum **4 images** per request.
- Maximum **3 concurrent tasks** per API key.
- **Character consistency**: Up to 5 characters per workflow.
- **Object consistency**: Up to 14 objects per generation.
- **Resolution**: Supports 512px, 1K, 2K, 4K output.
- **Thinking levels**: Use `dynamic` for complex prompts with text, `high` for most cases, `minimal` for quick drafts.
