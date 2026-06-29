"""Seed real-world advertising news with editorial voice."""
from datetime import datetime, timedelta

from app import create_app, db
from app.models import Post, PostCategory, PostTranslation, User


app = create_app()


def upsert_category(name_es, name_en):
    cat = PostCategory.query.filter_by(name_es=name_es).first()
    if not cat:
        cat = PostCategory(name_es=name_es, name_en=name_en)
        db.session.add(cat)
        db.session.flush()
    else:
        cat.name_en = name_en
    return cat


def upsert_translation(post, lang, data):
    t = post.translation(lang)
    if not t:
        t = PostTranslation(post_id=post.id, language=lang)
        db.session.add(t)
    t.title = data["title"]
    t.excerpt = data["excerpt"]
    t.body = data["body"]
    t.meta_title = data.get("meta_title")
    t.meta_description = data.get("meta_description")


def source_list(items, lang):
    title = "Fuentes" if lang == "es" else "Sources"
    links = "".join(f'<li><a href="{url}" target="_blank" rel="noopener">{label}</a></li>' for label, url in items)
    return f"<h2>{title}</h2><ul>{links}</ul>"


with app.app_context():
    admin = User.query.filter_by(role="admin").first()
    if not admin:
        raise RuntimeError("No admin user found. Run seed.py first.")

    cats = {
        "Industria": upsert_category("Industria", "Industry"),
        "Análisis": upsert_category("Análisis", "Analysis"),
        "Opinión": upsert_category("Opinión", "Opinion"),
        "Tendencias": upsert_category("Tendencias", "Trends"),
        "Mundial": upsert_category("Mundial", "World Cup"),
        "Cannes": upsert_category("Cannes", "Cannes"),
        "LatAm": upsert_category("LatAm", "LatAm"),
    }

    now = datetime.utcnow()
    posts = [
        {
            "slug": "adidas-backyard-legends-mundial-2026",
            "published_at": now - timedelta(hours=8),
            "is_premium": False,
            "categories": ["Mundial", "Tendencias", "Análisis"],
            "cover_image_url": "https://i.ytimg.com/vi/wSj8ha07LjI/hqdefault.jpg",
            "youtube_id": "wSj8ha07LjI",
            "video_source_type": "youtube",
            "video_source_value": "wSj8ha07LjI",
            "sources": [
                ("Adidas — Backyard Legends", "https://www.youtube.com/watch?v=wSj8ha07LjI"),
                ("FIFA World Cup 26", "https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026"),
            ],
            "es": {
                "title": "Adidas convierte el Mundial 2026 en patio de barrio: por qué 'Backyard Legends' funciona",
                "excerpt": "Messi, Beckham y un casting imposible no son el punto. El punto es que Adidas volvió a vender fútbol como memoria compartida.",
                "body": "",
            },
            "en": {
                "title": "Adidas turns World Cup 2026 into a backyard myth: why 'Backyard Legends' works",
                "excerpt": "Messi, Beckham and an impossible cast are not the real point. Adidas is selling football as shared memory again.",
                "body": "",
            },
        },
        {
            "slug": "coca-cola-uncanned-emotions-mundial-2026",
            "published_at": now - timedelta(days=1, hours=3),
            "is_premium": False,
            "categories": ["Mundial", "Análisis"],
            "cover_image_url": "https://i.ytimg.com/vi/rTQUWIgalUs/hqdefault.jpg",
            "youtube_id": "rTQUWIgalUs",
            "video_source_type": "youtube",
            "video_source_value": "rTQUWIgalUs",
            "sources": [
                ("Coca-Cola — Uncanned Emotions", "https://www.youtube.com/watch?v=rTQUWIgalUs"),
                ("FIFA World Cup 26", "https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026"),
            ],
            "es": {
                "title": "Coca-Cola y el Mundial: emociones enlatadas, pero con oficio",
                "excerpt": "La marca vuelve al territorio que mejor domina: vender celebración antes que producto. La pregunta es si todavía sorprende.",
                "body": "",
            },
            "en": {
                "title": "Coca-Cola and the World Cup: canned emotion, professionally uncanned",
                "excerpt": "The brand returns to the territory it knows best: selling celebration before product. The question is whether it still surprises.",
                "body": "",
            },
        },
        {
            "slug": "mundial-2026-batalla-sponsors",
            "published_at": now - timedelta(days=2),
            "is_premium": False,
            "categories": ["Mundial", "Industria"],
            "cover_image_url": "https://images.unsplash.com/photo-1522778119026-d647f0596c20?auto=format&fit=crop&w=1400&q=80",
            "sources": [
                ("FIFA World Cup 26", "https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026"),
                ("FIFA commercial partners", "https://inside.fifa.com/organisation/commercial/partners"),
            ],
            "es": {
                "title": "La guerra invisible del Mundial 2026: el negocio no está solo dentro del estadio",
                "excerpt": "FIFA vende el torneo; las marcas venden pertenencia. Entre sponsor oficial, activación local y oportunismo elegante está la verdadera batalla.",
                "body": "",
            },
            "en": {
                "title": "The invisible war of World Cup 2026: the business is not only inside the stadium",
                "excerpt": "FIFA sells the tournament; brands sell belonging. The real fight lives between official sponsorship, local activation and elegant opportunism.",
                "body": "",
            },
        },
        {
            "slug": "cannes-2026-ia-no-es-idea",
            "published_at": now - timedelta(days=3, hours=4),
            "is_premium": True,
            "categories": ["Cannes", "Opinión", "Tendencias"],
            "cover_image_url": "https://images.unsplash.com/photo-1519671482749-fd09be7ccebf?auto=format&fit=crop&w=1400&q=80",
            "sources": [
                ("Cannes Lions", "https://www.canneslions.com/"),
                ("Cannes Lions awards", "https://www.canneslions.com/awards"),
            ],
            "es": {
                "title": "Cannes 2026 y la IA: producir más no es pensar mejor",
                "excerpt": "La industria ya aprendió a generar piezas con IA. La pregunta adulta es otra: quién tiene una idea que valga la pena automatizar.",
                "body": "",
            },
            "en": {
                "title": "Cannes 2026 and AI: producing more is not thinking better",
                "excerpt": "The industry has learned to generate assets with AI. The adult question is different: who has an idea worth automating?",
                "body": "",
            },
        },
        {
            "slug": "creadores-cannes-2026",
            "published_at": now - timedelta(days=4, hours=2),
            "is_premium": False,
            "categories": ["Cannes", "Tendencias"],
            "cover_image_url": "https://images.unsplash.com/photo-1556761175-b413da4baf72?auto=format&fit=crop&w=1400&q=80",
            "sources": [
                ("Cannes Lions", "https://www.canneslions.com/"),
                ("Cannes Lions awards", "https://www.canneslions.com/awards"),
            ],
            "es": {
                "title": "Los creadores ya no son invitados a Cannes: son el medio",
                "excerpt": "Las marcas quieren cultura, pero la cultura ya no vive solo en agencias. Vive en gente con audiencia, criterio y velocidad.",
                "body": "",
            },
            "en": {
                "title": "Creators are no longer guests at Cannes: they are the media",
                "excerpt": "Brands want culture, but culture no longer lives only inside agencies. It lives in people with audience, taste and speed.",
                "body": "",
            },
        },
        {
            "slug": "latam-mundial-2026-marcas",
            "published_at": now - timedelta(days=5),
            "is_premium": False,
            "categories": ["LatAm", "Mundial", "Industria"],
            "cover_image_url": "https://images.unsplash.com/photo-1518105779142-d975f22f1b0a?auto=format&fit=crop&w=1400&q=80",
            "sources": [
                ("FIFA World Cup 26", "https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026"),
                ("FIFA commercial partners", "https://inside.fifa.com/organisation/commercial/partners"),
            ],
            "es": {
                "title": "LatAm ante el Mundial 2026: menos spot épico, más calle",
                "excerpt": "México será sede, Sudamérica mirará con hambre y las marcas regionales tendrán que escoger: postal patriótica o activación viva.",
                "body": "",
            },
            "en": {
                "title": "LatAm and World Cup 2026: less epic spot, more street",
                "excerpt": "Mexico will host, South America will watch hungrily, and regional brands must choose: patriotic postcard or living activation.",
                "body": "",
            },
        },
    ]

    bodies = {
        "adidas-backyard-legends-mundial-2026": {
            "es": [
                "<p>El Mundial 2026 todavía no empezó y Adidas ya hizo algo que muchas marcas olvidan: no trató al fútbol como un calendario de medios, sino como una máquina de recuerdos.</p>",
                "<p><em>Backyard Legends</em> junta nombres enormes y los pone al servicio de una imagen simple: el juego empieza en cualquier patio. Esa decisión es más importante que el casting. En vez de vender grandeza desde un pedestal, la baja al lugar donde el fan la puede tocar.</p>",
                "<p>La campaña entiende que el fútbol global se gana con una paradoja: cuanto más masivo se vuelve, más necesita sentirse íntimo. Ese es el lujo de Adidas aquí. No grita performance. Susurra pertenencia.</p>",
                "<h2>La lectura crítica</h2>",
                "<p>El riesgo está en la nostalgia fácil. Pero cuando una marca deportiva usa leyendas para activar memoria y no solo autoridad, el resultado tiene músculo cultural. El Mundial será una guerra de sponsors; Adidas está intentando ganar antes del pitazo inicial.</p>",
            ],
            "en": [
                "<p>World Cup 2026 has not started yet, and Adidas has already remembered what many brands forget: football is not a media calendar, it is a memory machine.</p>",
                "<p><em>Backyard Legends</em> gathers enormous names and puts them in service of a simple image: the game starts in any backyard. That choice matters more than the cast. Instead of selling greatness from a pedestal, it brings it down to where fans can touch it.</p>",
                "<p>The campaign understands a global football paradox: the bigger the game becomes, the more intimate it needs to feel. That is the luxury in this Adidas move. It does not shout performance. It whispers belonging.</p>",
                "<h2>The critique</h2>",
                "<p>The danger is easy nostalgia. But when a sports brand uses legends to activate memory rather than mere authority, the work gains cultural muscle. The World Cup will be a sponsor war; Adidas is trying to win before kickoff.</p>",
            ],
        },
        "coca-cola-uncanned-emotions-mundial-2026": {
            "es": [
                "<p>Coca-Cola no necesita explicar su relación con el fútbol. Tiene décadas vendiendo algo más rentable que bebida: el permiso social para celebrar juntos.</p>",
                "<p><em>Uncanned Emotions</em> vuelve a ese territorio. La lata no es envase, es detonador emocional. La marca sabe que en Mundial nadie compra solo sabor; compra grito, abrazo, superstición y una pequeña fantasía de unidad.</p>",
                "<p>La pregunta interesante no es si la campaña es coherente. Lo es. La pregunta es si Coca-Cola todavía puede sorprender dentro de un territorio que domina tanto que ya parece automático.</p>",
                "<h2>La lectura crítica</h2>",
                "<p>Funciona porque es oficio puro: ritmo, escala, humanidad y un insight universal. Pero su mayor virtud también es su límite. Coca-Cola es tan buena en felicidad colectiva que cada nueva campaña pelea contra su propia historia.</p>",
            ],
            "en": [
                "<p>Coca-Cola does not need to explain its relationship with football. For decades it has sold something more profitable than soda: social permission to celebrate together.</p>",
                "<p><em>Uncanned Emotions</em> returns to that territory. The can is not packaging, it is an emotional trigger. The brand knows that during a World Cup nobody buys only taste; they buy screaming, hugging, superstition and a small fantasy of unity.</p>",
                "<p>The interesting question is not whether the campaign is coherent. It is. The question is whether Coca-Cola can still surprise inside a territory it owns so completely that it can feel automatic.</p>",
                "<h2>The critique</h2>",
                "<p>It works because it is pure craft: rhythm, scale, humanity and a universal insight. But its greatest virtue is also its ceiling. Coca-Cola is so good at collective happiness that every new campaign competes with its own history.</p>",
            ],
        },
        "mundial-2026-batalla-sponsors": {
            "es": [
                "<p>El Mundial 2026 será el torneo de tres países, 16 ciudades y una ansiedad enorme por capturar atención antes, durante y después de cada partido. Para publicidad, eso significa una cosa: el estadio es apenas el principio.</p>",
                "<p>La diferencia entre sponsor oficial y marca oportunista será más visible que nunca. FIFA controla derechos, símbolos y acceso. Pero las marcas que no están en la foto oficial intentarán ganar en barrios, bares, delivery, creadores, memes y experiencias alrededor del partido.</p>",
                "<p>Ahí está la tensión: el sponsor compra legitimidad; el outsider necesita ingenio. En un Mundial extendido por Norteamérica, la creatividad local puede ser tan poderosa como el logo en la valla.</p>",
                "<h2>La lectura crítica</h2>",
                "<p>Las campañas más interesantes no serán necesariamente las más caras. Serán las que entiendan que el fútbol no sucede solo en el campo. Sucede en la previa, en la mesa, en el grupo de WhatsApp y en la calle.</p>",
            ],
            "en": [
                "<p>World Cup 2026 will be a tournament across three countries, 16 cities and a massive anxiety to capture attention before, during and after every match. For advertising, that means one thing: the stadium is only the beginning.</p>",
                "<p>The difference between official sponsor and opportunistic brand will be more visible than ever. FIFA controls rights, symbols and access. But brands outside the official photo will try to win in neighborhoods, bars, delivery, creators, memes and experiences around the match.</p>",
                "<p>That is the tension: the sponsor buys legitimacy; the outsider needs ingenuity. In a World Cup spread across North America, local creativity can become as powerful as the logo on the board.</p>",
                "<h2>The critique</h2>",
                "<p>The most interesting campaigns will not necessarily be the most expensive. They will be the ones that understand football does not only happen on the pitch. It happens in the pregame, at the table, in the group chat and on the street.</p>",
            ],
        },
        "cannes-2026-ia-no-es-idea": {
            "es": [
                "<p>Cannes 2026 llega después de años de ansiedad artificial: prompts, automatización, producción infinita y la fantasía de que una marca puede crear cultura con solo apretar un botón.</p>",
                "<p>Pero la conversación verdaderamente adulta ya no es si la IA produce. Produce. La pregunta es si produce algo que alguien necesite recordar. La diferencia entre asset y idea vuelve a ponerse brutalmente clara.</p>",
                "<p>La IA puede multiplicar versiones, acelerar adaptaciones y limpiar procesos. Pero una campaña no gana lugar en la cabeza de nadie por cantidad. Gana por punto de vista.</p>",
                "<h2>La lectura crítica</h2>",
                "<p>La industria no necesita menos IA. Necesita menos obediencia. Las marcas que usen tecnología para amplificar criterio humano van a avanzar; las que la usen para evitar criterio van a llenar internet de contenido correcto y muerto.</p>",
            ],
            "en": [
                "<p>Cannes 2026 arrives after years of artificial anxiety: prompts, automation, infinite production and the fantasy that a brand can create culture by pressing a button.</p>",
                "<p>But the adult conversation is no longer whether AI can produce. It can. The question is whether it produces anything someone needs to remember. The difference between asset and idea becomes brutally clear again.</p>",
                "<p>AI can multiply versions, accelerate adaptations and clean up processes. But a campaign does not earn space in anyone's head through quantity. It earns it through point of view.</p>",
                "<h2>The critique</h2>",
                "<p>The industry does not need less AI. It needs less obedience. Brands that use technology to amplify human judgment will move forward; those that use it to avoid judgment will fill the internet with correct, dead content.</p>",
            ],
        },
        "creadores-cannes-2026": {
            "es": [
                "<p>Durante años las agencias invitaron creadores para parecer contemporáneas. Ahora el gesto se invirtió: son las marcas y agencias las que quieren entrar al lenguaje de los creadores.</p>",
                "<p>La razón es simple y algo incómoda: muchos creadores entienden atención mejor que los departamentos que la compran. Saben ritmo, comentario, comunidad y riesgo. No siempre saben marca. Pero saben vida.</p>",
                "<p>El reto para la publicidad no es contratar influencers como cartelera humana. Es aprender a trabajar con personas que ya tienen una relación editorial con su audiencia.</p>",
                "<h2>La lectura crítica</h2>",
                "<p>El creador no reemplaza a la estrategia. La obliga a ser menos solemne. Cuando una marca colabora bien, no compra alcance: alquila confianza. Y la confianza, a diferencia del reach, se rompe rápido.</p>",
            ],
            "en": [
                "<p>For years, agencies invited creators to look contemporary. Now the gesture has reversed: brands and agencies want to enter the language of creators.</p>",
                "<p>The reason is simple and slightly uncomfortable: many creators understand attention better than the departments that buy it. They know rhythm, commentary, community and risk. They do not always know brand. But they know life.</p>",
                "<p>The challenge for advertising is not hiring influencers as human billboards. It is learning to work with people who already have an editorial relationship with their audience.</p>",
                "<h2>The critique</h2>",
                "<p>The creator does not replace strategy. The creator forces strategy to be less solemn. When a brand collaborates well, it does not buy reach: it rents trust. And trust, unlike reach, breaks fast.</p>",
            ],
        },
        "latam-mundial-2026-marcas": {
            "es": [
                "<p>LatAm llega al Mundial 2026 con una ventaja que muchas multinacionales no tienen: entiende el fútbol como desorden emocional, no como propiedad intelectual ordenada.</p>",
                "<p>Con México como sede y Sudamérica mirando desde una mezcla de orgullo, distancia y hambre competitiva, las marcas regionales tienen dos caminos. El primero: hacer la postal patriótica de siempre. El segundo: salir a la calle y activar rituales reales.</p>",
                "<p>La oportunidad está en mercados, bodegas, cantinas, barberías, delivery, radio local, streamers y plazas. Ahí el Mundial se vuelve cultura. Ahí también se vuelve compra.</p>",
                "<h2>La lectura crítica</h2>",
                "<p>La marca latinoamericana que gane no será la que parezca más global. Será la que logre que el Mundial se sienta propio sin depender de una bandera gigante y un jingle con bombo.</p>",
            ],
            "en": [
                "<p>LatAm enters World Cup 2026 with an advantage many multinationals do not have: it understands football as emotional disorder, not as tidy intellectual property.</p>",
                "<p>With Mexico as a host and South America watching from a mix of pride, distance and competitive hunger, regional brands have two paths. First: the usual patriotic postcard. Second: go to the street and activate real rituals.</p>",
                "<p>The opportunity lives in markets, corner stores, cantinas, barbershops, delivery, local radio, streamers and plazas. That is where the World Cup becomes culture. That is also where it becomes purchase.</p>",
                "<h2>The critique</h2>",
                "<p>The Latin American brand that wins will not be the one that looks most global. It will be the one that makes the World Cup feel owned without leaning on a giant flag and a drum-heavy jingle.</p>",
            ],
        },
    }

    real_slugs = {post["slug"] for post in posts}
    for old in Post.query.filter(~Post.slug.in_(real_slugs)).all():
        if old.slug in {
            "marcas-peruanas-2024",
            "narrativa-emocional-vs-humor",
            "ia-en-produccion-publicitaria",
            "publicidad-exterior-regresa",
        }:
            old.status = "draft"

    for data in posts:
        post = Post.query.filter_by(slug=data["slug"]).first()
        if not post:
            post = Post(slug=data["slug"], author_id=admin.id)
            db.session.add(post)
            db.session.flush()

        post.author_id = admin.id
        post.cover_image_url = data["cover_image_url"]
        post.youtube_id = data.get("youtube_id")
        post.video_source_type = data.get("video_source_type")
        post.video_source_value = data.get("video_source_value")
        post.is_premium = data["is_premium"]
        post.published_at = data["published_at"]
        post.status = "published"
        post.categories = [cats[name] for name in data["categories"]]

        for lang in ("es", "en"):
            trans = data[lang].copy()
            paragraphs = bodies[data["slug"]][lang]
            trans["body"] = "".join(paragraphs) + source_list(data["sources"], lang)
            trans["meta_description"] = trans["excerpt"]
            upsert_translation(post, lang, trans)

        print(f"upserted {post.slug}")

    db.session.commit()
    print("real news seed done.")
