from app.models import Style


STYLES: list[Style] = [
    Style(id="digital-diamond", name="Цифровой алмаз", description="Кристаллы, свет и цифровая Якутия", preview_color="#22d3ee", category="theme", prompt_template="Transform the scene into a futuristic Digital Diamond forum portrait: luminous faceted diamond crystals, icy cyan and violet light, subtle data particles, premium technology-conference atmosphere, elegant black and silver fashion. Keep it sophisticated and photorealistic."),
    Style(id="yakutia-lena-pillars", name="Якутия — Ленские столбы", description="Легендарный пейзаж в современном стиле", preview_color="#f59e0b", category="theme", background_images=["yakutia-lenskie-stolby.jpg"], prompt_template="Place the people at the Lena Pillars in Yakutia above the Lena river, in dramatic golden-hour light. Add subtle Sakha-inspired geometric details to modern winter clothing. The result is a premium contemporary Yakutia travel portrait, not a postcard and without text."),
    Style(id="sakha-anime", name="Sakha Anime", description="Герой аниме из будущего Якутии", preview_color="#fb7185", category="theme", prompt_template="Render the people as high-end anime protagonists while preserving exact identity and recognizable facial structure. Set the scene in a futuristic winter Yakutsk with aurora light, crisp cel shading, expressive but non-chibi proportions, elegant Sakha ornament accents and cinematic anime key art quality."),
    Style(id="arctic-cyberpunk", name="Арктический киберпанк", description="Неон, мороз и технологии", preview_color="#8b5cf6", category="theme", prompt_template="Create an Arctic cyberpunk portrait at night: frosted neon, holographic interfaces, warm technical outerwear, icy breath and a futuristic Yakutsk skyline. Preserve faces photorealistically, use cyan-magenta lighting, premium cinematic detail and no text."),
    Style(id="pixel-yakutsk", name="Pixel Yakutsk", description="Будто вы внутри игры", preview_color="#34d399", category="theme", prompt_template="Turn the environment and clothing into a playful premium 16-bit video-game world inspired by winter Yakutsk, while keeping each face clearly recognizable as a polished pixel-art portrait. Use crisp pixels, bright arcade colors, snowy city details and dynamic game-character posing, without UI or text."),
    Style(id="mammoth-party", name="Мамонт на тусовке", description="Смешной кадр с якутским мамонтом", preview_color="#f97316", category="theme", prompt_template="Create a funny but polished party portrait in Yakutia with one friendly fluffy woolly mammoth joining the group like a celebrity guest. Preserve every real person's identity and count. Use joyful expressions, warm festival lights, tasteful winter fashion, realistic photography and playful energy without text."),
]


def get_style(style_id: str) -> Style | None:
    return next((style for style in STYLES if style.id == style_id), None)
