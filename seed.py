"""
Run once to populate the database with sample ads and an initial admin user.
Usage:
    python seed.py
"""
from app import create_app, db
from app.models import Ad, AdTranslation, User

SAMPLE_ADS = [
    {
        "slug": "beto-elena-america-tv-2023",
        "brand": "América TV",
        "country": "Perú",
        "year": 2023,
        "category": "Entretenimiento",
        "youtube_id": "dQw4w9WgXcQ",   # reemplaza con el ID real del spot
        "translations": {
            "es": {
                "title": "Beto y Elena: la pareja que vende como ninguna",
                "analysis_text": (
                    "<p>América TV lleva años apostando por el duo cómico de Beto Ortiz y Elena "
                    "Kross como imagen de su parrilla de programas. Lo que hace funcionar este "
                    "spot no es la creatividad del concepto —que es bastante convencional— sino "
                    "la <em>energía de contrastes</em> entre ambos personajes: él irónico y "
                    "distante, ella desbordante y física.</p>"
                    "<p>El casting hace el trabajo que el guion no siempre alcanza a hacer. "
                    "Cuando la química entre dos personas es real, el espectador lo siente antes "
                    "de procesar el mensaje. América TV lo sabe y lo explota con eficiencia."
                    "</p>"
                    "<p>El riesgo de esta estrategia: la marca queda atada a la imagen de dos "
                    "personas públicas cuya reputación puede cambiar. Es una apuesta de alto "
                    "rendimiento pero también de alta exposición.</p>"
                ),
            },
            "en": {
                "title": "Beto & Elena: The Comedy Duo That Sells",
                "analysis_text": (
                    "<p>América TV has been betting for years on the comic duo of Beto Ortiz "
                    "and Elena Kross as the face of their programming lineup. What makes this "
                    "spot work isn't the creativity of the concept — which is fairly conventional "
                    "— but the <em>energy of contrasts</em> between both characters: him ironic "
                    "and detached, her exuberant and physical.</p>"
                    "<p>Casting does the job that the script doesn't always manage. When the "
                    "chemistry between two people is real, the viewer feels it before processing "
                    "the message. América TV knows this and exploits it efficiently.</p>"
                    "<p>The risk with this strategy: the brand becomes tied to the image of two "
                    "public figures whose reputation can change. It's a high-yield bet, but also "
                    "high-exposure.</p>"
                ),
            },
        },
    },
    {
        "slug": "gap-vs-american-eagle-2023",
        "brand": "Gap",
        "country": "EE.UU.",
        "year": 2023,
        "category": "Moda",
        "youtube_id": "dQw4w9WgXcQ",   # reemplaza con el ID real del spot
        "translations": {
            "es": {
                "title": "Gap responde a American Eagle: cuando el rival te da el guion",
                "analysis_text": (
                    "<p>En publicidad, la táctica de responder directamente a un competidor es "
                    "de altísimo riesgo: si lo haces mal, amplias el mensaje del rival. Gap lo "
                    "hizo bien. Cuando American Eagle lanzó su campaña posicionándose como la "
                    "alternativa cool al denim 'anticuado', Gap no ignoró el ataque —lo absorbió "
                    "y lo convirtió en combustible.</p>"
                    "<p>El spot de respuesta de Gap funciona porque no defiende: <em>reencuadra</em>. "
                    "En vez de argumentar que su denim no es anticuado, Gap abraza la idea de "
                    "permanencia como virtud. 'Llevamos aquí décadas porque algo estamos haciendo "
                    "bien' es una respuesta más fuerte que 'nosotros también somos cool'.</p>"
                    "<p>Lección para los creativos: cuando el competidor te ataca, la respuesta "
                    "más débil es la defensa. La más fuerte es cambiar el terreno del debate.</p>"
                ),
            },
            "en": {
                "title": "Gap Fires Back at American Eagle: When Your Rival Writes Your Script",
                "analysis_text": (
                    "<p>In advertising, directly responding to a competitor is an extremely "
                    "high-risk tactic: if you do it wrong, you amplify your rival's message. "
                    "Gap did it right. When American Eagle launched its campaign positioning "
                    "itself as the cool alternative to 'outdated' denim, Gap didn't ignore the "
                    "attack — it absorbed it and turned it into fuel.</p>"
                    "<p>Gap's response spot works because it doesn't defend: it <em>reframes</em>. "
                    "Instead of arguing that their denim isn't outdated, Gap embraces the idea "
                    "of permanence as a virtue. 'We've been here for decades because we must be "
                    "doing something right' is a far stronger answer than 'we're cool too'.</p>"
                    "<p>Lesson for creatives: when a competitor attacks, defense is the weakest "
                    "response. The strongest move is to change the ground of the debate.</p>"
                ),
            },
        },
    },
    {
        "slug": "inca-kola-creatividad-peruana-2022",
        "brand": "Inca Kola",
        "country": "Perú",
        "year": 2022,
        "category": "Bebidas",
        "youtube_id": "dQw4w9WgXcQ",   # reemplaza con el ID real del spot
        "translations": {
            "es": {
                "title": "Inca Kola y el orgullo peruano: el truco más viejo que sigue funcionando",
                "analysis_text": (
                    "<p>Pocas marcas en el mundo han construido una identidad tan sólida sobre "
                    "el nacionalismo como Inca Kola. Desde los años 80, la fórmula es casi "
                    "idéntica: peruanidad, creatividad, orgullo. Este spot de 2022 no rompe esa "
                    "tradición —y esa es exactamente la decisión correcta.</p>"
                    "<p>Cuando una marca ha construido un territorio emocional durante décadas, "
                    "innovar por innovar es un error. La consistencia <em>es</em> la estrategia. "
                    "Lo que Inca Kola hace bien aquí es actualizar el tono sin traicionar el "
                    "territorio: las referencias culturales son contemporáneas, pero la promesa "
                    "emocional es la misma de siempre.</p>"
                    "<p>El peligro de este enfoque a largo plazo: la marca puede volverse "
                    "predecible. El antídoto es exactamente lo que hace este spot: usar "
                    "ejecuciones frescas para sostener un mensaje atemporal.</p>"
                ),
            },
            "en": {
                "title": "Inca Kola and Peruvian Pride: The Oldest Trick That Still Works",
                "analysis_text": (
                    "<p>Few brands in the world have built such a solid identity around "
                    "nationalism as Inca Kola. Since the 1980s, the formula has been almost "
                    "identical: Peruvianness, creativity, pride. This 2022 spot doesn't break "
                    "that tradition — and that's exactly the right call.</p>"
                    "<p>When a brand has built an emotional territory over decades, innovating "
                    "for the sake of it is a mistake. Consistency <em>is</em> the strategy. "
                    "What Inca Kola does well here is updating the tone without betraying the "
                    "territory: the cultural references are contemporary, but the emotional "
                    "promise is the same as always.</p>"
                    "<p>The long-term risk of this approach: the brand can become predictable. "
                    "The antidote is exactly what this spot does: using fresh executions to "
                    "sustain a timeless message.</p>"
                ),
            },
        },
    },
    {
        "slug": "apple-shot-on-iphone-2024",
        "brand": "Apple",
        "country": "EE.UU.",
        "year": 2024,
        "category": "Tecnología",
        "youtube_id": "dQw4w9WgXcQ",   # reemplaza con el ID real del spot
        "translations": {
            "es": {
                "title": "Shot on iPhone: el brief más elegante de la última década",
                "analysis_text": (
                    "<p>'Shot on iPhone' es un caso de estudio en cómo convertir una "
                    "característica técnica en un movimiento cultural. La mayoría de las marcas "
                    "de tecnología habla <em>sobre</em> sus productos. Apple decidió hablar "
                    "<em>con</em> sus productos —literalmente.</p>"
                    "<p>El insight es brillante en su simplicidad: si la cámara es tan buena, "
                    "que sean los usuarios quienes lo demuestren. El resultado es publicidad "
                    "que no parece publicidad, creada por personas reales con historias reales, "
                    "donde el producto es el medio, no el mensaje.</p>"
                    "<p>La ejecución de 2024 mantiene esa esencia pero incorpora formatos "
                    "verticales nativos de redes sociales, lo que demuestra que Apple entiende "
                    "que el canal es parte del mensaje. Un brief que se ha mantenido relevante "
                    "por casi diez años merece estudio.</p>"
                ),
            },
            "en": {
                "title": "Shot on iPhone: The Most Elegant Brief of the Last Decade",
                "analysis_text": (
                    "<p>'Shot on iPhone' is a case study in how to turn a technical feature "
                    "into a cultural movement. Most tech brands talk <em>about</em> their "
                    "products. Apple decided to talk <em>with</em> their products — literally.</p>"
                    "<p>The insight is brilliant in its simplicity: if the camera is that good, "
                    "let users prove it. The result is advertising that doesn't feel like "
                    "advertising, created by real people with real stories, where the product "
                    "is the medium, not the message.</p>"
                    "<p>The 2024 execution maintains that essence while incorporating native "
                    "vertical formats for social media, showing Apple understands that the "
                    "channel is part of the message. A brief that has stayed relevant for "
                    "almost ten years deserves careful study.</p>"
                ),
            },
        },
    },
]


def seed():
    app = create_app()
    with app.app_context():
        db.create_all()

        # --- Initial admin user ---
        ADMIN_EMAIL = "admin@adcritic.com"
        ADMIN_PASSWORD = "cambia-esta-clave-ahora"
        if not User.query.filter_by(email=ADMIN_EMAIL).first():
            admin = User(email=ADMIN_EMAIL, role="admin")
            admin.set_password(ADMIN_PASSWORD)
            db.session.add(admin)
            db.session.commit()
            print(f"  admin created: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
            print("  *** Cambia la contraseña desde el panel lo antes posible ***")
        else:
            print(f"  skip (already exists): {ADMIN_EMAIL}")
        for data in SAMPLE_ADS:
            if Ad.query.filter_by(slug=data["slug"]).first():
                print(f"  skip (already exists): {data['slug']}")
                continue
            ad = Ad(
                slug=data["slug"],
                brand=data["brand"],
                country=data["country"],
                year=data["year"],
                category=data["category"],
                youtube_id=data["youtube_id"],
            )
            db.session.add(ad)
            db.session.flush()
            for lang, td in data["translations"].items():
                db.session.add(AdTranslation(
                    ad_id=ad.id,
                    language=lang,
                    title=td["title"],
                    analysis_text=td["analysis_text"],
                ))
            print(f"  added: {data['slug']}")
        db.session.commit()
        print("Seed complete.")


if __name__ == "__main__":
    seed()
