from __future__ import annotations

import asyncio
import base64
import random
from pathlib import Path

import httpx
from PIL import Image, ImageEnhance, ImageFilter

from app.core.booth_config import load_booth_config
from app.core.config import Settings
from app.models import Style

BACKGROUNDS_DIR = Path(__file__).resolve().parent.parent / "assets" / "backgrounds"
OUTFITS_DIR = Path(__file__).resolve().parent.parent / "assets" / "outfits"
MERCH_DIR = Path(__file__).resolve().parent.parent / "assets" / "merch"
SELFIE_EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "assets" / "selfie-examples"
STYLE_REFERENCES_DIR = Path(__file__).resolve().parent.parent / "assets" / "style-references"

MERCH_IMAGE = "merch.jpg"

IDENTITY_LOCK = """

MANDATORY FACE AND IDENTITY LOCK — HIGHEST PRIORITY
The PERSON reference is the only source of identity. Keep every foreground person's face unchanged and immediately
recognizable. Preserve the exact facial geometry, head shape, eyes, eyelids, eyebrows, nose, lips, jawline, cheeks,
ears, skin tone, age, ethnicity, distinctive features and natural asymmetry. Do not beautify, idealize, age, de-age,
swap, reconstruct or invent any face. Do not combine facial traits between people. Styling may change clothing,
background, lighting, pose and artistic rendering only; it must not change who the person is or alter their facial
features. If the output is illustrated or animated, retain the same facial proportions and distinctive features.
For a multi-frame sheet, the same unchanged identity must be consistent in every frame.
"""

# ---------- Culture: all camera-facing people + per-gender outfit + ethnic background ----------
PROMPT_CULTURE = """You are provided with the following reference images in this order:
1. PERSON - the original camera photo of one or more people.
2. OUTFIT REFERENCE(S) - one or two images showing the traditional costume (a female version and/or a male version).
3. OPTIONAL BACKGROUND - if a fourth image is provided, it shows the ethnic setting to place the people in.

This transformation applies to EVERY person who is standing in front of the camera and looking into the camera in the PERSON reference image - NOT to just one person. If several people are present, all of them are transformed together.


FOREGROUND SUBJECTS ONLY

The transformation applies ONLY to the person(s) standing in the FOREGROUND of the photo, directly in front of the camera and looking into it.

Remove ALL other people from the result:
- Anyone standing behind the foreground subjects, farther from the camera, partially visible, or otherwise in the BACKGROUND must be completely removed.
- Do NOT keep, dress, transform, or preserve background people in any way.
- Do NOT turn a background person into a foreground subject.
- The final background must contain only the described ethnic setting and never any human figures.


REFERENCE IMAGE 1 - PERSON (PRIMARY REFERENCE)

This is the most important reference.

Preserve the identity of EACH person standing in front of the camera and looking into it exactly.

For EVERY such person, keep unchanged:
- face
- facial features
- hairstyle
- facial expression
- body proportions
- skin tone
- age
- body shape
- pose
- body position
- head angle
- eye direction

Do not change the identity of any of these people.

Do not beautify, stylize or alter any person's appearance.

Never replace any face.

Never change any pose.

Never change any body position.

Never rotate any body.

The generated image should clearly show the same people photographed by the camera.

Do NOT add, duplicate or merge FOREGROUND subjects, and do NOT remove any FOREGROUND person who was facing the camera; the number of FOREGROUND people in the scene must stay exactly the same. Background people must be removed entirely and must never appear in the result.


OUTFIT REFERENCE(S) - TRADITIONAL COSTUME

The outfit reference image(s) define ONLY the clothing.

For all Yakut/Sakha costume styles, treat the supplied VEF_budka_v2 outfit image as a literal garment reference: reproduce that exact costume and its northern details, not a generic approximation of a Yakut costume.

If a female outfit reference is provided, use it for every woman/female-presenting person.

If a male outfit reference is provided, use it for every man/male-presenting person.

For EACH person, determine their gender and replace that person's clothing with the matching outfit reference (female -> female outfit, male -> male outfit). If only one outfit is available, dress every person with it, adapting subtly to their gender so it looks natural while keeping its traditional character.

Reproduce every visible detail: jacket, shirt, dress, pants, skirt, headwear, jewelry, accessories, textures, fabrics, patterns, colors, decorations.

Do not redesign the clothing.

Do not simplify it.

Do not invent new clothing.

The outfit should naturally fit each person's body while preserving the original pose.


BACKGROUND

The ethnic background is described in the LOCATION instructions and, if provided, shown in the optional BACKGROUND reference image.

Place ALL the FOREGROUND people into this ethnic setting.

If a BACKGROUND reference image is provided, recreate that exact place and match its perspective, lighting, shadows, atmosphere and color.

If NO background reference image is provided, generate the setting from the textual LOCATION description.

Keep everyone looking at the camera and keep each person's pose; only the environment behind them changes.

Match the outfit lighting to the background lighting.


POSE

Each person's pose always comes from Reference Image 1.

Never modify the position of anyone's:
- arms
- hands
- fingers
- legs
- feet
- shoulders
- torso
- head

Adapt the clothing to each existing pose.

Do not adapt any pose to the clothing.


REALISM

Generate a completely photorealistic image with realistic fabric folds, wrinkles, gravity, contact shadows, fabric thickness.

Hair must interact naturally with the headwear.

Everyone's feet must correctly contact the ground.

Shadows must be physically consistent.

Lighting on each outfit must match its background.

The transition between every subject and the background must be invisible.


ANATOMY

Maintain perfect human anatomy for every person: five fingers per hand, realistic hands, eyes, ears, proportional limbs, natural face symmetry, natural skin texture.

Avoid all anatomical distortions.


NEGATIVE REQUIREMENTS

Do NOT generate:
- collage effect
- pasted clothing
- pasted face
- floating objects
- duplicated or extra fingers
- warped anatomy
- distorted clothing
- blurry faces
- inconsistent lighting
- AI artifacts
- text, captions, logos, watermarks, borders, frames
- extra people that were not in the original photo
- people in the background / bystanders (always remove them)


FINAL GOAL

Generate a seamless, ultra-photorealistic DSLR-quality photograph: every person who was standing in front of the camera and looking into it now authentically wears this traditional outfit in the described ethnic setting, with all identities and poses preserved.
"""

# ---------- Travel: selfie + background + merch ----------
PROMPT_SELFIE_FILTER = """You are provided with exactly three reference images.

This transformation applies ONLY to the people standing in the FOREGROUND and facing the camera in the PERSON reference - NOT to anyone else. If several FOREGROUND people are present, all of them are transformed together. Do NOT add, duplicate or merge FOREGROUND subjects, and do NOT remove any FOREGROUND person who faced the camera; the number of FOREGROUND people must stay exactly the same. ANY people in the BACKGROUND must be completely removed from the result; the location scenery is recreated without any human figures.

REFERENCE IMAGE 1 - PERSON (PRIMARY REFERENCE)

This image defines ONLY the identity of the people present.

Preserve the identity of EACH person standing in front of the camera and looking into it, so that they are immediately recognizable.

For every such person, preserve:
- face
- facial features
- hairstyle
- facial expression
- age
- skin tone
- body proportions

Do NOT replace any face.

Do NOT change the identity of any person.

Stylize every person while preserving clear facial recognition for each.

The viewer should instantly recognize the same individuals.

REFERENCE IMAGE 2 - BACKGROUND

This image defines ONLY the location.

Recreate the exact place while adapting it into the illustration style.

Preserve:
- landmarks
- architecture
- landscape
- composition
- atmosphere
- lighting direction

REFERENCE IMAGE 3 - MERCH GARMENT (MERCH CLOTHING / OUTERWEAR)

This garment may be a T-shirt OR a warm winter jacket / parka / outerwear. Reproduce the EXACT type, cut, thickness, fabric and logo from the reference image — do NOT replace it with a plain T-shirt and do NOT reinterpret it as different clothing.

Dress EVERY person standing in front of the camera and looking into it in the exact merch garment shown.

Preserve exactly:
- colors
- artwork
- logo
- typography
- print placement
- proportions
- collar
- sleeves
- fabric shape
- fabric thickness
- garment type (T-shirt / winter jacket / parka)

The merch garment design must remain fully recognizable.

STYLE

Create a high-quality illustrated tourist postcard.

This is an illustration, NOT a photograph.

Illustration style:
- classic Soviet travel postcard
- Soviet children's book illustration
- mid-century printed illustration
- vintage travel poster aesthetics
- hand-painted gouache
- subtle watercolor texture
- clean ink outlines
- soft brush strokes
- rich but natural colors
- slightly simplified realistic shapes

The illustration should feel warm, nostalgic and handcrafted.

Avoid modern CGI or AI art aesthetics.

FACE STYLE

Although illustrated, EACH person's identity must remain highly recognizable.

For every person, preserve:
- facial proportions
- eye shape
- nose shape
- mouth shape
- hairstyle
- expression

Do NOT exaggerate facial features.

Avoid caricatures.

Avoid anime style.

Avoid Pixar style.

Avoid Disney style.

Avoid comic-book proportions.

Avoid chibi style.

The face should resemble a carefully painted portrait.

POSE

Generate a natural vacation selfie.

Create:
- natural head angle
- relaxed shoulders
- realistic selfie arm
- smartphone viewpoint
- natural body rotation

The pose should look spontaneous.

COMPOSITION

Create a premium tourist postcard illustration.

When there is a single person, they should occupy about 60-70% of the composition.

When several people are present, ALL of them must remain fully visible, well-framed and clearly recognizable; keep everyone who faces the camera in the frame.

The location should remain clearly visible.

Use balanced travel-poster composition.

COLORS

Use:
- warm vintage palette
- slightly muted colors
- rich blues
- warm reds
- cream highlights
- painted gradients

Avoid oversaturation.

Avoid neon colors.

DETAIL

Render:
- painted fabric folds
- soft hair strands
- painterly shadows
- illustrated vegetation
- realistic architectural details

The merch garment artwork must remain sharp and readable.

NEGATIVE REQUIREMENTS

Do NOT generate:
- photorealism
- 3D rendering
- Pixar
- Disney
- anime
- manga
- caricature
- comic book
- cel shading
- vector art
- low detail
- AI artifacts
- text
- borders
- postcard template
- stamps
- watermarks
- logos outside the merch garment
- exaggerated facial proportions
- extra people that were not in the original photo
- people in the background / bystanders (always remove them)
- missing people (do not remove anyone who faced the camera)

FINAL GOAL

Generate a beautiful illustrated tourist souvenir postcard inspired by classic Soviet travel postcards from the 1950s-1970s.

The illustration should look like it was hand-painted by a professional book illustrator using gouache and watercolor.

Every person must remain immediately recognizable from Reference Image 1.

The location must remain faithful to Reference Image 2.

The merch garment must remain faithful to Reference Image 3.

The final result should resemble a collectible vintage tourist postcard illustration rather than a modern digital artwork.
"""

PROMPT_SELFIE_NO_FILTER = """You are provided with exactly three reference images.

This transformation applies ONLY to the people standing in the FOREGROUND and facing the camera in the PERSON reference - NOT to anyone else. If several FOREGROUND people are present, all of them are transformed together. Do NOT add, duplicate or merge FOREGROUND subjects, and do NOT remove any FOREGROUND person who faced the camera; the number of FOREGROUND people must stay exactly the same. ANY people in the BACKGROUND must be completely removed from the result; the location scenery is recreated without any human figures.

REFERENCE IMAGE 1 - PERSON (PRIMARY REFERENCE)

This image defines ONLY the identity of the people present.

For EVERY person standing in front of the camera and looking into it, preserve exactly:
- face
- facial features
- hairstyle
- facial expression
- age
- skin tone
- body proportions
- body shape
- eye color
- facial hair (if present)
- natural appearance

Do not change the identity of any person.

Do not beautify, stylize or alter any person's appearance.

Never replace any face.

Every generated person must clearly be the same individuals shown in Reference Image 1.

REFERENCE IMAGE 2 - BACKGROUND

This image defines ONLY the environment.

Place the people into this exact location.

Match perfectly:
- perspective
- lighting
- atmosphere
- shadows
- reflections
- weather
- exposure
- white balance
- color grading
- depth of field
- lens characteristics
- ambient light

The location must appear completely authentic.

REFERENCE IMAGE 3 - MERCH GARMENT (MERCH CLOTHING / OUTERWEAR)

This image defines ONLY the merch garment.

The garment may be a T-shirt OR a warm winter jacket / parka / outerwear. Reproduce the EXACT type, cut, thickness, fabric and logo from the reference image — do NOT replace it with a plain T-shirt and do NOT reinterpret it as different clothing.

Replace EVERY person's upper-body clothing with the exact merch garment shown in Reference Image 3.

Preserve exactly:
- color
- material
- texture
- collar
- sleeves
- stitching
- seams
- wrinkles
- folds
- fit
- logos
- graphics
- artwork
- typography
- branding
- print colors
- print placement
- proportions
- garment type (T-shirt / winter jacket / parka)
- fabric thickness

Do not redesign the merch garment.

Do not simplify the graphics.

Do not reinterpret the artwork.

Do not invent missing details.

The print must remain perfectly readable.

The merch garment must naturally wrap around the person's body with realistic folds and stretching.

SELFIE POSE

Unlike Reference Image 1, do NOT preserve the original pose.

Reference Image 1 defines ONLY the identities of the people.

If there is one person, generate an entirely new pose that naturally corresponds to a real handheld selfie.

If several people are present, generate a natural group selfie in which every camera-facing person stays fully visible, well-framed and recognizable; do not cut anyone out of the frame.

Generate:
- realistic head angle
- realistic neck position
- natural shoulder rotation
- natural torso rotation
- realistic arm position
- realistic body balance
- realistic weight distribution

The head may naturally:
- tilt slightly
- rotate toward the phone
- lean slightly forward
- have a subtle selfie angle

The shoulders should naturally rotate toward the smartphone.

The torso should naturally follow the head orientation.

The free arm should hang naturally or rest comfortably.

The smartphone-holding arm should appear naturally extended.

The body should not appear stiff or perfectly symmetrical.

The eyes must naturally look toward the smartphone camera.

The facial expression should remain the same as Reference Image 1.

SELFIE CAMERA

Generate a genuine smartphone selfie.

Do NOT preserve the original camera viewpoint.

Instead generate:
- handheld smartphone perspective
- arm-length camera distance
- realistic front-camera wide-angle lens (approximately 24-28 mm equivalent)
- slight perspective distortion typical of smartphone selfies
- authentic selfie framing

The smartphone may be partially visible.

The arm holding the phone may be visible.

The composition should naturally include both the person and the surrounding location.

The image should immediately be recognizable as a genuine selfie.

REALISM

Generate a completely photorealistic image.

Everything must appear physically believable.

Generate realistic:
- lighting
- shadows
- contact shadows
- ambient occlusion
- reflections
- gravity
- fabric interaction
- skin texture
- hair strands
- fabric folds
- perspective

The merch garment must naturally follow the body.

The lighting on the person must perfectly match the environment.

The transition between the subject and the background must be invisible.

The result must look like one real photograph.

ANATOMY

Maintain perfect human anatomy.

Generate:
- five fingers per hand
- realistic hands
- realistic wrists
- realistic elbows
- realistic shoulders
- proportional limbs
- natural neck
- realistic ears
- realistic eyes
- realistic teeth
- natural skin texture
- realistic hair

Avoid:
- extra fingers
- missing fingers
- duplicated limbs
- warped hands
- twisted wrists
- broken anatomy
- distorted face

POSTCARD TRAVEL SELFIE

Generate a premium vacation selfie suitable for printing as the front image of a tourist souvenir postcard.

This is NOT a designed postcard.

Do NOT generate:
- postcard template
- borders
- frames
- decorative graphics
- stickers
- stamps
- captions
- typography
- titles
- watermarks
- graphic elements

The image must remain a genuine photograph.

The photograph should resemble premium travel photography captured casually with a flagship smartphone.

Use:
- beautiful natural lighting
- vibrant but realistic colors
- premium travel atmosphere
- authentic vacation mood
- realistic HDR
- crisp details
- excellent composition
- DSLR-like image quality while retaining a smartphone selfie perspective

The location should feel iconic, memorable and visually impressive.

NEGATIVE REQUIREMENTS

Do NOT generate:
- pasted face
- pasted body
- collage effect
- floating objects
- floating hands
- floating phone
- duplicated limbs
- duplicated fingers
- extra fingers
- missing fingers
- warped anatomy
- blurry face
- blurry clothing
- blurry logo
- incorrect merch garment graphics
- inconsistent lighting
- inconsistent shadows
- inconsistent perspective
- AI artifacts
- excessive HDR
- beauty filters
- cartoon style
- illustrations
- painterly effects
- text
- captions
- borders
- frames
- watermarks
- extra people that were not in the original photo
- people in the background / bystanders (always remove them)
- missing people (do not remove anyone who faced the camera)

FINAL GOAL

Generate a seamless ultra-photorealistic smartphone vacation selfie.

Every person must remain completely identical to Reference Image 1.

The location must remain completely faithful to Reference Image 2.

The merch garment must remain completely faithful to Reference Image 3.

The pose, body orientation, shoulder rotation, head angle, arm position, eye direction, perspective and camera viewpoint must all be newly generated to naturally match a genuine handheld selfie (or a natural group selfie when several people are present).

The image must NOT look like the original portrait inserted into another background.

Instead, it should look as though the entire photograph was captured from scratch as a real selfie at this exact location while naturally wearing the exact merchandise merch garment.

The final image should be indistinguishable from a real high-end smartphone travel selfie and suitable for printing as the front image of a premium tourist souvenir postcard.
"""


class ImageProvider:
    async def generate(self, source: Path, style: Style, output: Path, aspect_ratio: str = "2:3", *, six_frame_sheet: bool = False) -> None:
        raise NotImplementedError



class DemoImageProvider(ImageProvider):
    async def generate(self, source: Path, style: Style, output: Path, aspect_ratio: str = "2:3", *, six_frame_sheet: bool = False) -> None:
        def render() -> None:
            with Image.open(source) as image:
                image = image.convert("RGB")
                image = ImageEnhance.Color(image).enhance(1.25)
                image = ImageEnhance.Contrast(image).enhance(1.12)
                image = image.filter(ImageFilter.GaussianBlur(radius=0.15))
                if six_frame_sheet:
                    cell = image.resize((600, 600), Image.LANCZOS)
                    sheet = Image.new("RGB", (1200, 1800), "white")
                    for index in range(6):
                        column, row = divmod(index, 3)
                        sheet.paste(cell, (column * 600, row * 600))
                    sheet.save(output, "PNG", dpi=(300, 300))
                else:
                    image.save(output, quality=94)
        await asyncio.to_thread(render)


class OpenRouterImageProvider(ImageProvider):
    def __init__(self, settings: Settings):
        self.settings = settings

    @staticmethod
    def _existing(files: list[str], base: Path) -> list[Path]:
        return [base / name for name in files if (base / name).is_file()]

    def _culture_outfits(self, style: Style, gender: str | None = None) -> list[Path]:
        """Return outfit references for the given gender (only that gender's costume),
        falling back to both genders when gender is unknown. Only existing files are
        considered, so a missing/renamed image can never be picked."""
        groups = (gender,) if gender in ("male", "female") else ("male", "female")
        paths: list[Path] = []
        seen: set[str] = set()
        for group in groups:
            options = self._existing(style.outfit_images.get(group) or [], OUTFITS_DIR)
            if not options:
                continue
            chosen = random.choice(options)
            if chosen.name not in seen:
                seen.add(chosen.name)
                paths.append(chosen)
        if not paths:
            raise RuntimeError(f"Style {style.id} has no existing outfits for {'/'.join(groups)}")
        print(f"[BOOTH] style={style.id} gender={gender} outfits={[p.name for p in paths]}", flush=True)
        return paths

    def _culture_background(self, style: Style) -> Path | None:
        options = self._existing(style.background_images or [], BACKGROUNDS_DIR)
        if not options:
            return None
        return random.choice(options)

    def _pick(self, style: Style, gender: str | None) -> Path:
        backgrounds = self._existing(style.background_images or [], BACKGROUNDS_DIR)
        if not backgrounds:
            raise RuntimeError(f"Style {style.id} has no existing backgrounds")
        return random.choice(backgrounds)

    def _merch(self, style: Style) -> Path:
        if style.merch_image:
            candidate = MERCH_DIR / style.merch_image
            if candidate.is_file():
                return candidate
        path = MERCH_DIR / MERCH_IMAGE
        if not path.is_file():
            raise RuntimeError(f"Merch image not found: {path}")
        return path

    async def generate(self, source: Path, style: Style, output: Path, aspect_ratio: str = "2:3", *, six_frame_sheet: bool = False) -> None:
        if not self.settings.openrouter_api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not configured")

        def to_b64(path: Path) -> str:
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode("ascii")

        await asyncio.sleep(0)

        if style.category == "culture":
            outfit_paths = self._culture_outfits(style)
            background_path = self._culture_background(style)
            refs_to_encode = [source] + outfit_paths
            if background_path:
                refs_to_encode.append(background_path)
            encoded = await asyncio.gather(*(asyncio.to_thread(to_b64, p) for p in refs_to_encode))
            person_b64, *rest = encoded
            n_outfits = len(outfit_paths)
            input_references = [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{person_b64}"}},
            ] + [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b}"}}
                for b in rest
            ]
            prompt = PROMPT_CULTURE
            if style.id == "costume-female-jewelry":
                prompt = """You are provided with a PERSON reference and a JEWELRY reference.
Preserve the person's identity, face, hair, clothing, body, pose, framing and background exactly.
Add ONLY the authentic Sakha silver jewelry visible in the JEWELRY reference: the forehead ornament,
long side earrings, chest necklace and layered silver pendants. The jewelry reference defines accessories
only; do not copy its red dress, fur coat, hood, lighting or scenery. Do not change any garment or add a costume.
Make the jewelry fit naturally and remain sharply visible. Do not add people, text, logos or watermarks.
"""
            print(f"[BOOTH] culture refs person+{n_outfits}outfits+{'bg' if background_path else 'textbg'}", flush=True)
        elif style.category == "travel":
            bg_path = self._pick(style, None)
            person_b64, bg_b64 = await asyncio.gather(
                asyncio.to_thread(to_b64, source),
                asyncio.to_thread(to_b64, bg_path),
            )
            if style.id == "lena-pillars-winter":
                prompt = """Create a realistic winter portrait from the PERSON reference at the Lena Pillars in winter.
Preserve the person's exact identity, natural pose and anatomy. Dress them in an ordinary warm winter jacket with
no logos, no branded merchandise and no reference jacket. Use only the BACKGROUND reference for the Lena Pillars
location. Do not create a selfie pose, selfie arm or smartphone perspective. Do not add text or extra people.
"""
                input_references = [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{person_b64}"}},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{bg_b64}"}},
                ]
            else:
                merch_path = self._merch(style)
                merch_b64 = await asyncio.to_thread(to_b64, merch_path)
                prompt = PROMPT_SELFIE_NO_FILTER
                input_references = [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{person_b64}"}},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{bg_b64}"}},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{merch_b64}"}},
                ]
        else:
            person_b64 = await asyncio.to_thread(to_b64, source)
            input_references = [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{person_b64}"}},
            ]
            if style.style_reference_image:
                reference_path = STYLE_REFERENCES_DIR / style.style_reference_image
                if not reference_path.is_file():
                    raise RuntimeError(f"Style reference not found: {reference_path}")
                reference_b64 = await asyncio.to_thread(to_b64, reference_path)
                input_references.append(
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{reference_b64}"}},
                )
            if style.style_reference_image:
                if style.id == "fashion":
                    prompt = """Create a realistic high-fashion editorial portrait from the PERSON reference.
Use Reference Image 2 only for its avant-garde mirrored geometry, sculptural silver couture, dramatic studio light
and composition. Add authentic Yakut/Sakha geometric ornament and silver jewelry details to the garment. Keep real
skin, natural anatomy, photographic materials and the person's exact identity. Do not make it anime, animated,
cartoon, 3D, painted or illustrated. Do not copy the reference model's face, text, logos or watermark.
"""
                elif style.id == "postcard-soviet":
                    prompt = """Create a finished soft hand-painted Soviet New Year postcard from the PERSON reference.
Use Reference Image 2 as the exact target for brush texture, nostalgic printed-paper finish, winter palette,
falling snow, Christmas tree and warm seasonal composition. Keep faces recognizable and anatomy natural.
Do not copy the reference people's faces, watermark or dog. Do not add any animals, logos, watermarks or extra people.
The only lettering allowed is the exact greeting «С Новым Годом» at the bottom in a large elegant red vintage script.
"""
                elif style.id.startswith("postcard-"):
                    prompt = """Create a realistic professional New Year portrait from the PERSON reference.
Use Reference Image 2 only for its seasonal palette, lighting, snow, decorations and composition. Render natural
skin, real fabric and fur, believable anatomy, photographic detail and physically plausible light.
Do not make it anime, manga, chibi, cel-shaded, 3D, cartoon, painted or illustrated. Do not copy the reference people's faces, text,
watermarks, animals or exact poses. Preserve the people from Reference Image 1 as the only identities. Do not add
text, logos, borders, watermarks, animals or extra people.
"""
                else:
                    prompt = """Create a strongly stylized, fully illustrated character poster from the PERSON reference.
The result must clearly look hand-drawn and graphic, not like a photograph with a light filter. Keep the same number
of foreground people and preserve their recognizable identities, but render the entire image as polished key art.
Reference Image 2 is a STYLE REFERENCE ONLY. Copy its illustration technique, line work, cel shading, color palette,
sunset lighting, character rendering and cinematic composition very closely. Use clearly visible dark ink contours
around the face, jaw, nose, eyes, hair, clothing and body silhouette. Build forms from clean angular color planes,
hard-edged shadows, crisp rim light and bold graphic highlights. Simplify skin and fabric into deliberate painted
shapes while retaining the person's defining facial proportions and features. Avoid photographic skin texture,
soft airbrushing, shallow-depth-of-field photography and photorealistic rendering. Every element, including the
background, must share the same illustrated loading-screen aesthetic. Do not copy the reference's people, faces,
weapons, tattoos, clothing or exact scene. The people from Reference Image 1 must remain the only identities.
Do not add text, logos, borders, watermarks or extra people.
"""
            else:
                prompt = """Create a premium event portrait from the PERSON reference.
Preserve every foreground person's identity, face, age, skin tone, expression and recognizable features exactly.
Keep the same number of foreground people. Remove background bystanders. Apply the requested visual theme to clothing,
lighting and environment while keeping faces realistic and immediately recognizable. Use polished editorial composition,
clean anatomy, natural hands and print-ready detail. Do not add text, logos, watermarks, borders or extra people."""

        if style.prompt_template:
            prompt += f"\nLOCATION\n\n{style.prompt_template}\n"

        # This invariant is appended to every provider branch and every style,
        # so no theme-specific prompt can accidentally weaken face preservation.
        prompt += IDENTITY_LOCK

        if six_frame_sheet:
            prompt += """

OUTPUT LAYOUT — FOLLOW EXACTLY
Create ONE finished vertical 2:3 print sheet from the single person reference in ONE generation.
The sheet must contain exactly SIX distinct square photos arranged edge-to-edge in a precise 2-column by 3-row grid.
Generate a different natural pose, expression, crop or camera angle in every cell while preserving the exact same
person, identity, face, clothing theme and visual style in all six cells. Each cell must look like a separate photo,
not a crop of one larger scene. Fill the entire canvas. Use no gaps, margins, frames, captions, logos or text.
Keep every face safely inside its square cell. The vertical division must be exactly centered so the sheet can be
cut into two equal photo strips, each containing three square photos.
"""

        config = load_booth_config()
        payload = {
            "model": self.settings.openrouter_model,
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "quality": config.image.quality,
            "output_format": "png",
            "stream": False,
            "input_references": input_references,

        }

        headers = {
            "Authorization": f"Bearer {self.settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "X-Title": "AI Photo Booth",
        }

        print(f"[BOOTH] generating style={style.id} category={style.category} "
              f"quality={payload['quality']} aspect={payload['aspect_ratio']} "
              f"refs={len(input_references)}", flush=True)

        async def call_api() -> bytes:
            def request() -> bytes:
                with httpx.Client(timeout=600) as client:
                    resp = client.post(
                        "https://openrouter.ai/api/v1/images",
                        headers=headers,
                        json=payload,
                    )
                    try:
                        resp.raise_for_status()
                    except httpx.HTTPStatusError as error:
                        raise RuntimeError(
                            f"OpenRouter API {resp.status_code}: {resp.text[:500]}"
                        ) from error
                    data = resp.json()

                    result = data.get("data", [{}])[0]
                    if "b64_json" in result:
                        return base64.b64decode(result["b64_json"])
                    if "url" in result:
                        with httpx.Client(timeout=300) as dl:
                            dl_resp = dl.get(result["url"])
                            dl_resp.raise_for_status()
                            return dl_resp.content

                    b64 = result.get("b64")
                    if b64:
                        return base64.b64decode(b64)
                    url = result.get("output", {}).get("url")
                    if url:
                        with httpx.Client(timeout=300) as dl:
                            dl_resp = dl.get(url)
                            dl_resp.raise_for_status()
                            return dl_resp.content

                    raise RuntimeError(f"Unexpected OpenRouter response shape: {data}")

            return await asyncio.to_thread(request)

        image_bytes = await call_api()
        output.write_bytes(image_bytes)


def build_provider(settings: Settings) -> ImageProvider:
    return OpenRouterImageProvider(settings) if settings.image_provider == "openrouter" else DemoImageProvider()
