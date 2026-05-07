#!/usr/bin/env python3
"""
Nano Banana 2 (nano-banana-2-bltcy) Image Generation Script
Generates images using Nano Banana 2 (Gemini 3.1 Flash Image) via async task workflow.

Nano Banana 2 is Google DeepMind's next-generation image model with:
- World knowledge enhancement (Gemini knowledge base + web search)
- Multi-language text rendering (Chinese, English, etc.)
- Character consistency (up to 5 characters per workflow)
- Object consistency (up to 14 objects per generation)
- Configurable thinking levels (minimal, high, dynamic)
- Image editing (background replacement, style transfer, localization)
- Resolution: 512px to 4K

Usage:
    python generate_image.py --api-key YOUR_KEY --prompt "A serene Japanese garden"
    python generate_image.py --api-key YOUR_KEY --prompt "猫咪在太空" --size 16:9 --thinking-level dynamic
    python generate_image.py --api-key YOUR_KEY --prompt "same character in new scene" --reference-images "https://example.com/ref.jpg"
"""

import argparse
import json
import sys
import time
import warnings
from typing import List, Optional

import requests


# Skill 版本号 —— 与 API 返回的 skillVersion 对比，不匹配时提示用户升级
# 格式: 主版本.次版本.修订号
SKILL_VERSION = "1.0.0"

BASE_URL = "https://www.moodmax.cn/open_api/v2"
POLL_INTERVAL = 3  # seconds
MAX_POLL = 100     # max ~5 minutes


def _parse_version(version_str: str) -> tuple[int, int, int]:
    """Parse version string like '1.2.3' into (1, 2, 3)."""
    try:
        parts = version_str.split(".")
        return (int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        return (0, 0, 0)


def _check_skill_version(api_version: Optional[str]) -> None:
    """
    Compare local SKILL_VERSION with API's skillVersion.
    Print a warning if the API has a newer major/minor version.
    """
    if not api_version:
        return

    local = _parse_version(SKILL_VERSION)
    remote = _parse_version(api_version)

    if remote[0] > local[0]:
        # Major version mismatch — breaking change, must upgrade
        warnings.warn(
            f"\n[Skill Upgrade Required] Your skill version is {SKILL_VERSION}, "
            f"but the API requires {api_version}.\n"
            f"Please download and reinstall the latest skill files:\n"
            f"  https://github.com/daimali/nano-banana2-skill.git\n",
            UserWarning
        )
    elif remote[0] == local[0] and remote[1] > local[1]:
        # Minor version mismatch — new features available, recommend upgrade
        warnings.warn(
            f"\n[Skill Upgrade Recommended] Your skill version is {SKILL_VERSION}, "
            f"but the API has newer features in {api_version}.\n"
            f"Consider downloading the latest skill files:\n"
            f"  https://github.com/daimali/nano-banana2-skill.git\n",
            UserWarning
        )


def create_task(
    api_key: str,
    prompt: str,
    size: str = "16:9",
    n: int = 1,
    thinking_level: str = "high",
    reference_images: Optional[List[str]] = None
) -> dict:
    """
    Create an image generation task. Returns the task dict with taskId.

    Args:
        api_key: API key from moodmax.cn
        prompt: Image description (supports Chinese and English)
        size: Aspect ratio (e.g., "16:9", "1:1", "4:1", "1:4")
        n: Number of images to generate (1-4)
        thinking_level: Reasoning depth - "minimal", "high", or "dynamic"
        reference_images: Optional list of image URLs for character/object consistency
    """
    url = f"{BASE_URL}/create-task"
    params = {
        "size": size,
        "n": n,
        "thinkingLevel": thinking_level,
    }

    # Add reference images if provided
    if reference_images:
        params["referenceImages"] = reference_images

    payload = {
        "apiKey": api_key,
        "modelCode": "nano-banana-2-bltcy",
        "prompt": prompt,
        "skillVersion": SKILL_VERSION,
        "params": params
    }
    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if data.get("code") != 0:
        raise RuntimeError(f"Create task failed: {data.get('message')} (code={data.get('code')})")

    result = data["data"]
    _check_skill_version(result.get("skillVersion"))
    return result


def query_task(api_key: str, task_id: int) -> dict:
    """Query task status by taskId."""
    url = f"{BASE_URL}/query-task"
    payload = {
        "apiKey": api_key,
        "taskId": task_id
    }
    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if data.get("code") != 0:
        raise RuntimeError(f"Query task failed: {data.get('message')} (code={data.get('code')})")

    result = data["data"]
    _check_skill_version(result.get("skillVersion"))
    return result


def generate_image(
    api_key: str,
    prompt: str,
    size: str = "16:9",
    n: int = 1,
    thinking_level: str = "high",
    reference_images: Optional[List[str]] = None,
    poll_interval: int = POLL_INTERVAL,
    max_poll: int = MAX_POLL,
    verbose: bool = False
) -> dict:
    """
    Generate an image and wait for completion (including OSS transfer).

    The API returns status="processing" until the image is both generated **and**
    transferred to OSS. The task is only considered `completed` when the final URL is ready.

    Returns:
        dict: The final task data with status "completed" and outputFiles.
    """
    # Step 1: Create task
    task = create_task(api_key, prompt, size, n, thinking_level, reference_images)
    task_id = task["taskId"]

    if verbose:
        print(f"[Task created] taskId={task_id}, status={task['status']}")

    # Step 2: Poll until complete
    for i in range(max_poll):
        time.sleep(poll_interval)
        result = query_task(api_key, task_id)
        status = result["status"]

        if verbose:
            progress = result.get("progress", 0)
            output_files = result.get("outputFiles", [])
            url = output_files[0].get("url") if output_files else None
            print(
                f"[Poll {i+1}/{max_poll}] status={status}, progress={progress}%, "
                f"url={'yes' if url else 'no'}"
            )

        if status == "completed":
            output_files = result.get("outputFiles", [])
            if output_files and output_files[0].get("url"):
                if verbose:
                    print(f"[Done] Image URL: {output_files[0]['url']}")
                return result
            else:
                # Should not happen if API logic is correct, but handle gracefully
                raise RuntimeError(
                    f"Image generation completed but no URL available. "
                    f"outputFiles={output_files}"
                )
        elif status == "failed":
            raise RuntimeError(f"Image generation failed: {result.get('errorMessage', 'Unknown error')}")
        # else: processing / submitted -> keep polling

    raise TimeoutError(f"Image generation timed out after {max_poll * poll_interval} seconds")


def main():
    parser = argparse.ArgumentParser(description="Generate images with Nano Banana 2 (nano-banana-2-bltcy)")
    parser.add_argument("--api-key", required=True, help="Your API key from https://www.moodmax.cn")
    parser.add_argument("--prompt", required=True, help="Image description (Chinese and English both work well)")
    parser.add_argument("--size", default="16:9",
                        help="Aspect ratio: 1:1, 16:9, 9:16, 4:3, 3:2, 2:3, 21:9, 9:21, 4:1, 1:4, 8:1, 1:8")
    parser.add_argument("--n", type=int, default=1, help="Number of images (1-4)")
    parser.add_argument("--thinking-level", default="high", choices=["minimal", "high", "dynamic"],
                        help="Reasoning depth: minimal (fastest), high (balanced), dynamic (best for complex/text)")
    parser.add_argument("--reference-images", default=None,
                        help="Comma-separated URLs of reference images for character/object consistency")
    parser.add_argument("--verbose", action="store_true", help="Show progress logs")

    args = parser.parse_args()

    # Parse reference images
    ref_images = None
    if args.reference_images:
        ref_images = [url.strip() for url in args.reference_images.split(",") if url.strip()]

    try:
        result = generate_image(
            api_key=args.api_key,
            prompt=args.prompt,
            size=args.size,
            n=args.n,
            thinking_level=args.thinking_level,
            reference_images=ref_images,
            verbose=args.verbose
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except TimeoutError as e:
        print(f"Timeout: {e}", file=sys.stderr)
        sys.exit(1)
    except requests.RequestException as e:
        print(f"Network error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
