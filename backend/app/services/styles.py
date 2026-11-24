from app.models import Style


def style(
    id: str,
    name: str,
    description: str,
    color: str,
    prompt: str,
    *,
    strips: bool = True,
    category: str = "theme",
    backgrounds: list[str] | None = None,
    outfits: dict[str, list[str]] | None = None,
    merch: str | None = None,
    reference: str | None = None,
) -> Style:
    return Style(
        id=id,
        name=name,
        description=description,
        preview_color=color,
        category=category,
        prompt_template=prompt,
        background_images=backgrounds or [],
        outfit_images=outfits or {},
        merch_image=merch,
        style_reference_image=reference,
        supports_double_strip=strips,
    )


STYLES: list[Style] = [
    style("costume-male-summer", "Якутский костюм · мужской летний", "Традиционный летний образ", "#b98342", "Use only the clothing from the outfit reference. Dress every foreground person in this authentic Sakha men's summer costume and place them beside the Lena Pillars.", category="culture", backgrounds=["yakutia-lenskie-stolby-summer.jpg"], outfits={"male": ["yakut_male_no_hat.jpg"]}),
    style("costume-male-winter", "Якутский костюм · мужской зимний", "Тёплый северный образ", "#6ba6d6", "Use only the clothing from the outfit reference. Dress every foreground person in this warm authentic Sakha men's winter costume and place them in winter Yakutia.", category="culture", backgrounds=["yakutia-lenskie-stolby.jpg"], outfits={"male": ["yakut_male_1.jpg"]}),
    style("costume-male-north", "Якутский костюм · мужской северный", "Суровый северный образ", "#506986", "Use only the clothing from the northern male outfit reference. Reproduce its fur-trimmed traditional northern costume, beadwork, long-hair details, boots and red leg coverings exactly. Create an authentic ceremonial northern Sakha men's portrait with a realistic Yakutian landscape.", category="culture", backgrounds=["yakutia-lenskie-stolby.jpg"], outfits={"male": ["yakut_north_male.jpg"]}),
    style("costume-male-botur", "Якутский костюм · Ботур", "Образ якутского богатыря", "#a65c39", "Use the Botur warrior outfit reference as the exact foundation. Reproduce the helmet, layered dark armor, shoulder guards, segmented chest and skirt armor, belt, olive undergarment and sword exactly as shown. Preserve exact identity, pose and anatomy; make it heroic, realistic and respectful.", category="culture", backgrounds=["yakutia-lenskie-stolby-summer.jpg"], outfits={"male": ["yakut_botur.jpg"]}),
    style("costume-female-summer", "Якутский костюм · женский летний", "Лёгкий традиционный образ", "#e08fa8", "Use only the clothing from the outfit reference. Dress every foreground person in this authentic Sakha women's summer costume and place them beside the Lena Pillars.", category="culture", backgrounds=["yakutia-lenskie-stolby-summer.jpg"], outfits={"female": ["yakut_female_1.jpg"]}),
    style("costume-female-winter", "Якутский костюм · женский зимний", "Тёплый зимний образ", "#b9d8ec", "Use only the clothing from this exact female winter outfit reference. Reproduce the red embroidered parka, black fur panels, large brown fur hood and cuffs, white geometric embroidery, silver chest ornaments, mittens and fur-trimmed boots exactly. Dress every foreground person in this warm authentic Sakha women's winter costume in winter Yakutia.", category="culture", backgrounds=["yakutia-lenskie-stolby.jpg"], outfits={"female": ["yakut_winter_female.jpg"]}),
    style("costume-female-north", "Якутский костюм · женский северный", "Северная церемония", "#7b93b1", "Use only the clothing from the northern female outfit reference. Reproduce its brown fur-trimmed coat, colorful beadwork, headwear, white fur cuffs and traditional boots exactly. Create an authentic ceremonial northern Sakha women's portrait with a calm northern atmosphere.", category="culture", backgrounds=["yakutia-lenskie-stolby.jpg"], outfits={"female": ["yakut_north_female.jpg"]}),
    style("costume-female-jewelry", "Якутский костюм · украшения", "Традиционные серебряные украшения", "#c7c9d6", "Add only the authentic Sakha silver jewelry from the reference: the forehead ornament, long side earrings, chest necklace and layered silver pendants. Keep the person's original clothing, hair, body, pose, background and every other detail unchanged. Do not add a costume, fur, hat or new clothing.", category="culture", backgrounds=["yakutia-lenskie-stolby-summer.jpg"], outfits={"female": ["yakut_jewelry.jpg"]}),
    style("lena-pillars-winter", "Ленские столбы · зима", "Зимняя Якутия", "#8cb8db", "The location is the Lena Pillars in winter Yakutia. Every foreground person wears the exact warm winter jacket from the merchandise reference.", category="travel", backgrounds=["yakutia-lenskie-stolby.jpg"], merch="merch_yakutia.jpg"),
    style("fashion", "Мода", "Современная fashion-съёмка", "#d99b8f", "Create a high-fashion editorial portrait with bold contemporary styling, studio lighting and premium magazine photography. Preserve exact identity."),
    style("frozen-face", "Замерзшее лицо", "Морозный арт-эффект", "#9ccfe1", "Create a photorealistic extreme-Yakutian-frost portrait with clearly visible delicate white frost crystals on the eyebrows, hair and especially along both the upper and lower eyelashes of both eyes. The eyelashes must look naturally coated with fine sparkling hoarfrost, with individual frosted lashes visible in sharp detail. Keep the eyes open, unobstructed and recognizable; do not alter their shape, color or expression. Add visible breath and cold icy light. Preserve exact identity and keep the face natural."),
    style("anime", "Аниме", "Яркий аниме-портрет", "#ef7ca6", "Use Reference Image 2 as the strict, primary and dominant style target. Reproduce its exact overall art direction as closely as possible: the same polished Japanese fashion-anime illustration finish, line-art thickness and placement, expressive oversized anime eyes, face rendering, hair rendering with warm brown and honey highlights, soft pastel lavender and icy-blue clothing, pink accents, bright star sparkles, cute sticker-like decorations, warm peach outline around the figures, layered character composition and clean printed key-art quality. Preserve the reference's exact three-part character presentation: (1) a large close-up portrait of the person, (2) a larger full-body fashion pose of the same person, and (3) a small cute mini/chibi full-body version of that same person near the bottom. All three must be visible in one finished composition, clearly related to the same source person, with the mini version retained as a deliberate reference-like inset rather than removed or replaced. Do not substitute another anime aesthetic, generic manga style, semi-realistic anime, 3D anime, watercolor, chibi-only, cartoon, or photorealism. The output must look like it belongs to the same illustrated series as Reference Image 2. Preserve every foreground person's exact identity, facial proportions, age, skin tone, expression and recognizable features; stylize the rendering while keeping the person's real face recognizable and unchanged. Keep the same number of source people and do not invent additional identities. Do not add text, logos or watermarks.", reference="anime-style.png"),
    style("gta", "GTA", "Игровой постер в духе GTA", "#f2964a", "Match Reference Image 2 as closely as possible in visual treatment: unmistakably illustrated GTA-like loading-screen key art with prominent dark contour lines, angular facial planes, bold hard-edged cel shading, flat painted color regions, sharp highlights and a crisp graphic finish. Make the outlines clearly visible at print size. Use a saturated peach-pink-purple sunset, palm silhouettes, a coastal modern-city atmosphere, dramatic waist-up hero composition and fashionable contemporary clothing. The output must look drawn from edge to edge, never photorealistic and never like a simple photo filter. Keep the mood stylish and cinematic, without violence, guns, logos, game titles or text.", reference="gta-style.png"),
    style("cyberpunk", "Киберпанк", "Неон и технологии", "#8b5cf6", "Create an Arctic cyberpunk portrait at night with frosted neon, holographic interfaces and a futuristic Yakutsk skyline. Preserve exact identity."),
    style("postcard-soviet", "Открытка НГ · советская", "Новогодняя ретро-открытка", "#cf4f4f", "Use the New Year postcard reference as the strict style target: rich deep-red festive background, falling snow, warm editorial holiday lighting, red-and-green gift wrapping, elegant winter clothing and soft vintage print texture. Adapt the clothing and styling naturally for the person's gender: for a man use a masculine red winter suit or coat, and for a woman use a feminine festive suit or dress. Preserve exact identity. Do not copy the reference woman's face, text, watermark or exact pose; do not add any text.", strips=False, reference="new-year-postcard.png"),
    style("postcard-ca", "Открытка НГ · ЦА", "Новогодняя открытка", "#5f9ea0", "Use the New Year postcard reference as the strict style target: rich deep-red festive background, falling snow, warm editorial holiday lighting, red-and-green gift wrapping, elegant winter clothing and soft vintage print texture. Adapt the clothing and styling naturally for the person's gender: for a man use a masculine red winter suit or coat, and for a woman use a feminine festive suit or dress. Preserve exact identity. Do not copy the reference woman's face, text, watermark or exact pose; do not add any text.", strips=False, reference="new-year-postcard.png"),
]


def get_style(style_id: str) -> Style | None:
    return next((style for style in STYLES if style.id == style_id), None)
