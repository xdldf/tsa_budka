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
    style("costume-male-north", "Якутский костюм · мужской северный", "Суровый северный образ", "#506986", "Use only the clothing from the outfit reference. Create an authentic ceremonial northern Sakha men's portrait with a realistic Yakutian landscape.", category="culture", backgrounds=["yakutia-lenskie-stolby.jpg"], outfits={"male": ["yakut_male_2.jpg"]}),
    style("costume-male-botur", "Якутский костюм · Ботур", "Образ якутского богатыря", "#a65c39", "Use the outfit reference as the exact foundation and transform the foreground person into a noble Sakha Botur warrior. Preserve exact identity; make it heroic, realistic and respectful.", category="culture", backgrounds=["yakutia-lenskie-stolby-summer.jpg"], outfits={"male": ["yakut_male_1.jpg", "yakut_male_2.jpg"]}),
    style("costume-female-summer", "Якутский костюм · женский летний", "Лёгкий традиционный образ", "#e08fa8", "Use only the clothing from the outfit reference. Dress every foreground person in this authentic Sakha women's summer costume and place them beside the Lena Pillars.", category="culture", backgrounds=["yakutia-lenskie-stolby-summer.jpg"], outfits={"female": ["yakut_female_1.jpg"]}),
    style("costume-female-winter", "Якутский костюм · женский зимний", "Тёплый зимний образ", "#b9d8ec", "Use only the clothing from the outfit reference. Dress every foreground person in this warm authentic Sakha women's winter costume in winter Yakutia.", category="culture", backgrounds=["yakutia-lenskie-stolby.jpg"], outfits={"female": ["yakut_female_2.jpg"]}),
    style("costume-female-north", "Якутский костюм · женский северный", "Северная церемония", "#7b93b1", "Use only the clothing from the outfit reference. Create an authentic ceremonial northern Sakha women's portrait with a calm northern atmosphere.", category="culture", backgrounds=["yakutia-lenskie-stolby.jpg"], outfits={"female": ["yakut_female_3.jpg"]}),
    style("costume-female-jewelry", "Якутский костюм · украшения", "Традиционные серебряные украшения", "#c7c9d6", "Use the outfit reference as the exact foundation and emphasize its authentic Sakha silver jewelry. Preserve exact identity and natural face.", category="culture", backgrounds=["yakutia-lenskie-stolby-summer.jpg"], outfits={"female": ["yakut_female_1.jpg", "yakut_female_2.jpg", "yakut_female_3.jpg"]}),
    style("lena-pillars-winter", "Ленские столбы · зима", "Зимняя Якутия", "#8cb8db", "The location is the Lena Pillars in winter Yakutia. Every foreground person wears the exact warm winter jacket from the merchandise reference.", category="travel", backgrounds=["yakutia-lenskie-stolby.jpg"], merch="merch_yakutia.jpg"),
    style("fashion", "Мода", "Современная fashion-съёмка", "#d99b8f", "Create a high-fashion editorial portrait with bold contemporary styling, studio lighting and premium magazine photography. Preserve exact identity."),
    style("frozen-face", "Замерзшее лицо", "Морозный арт-эффект", "#9ccfe1", "Create a photorealistic extreme-Yakutian-frost portrait with clearly visible delicate white frost crystals on the eyebrows, hair and especially along both the upper and lower eyelashes of both eyes. The eyelashes must look naturally coated with fine sparkling hoarfrost, with individual frosted lashes visible in sharp detail. Keep the eyes open, unobstructed and recognizable; do not alter their shape, color or expression. Add visible breath and cold icy light. Preserve exact identity and keep the face natural."),
    style("anime", "Аниме", "Яркий аниме-портрет", "#ef7ca6", "Create a strongly stylized polished anime fashion illustration based on the style reference. Copy the reference's visual language closely: expressive large anime eyes, clean confident ink contours, soft cel-shaded color planes, warm brown and honey hair highlights, pastel lavender and light-blue clothing, pink accents, sparkles and cute sticker-like decorative stars, with a subtle warm outline around the character. Make it look like finished premium manga key art, playful and fashionable, with crisp line work visible at print size. Preserve every foreground person's exact identity, facial proportions, age, skin tone, expression and recognizable features; do not replace the face with a generic anime face. Keep the same number of people and poses. Do not add text, logos, watermarks or extra people.", reference="anime-style.png"),
    style("gta", "GTA", "Игровой постер в духе GTA", "#f2964a", "Match Reference Image 2 as closely as possible in visual treatment: unmistakably illustrated GTA-like loading-screen key art with prominent dark contour lines, angular facial planes, bold hard-edged cel shading, flat painted color regions, sharp highlights and a crisp graphic finish. Make the outlines clearly visible at print size. Use a saturated peach-pink-purple sunset, palm silhouettes, a coastal modern-city atmosphere, dramatic waist-up hero composition and fashionable contemporary clothing. The output must look drawn from edge to edge, never photorealistic and never like a simple photo filter. Keep the mood stylish and cinematic, without violence, guns, logos, game titles or text.", reference="gta-style.png"),
    style("cyberpunk", "Киберпанк", "Неон и технологии", "#8b5cf6", "Create an Arctic cyberpunk portrait at night with frosted neon, holographic interfaces and a futuristic Yakutsk skyline. Preserve exact identity."),
    style("postcard-soviet", "Открытка НГ · советская", "Новогодняя ретро-открытка", "#cf4f4f", "Create a warm Soviet-era New Year postcard portrait with nostalgic illustration style, fir branches, snow and festive atmosphere. Preserve the person. No text.", strips=False),
    style("postcard-ca", "Открытка НГ · ЦА", "Новогодняя открытка", "#5f9ea0", "Create a premium festive New Year postcard portrait with winter magic, elegant holiday decor and a warm celebratory mood. Preserve the person. No text.", strips=False),
]


def get_style(style_id: str) -> Style | None:
    return next((style for style in STYLES if style.id == style_id), None)
