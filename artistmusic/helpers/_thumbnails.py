# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# Adapted from CyberPixelPro/AviaxMusic for Elevenyts.

import os

import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

from Elevenyts import config, logger
from Elevenyts.helpers import Track


class Thumbnail:
    def __init__(self):
        self.rect = (914, 514)
        self.fill = (255, 255, 255)
        self.mask = Image.new("L", self.rect, 0)
        try:
            self.font1 = ImageFont.truetype("Elevenyts/helpers/Raleway-Bold.ttf", 30)
            self.font2 = ImageFont.truetype("Elevenyts/helpers/Inter-Light.ttf", 30)
        except OSError:
            self.font1 = ImageFont.load_default()
            self.font2 = ImageFont.load_default()
        self.session: aiohttp.ClientSession | None = None

    async def start(self) -> None:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def close(self) -> None:
        if self.session and not self.session.closed:
            await self.session.close()

    async def save_thumb(self, output_path: str, url: str) -> str:
        if self.session is None or self.session.closed:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    resp.raise_for_status()
                    with open(output_path, "wb") as f:
                        f.write(await resp.read())
        else:
            async with self.session.get(url) as resp:
                resp.raise_for_status()
                with open(output_path, "wb") as f:
                    f.write(await resp.read())
        return output_path

    async def generate(self, song: Track, size=(1280, 720)) -> str:
        try:
            os.makedirs("cache", exist_ok=True)
            temp = f"cache/temp_{song.id}.jpg"
            output = f"cache/{song.id}.png"
            if os.path.exists(output):
                return output

            await self.save_thumb(temp, song.thumbnail)
            thumb = Image.open(temp).convert("RGBA").resize(
                size,
                Image.Resampling.LANCZOS,
            )
            blur = thumb.filter(ImageFilter.GaussianBlur(25))
            image = ImageEnhance.Brightness(blur).enhance(0.40)

            rect = ImageOps.fit(
                thumb,
                self.rect,
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.5),
            )
            ImageDraw.Draw(self.mask).rounded_rectangle(
                (0, 0, self.rect[0], self.rect[1]),
                radius=15,
                fill=255,
            )
            rect.putalpha(self.mask)
            image.paste(rect, (183, 30), rect)

            draw = ImageDraw.Draw(image)
            channel = (song.channel_name or "YouTube")[:25]
            views = song.view_count or ""
            duration = song.duration or "00:00"
            title = song.title or "Unknown"

            draw.text(
                xy=(50, 560),
                text=f"{channel} | {views}",
                font=self.font2,
                fill=self.fill,
            )
            draw.text((50, 600), title[:50], font=self.font1, fill=self.fill)
            draw.text((40, 650), "0:01", font=self.font1, fill=self.fill)
            draw.line([(140, 670), (1160, 670)], fill=self.fill, width=5, joint="curve")
            draw.text((1185, 650), duration, font=self.font1, fill=self.fill)

            image.save(output)
            try:
                os.remove(temp)
            except OSError:
                pass
            return output
        except Exception as e:
            logger.warning(f"Thumbnail generation failed: {e}")
            return config.DEFAULT_THUMB
