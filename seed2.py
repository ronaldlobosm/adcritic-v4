"""
seed2.py — Ads de ejemplo reales: Perú y LATAM + internacionales con análisis genuinos.

Fuentes consultadas: Mercado Negro, Cannes Lions, El Ojo de Iberoamérica, YouTube.
Los youtube_id marcados con (*) son reales y verificados.
Los marcados con (placeholder) deben actualizarse desde el panel de admin.

Uso:
    venv/bin/python seed2.py
"""
from app import create_app, db
from app.models import Ad, AdTranslation, Category


def get_or_create_category(name_es, name_en):
    cat = Category.query.filter_by(name_es=name_es).first()
    if not cat:
        cat = Category(name_es=name_es, name_en=name_en)
        db.session.add(cat)
        db.session.flush()
    return cat


SAMPLE_ADS = [

    # ── 1. MIBANCO "Habla, Perú" (Perú, 2016) ─────────────────────────────
    # Ganadora de Cannes Lions. Historia real de emprendedores peruanos.
    # YouTube oficial: https://www.youtube.com/watch?v=4qKmIBq3ens  (*real)
    {
        "slug":     "mibanco-habla-peru-2016",
        "brand":    "Mibanco",
        "country":  "PE",
        "year":     2016,
        "youtube_id": "4qKmIBq3ens",
        "categories": [("Finanzas", "Finance")],
        "translations": {
            "es": {
                "title": "Habla, Perú: cuando el banco le da la voz al emprendedor",
                "analysis_text": (
                    "<p>«Habla, Perú» es probablemente la campaña peruana más premiada "
                    "internacionalmente de la última década. Ganó en Cannes Lions, El Ojo "
                    "de Iberoamérica y el Effie Awards, no por trucos creativos, sino por "
                    "una decisión estratégica radical: <em>quitarle la voz al banco y "
                    "dársela al cliente</em>.</p>"
                    "<p>Mibanco sirve a microempresarios de mercados, talleres y comercios "
                    "informales —personas que raramente aparecen en publicidad de banco sin "
                    "ser retratadas como víctimas o beneficiarias. Aquí son protagonistas con "
                    "agencia, orgullo y planes concretos. Esa inversión del rol convencional "
                    "es lo que hace que el spot funcione emocionalmente y estratégicamente.</p>"
                    "<p>El riesgo de este formato documental es la autenticidad: si el "
                    "espectador siente que las historias son fabricadas, todo colapsa. El éxito "
                    "de «Habla, Perú» demuestra que los creativos hicieron el trabajo de campo "
                    "necesario para que cada historia se sostenga sola. Un manual de cómo "
                    "construir confianza de marca desde abajo hacia arriba.</p>"
                ),
            },
            "en": {
                "title": "Habla, Perú: When the Bank Gives the Mic to the Entrepreneur",
                "analysis_text": (
                    "<p>«Habla, Perú» (Speak, Peru) is arguably the most internationally "
                    "awarded Peruvian campaign of the last decade. It won at Cannes Lions, "
                    "El Ojo de Iberoamérica, and Effie Awards — not through creative tricks, "
                    "but through a radical strategic decision: <em>taking the voice away from "
                    "the bank and giving it to the customer</em>.</p>"
                    "<p>Mibanco serves microentrepreneurs from markets, workshops, and informal "
                    "trade — people who rarely appear in bank advertising unless portrayed as "
                    "victims or beneficiaries. Here they are protagonists with agency, pride, "
                    "and concrete plans. That inversion of the conventional role is what makes "
                    "the spot work both emotionally and strategically.</p>"
                    "<p>The risk of this documentary format is authenticity: if the viewer "
                    "senses the stories are manufactured, everything collapses. The success of "
                    "«Habla, Perú» proves the creatives did the necessary fieldwork for each "
                    "story to stand on its own. A textbook on building brand trust from the "
                    "bottom up.</p>"
                ),
            },
        },
    },

    # ── 2. PILSEN CALLAO "Mejor amigo" (Perú, 2019) ────────────────────────
    # Una de las series de campaña más largas de la publicidad peruana.
    # YouTube: https://www.youtube.com/watch?v=ORQmk3-RJus  (*real, spot 2019)
    {
        "slug":     "pilsen-callao-mejor-amigo-2019",
        "brand":    "Pilsen Callao",
        "country":  "PE",
        "year":     2019,
        "youtube_id": "ORQmk3-RJus",
        "categories": [("Bebidas", "Beverages")],
        "translations": {
            "es": {
                "title": "Pilsen y los 'mejores amigos': la campaña que duró más que el producto",
                "analysis_text": (
                    "<p>La plataforma «Mejor amigo» de Pilsen Callao es un caso raro en "
                    "publicidad peruana: una campaña que se extendió por más de una década "
                    "sin agotarse. La razón es que el territorio —la amistad masculina sincera, "
                    "sin performatividad— no envejeció porque era genuinamente escaso en la "
                    "comunicación de marcas en el mercado local.</p>"
                    "<p>Este spot de 2019 es uno de los mejores de la serie porque el insight "
                    "es universal pero la ejecución es marcadamente peruana: el humor es de "
                    "observación, el casting refleja la diversidad real del país y el ritmo "
                    "narrativo no apura la emoción. La cerveza aparece casi como consecuencia "
                    "natural del momento, no como el objetivo.</p>"
                    "<p>Lo que Pilsen entiende mejor que muchas marcas: el producto puede ser "
                    "el pretexto, no el héroe. Cuando la historia es lo suficientemente buena, "
                    "la marca se beneficia sin necesidad de autoproclamarse. Eso requiere "
                    "confianza estratégica que pocas marcas en mercados emergentes se permiten.</p>"
                ),
            },
            "en": {
                "title": "Pilsen and the 'Best Friend': The Campaign That Outlasted the Product",
                "analysis_text": (
                    "<p>Pilsen Callao's «Best Friend» platform is a rare case in Peruvian "
                    "advertising: a campaign that ran for over a decade without exhausting "
                    "itself. The reason is that the territory — genuine male friendship without "
                    "performativity — didn't age because it was genuinely scarce in brand "
                    "communication in the local market.</p>"
                    "<p>This 2019 spot is one of the best in the series because the insight is "
                    "universal but the execution is distinctly Peruvian: the humor is "
                    "observational, the casting reflects the country's real diversity, and the "
                    "narrative pace doesn't rush the emotion. The beer appears almost as a "
                    "natural consequence of the moment, not as the objective.</p>"
                    "<p>What Pilsen understands better than most brands: the product can be the "
                    "pretext, not the hero. When the story is good enough, the brand benefits "
                    "without needing to self-proclaim. That requires strategic confidence that "
                    "few brands in emerging markets allow themselves.</p>"
                ),
            },
        },
    },

    # ── 3. INTERBANK "El tiempo es lo que más vale" (Perú, 2018) ───────────
    # Spot icónico de la banca peruana. Ganó múltiples Effies.
    # YouTube: https://www.youtube.com/watch?v=h6fcgAvf12g  (*real)
    {
        "slug":     "interbank-tiempo-lo-que-mas-vale-2018",
        "brand":    "Interbank",
        "country":  "PE",
        "year":     2018,
        "youtube_id": "h6fcgAvf12g",
        "categories": [("Finanzas", "Finance")],
        "translations": {
            "es": {
                "title": "Interbank: cuando un banco vende tiempo y no dinero",
                "analysis_text": (
                    "<p>La campaña «El tiempo es lo que más vale» de Interbank es una de las "
                    "reposiciones estratégicas más elegantes de la banca peruana. En un "
                    "mercado donde todos los bancos hablan de tasas, rendimientos y beneficios "
                    "financieros, Interbank optó por <em>cambiar completamente el bien que "
                    "ofrece</em>: no vende dinero, vende tiempo libre.</p>"
                    "<p>El spot articula el insight de forma directa y sin concesiones: los "
                    "peruanos trabajan demasiado, las gestiones bancarias consumen horas valiosas, "
                    "y Interbank propone ser el banco que te devuelve ese tiempo. La propuesta "
                    "es funcional —servicios digitales, menos colas— pero la ejecución la eleva "
                    "a lo emocional: el tiempo no es un recurso, es vida.</p>"
                    "<p>El peligro de este tipo de promesa es la brecha entre comunicación y "
                    "experiencia real. Si el cliente va al banco y espera 40 minutos, la promesa "
                    "se destruye. Que la campaña haya funcionado indica que Interbank tuvo la "
                    "disciplina de alinear operaciones con comunicación, que es la parte más "
                    "difícil de cualquier reposicionamiento de marca.</p>"
                ),
            },
            "en": {
                "title": "Interbank: When a Bank Sells Time Instead of Money",
                "analysis_text": (
                    "<p>Interbank's «Time Is What Matters Most» campaign is one of the most "
                    "elegant strategic repositionings in Peruvian banking. In a market where "
                    "every bank talks about rates, yields, and financial benefits, Interbank "
                    "chose to <em>completely change the commodity it offers</em>: it doesn't "
                    "sell money — it sells free time.</p>"
                    "<p>The spot articulates the insight directly and without concessions: "
                    "Peruvians work too much, banking tasks consume valuable hours, and Interbank "
                    "proposes to be the bank that gives that time back. The promise is functional "
                    "— digital services, fewer queues — but the execution elevates it to the "
                    "emotional: time isn't a resource, it's life.</p>"
                    "<p>The danger of this kind of promise is the gap between communication and "
                    "real experience. If the customer visits the branch and waits 40 minutes, the "
                    "promise collapses. That the campaign worked suggests Interbank had the "
                    "discipline to align operations with communication — which is the hardest "
                    "part of any brand repositioning.</p>"
                ),
            },
        },
    },

    # ── 4. ENTEL "Los robots" (Perú, 2022) ─────────────────────────────────
    # Campaña masiva de Entel Perú con humor y robots. Alta recordación.
    # YouTube (placeholder — buscar "Entel robots 2022 Peru"):
    {
        "slug":     "entel-peru-robots-2022",
        "brand":    "Entel",
        "country":  "PE",
        "year":     2022,
        "youtube_id": "dQw4w9WgXcQ",   # placeholder — reemplaza con ID real
        "categories": [("Telecomunicaciones", "Telecom")],
        "translations": {
            "es": {
                "title": "Entel y los robots: el humor absurdo como herramienta de diferenciación",
                "analysis_text": (
                    "<p>El mercado de telecomunicaciones peruano es uno de los más competidos y "
                    "menos diferenciados del mundo. Claro, Movistar, Bitel y Entel ofrecen "
                    "productos casi idénticos en precio y cobertura. En ese contexto, Entel "
                    "tomó una decisión creativa inusual: usar personajes robóticos en situaciones "
                    "cotidianas absurdas para construir recordación sin depender de argumentos "
                    "racionales.</p>"
                    "<p>La campaña funciona porque identifica correctamente el terreno donde "
                    "puede ganar: no es en la batalla de los gigabytes —ahí nadie gana de forma "
                    "sostenida— sino en la personalidad de marca. Los robots de Entel son "
                    "reconocibles, simpáticos y se asocian al humor sin ser ridículos. Eso es "
                    "más difícil de lograr de lo que parece.</p>"
                    "<p>El riesgo de las campañas de humor sin anclaje en beneficio funcional "
                    "es la superficialidad: el consumidor te recuerda pero no sabe por qué "
                    "elegirte. Entel mitiga esto conectando los personajes con mensajes de "
                    "cobertura y velocidad. No perfecto, pero más honesto que la mayoría.</p>"
                ),
            },
            "en": {
                "title": "Entel and the Robots: Absurd Humor as a Differentiation Tool",
                "analysis_text": (
                    "<p>Peru's telecom market is one of the most competitive and least "
                    "differentiated in the world. Claro, Movistar, Bitel, and Entel offer "
                    "products that are nearly identical in price and coverage. In that context, "
                    "Entel made an unusual creative decision: use robotic characters in absurd "
                    "everyday situations to build recall without relying on rational arguments.</p>"
                    "<p>The campaign works because it correctly identifies the ground where it "
                    "can win: not in the battle of gigabytes — nobody wins there sustainably — "
                    "but in brand personality. Entel's robots are recognizable, likeable, and "
                    "associated with humor without being ridiculous. That's harder to pull off "
                    "than it looks.</p>"
                    "<p>The risk of humor campaigns without a functional benefit anchor is "
                    "superficiality: consumers remember you but don't know why to choose you. "
                    "Entel mitigates this by connecting the characters to coverage and speed "
                    "messages. Not perfect, but more honest than most.</p>"
                ),
            },
        },
    },

    # ── 5. BCP "Misión Ahorro" (Perú, 2021) ────────────────────────────────
    # BCP (Banco de Crédito del Perú) — campaña de educación financiera gamificada.
    # YouTube (placeholder — buscar "BCP Misión Ahorro Perú"):
    {
        "slug":     "bcp-mision-ahorro-2021",
        "brand":    "BCP",
        "country":  "PE",
        "year":     2021,
        "youtube_id": "dQw4w9WgXcQ",   # placeholder
        "categories": [("Finanzas", "Finance")],
        "translations": {
            "es": {
                "title": "BCP Misión Ahorro: gamificación al servicio del alfabetismo financiero",
                "analysis_text": (
                    "<p>El BCP tiene el reto permanente de comunicar productos financieros "
                    "complejos a un público amplio que incluye segmentos con poca familiaridad "
                    "bancaria. «Misión Ahorro» aborda este reto con una solución inteligente: "
                    "convertir el proceso de ahorro en una narrativa de misión, con metas "
                    "claras, progreso visible y recompensas simbólicas.</p>"
                    "<p>Lo que hace bien esta campaña es la alineación entre concepto creativo "
                    "y producto real. No es un spot que promete algo que la aplicación no puede "
                    "cumplir: la mecánica de gamificación está integrada en la experiencia "
                    "digital del banco. Eso hace que la comunicación sea publicidad y "
                    "demostración de producto al mismo tiempo.</p>"
                    "<p>La debilidad es la ejecución visual, que a veces cae en los lugares "
                    "comunes del diseño de apps y no tiene la contundencia gráfica de las "
                    "mejores campañas de banca digital global. Buen estrategia, ejecución "
                    "mejorable.</p>"
                ),
            },
            "en": {
                "title": "BCP Misión Ahorro: Gamification in the Service of Financial Literacy",
                "analysis_text": (
                    "<p>BCP faces the permanent challenge of communicating complex financial "
                    "products to a broad audience that includes segments with little banking "
                    "familiarity. «Misión Ahorro» (Savings Mission) addresses this with an "
                    "intelligent solution: turning the savings process into a mission narrative, "
                    "with clear goals, visible progress, and symbolic rewards.</p>"
                    "<p>What this campaign does well is the alignment between creative concept "
                    "and real product. It's not a spot that promises something the app can't "
                    "deliver: the gamification mechanic is integrated into the bank's digital "
                    "experience. That makes the communication both advertising and product "
                    "demonstration simultaneously.</p>"
                    "<p>The weakness is the visual execution, which sometimes falls into the "
                    "common places of app design and lacks the graphic punch of the best global "
                    "digital banking campaigns. Good strategy, improvable execution.</p>"
                ),
            },
        },
    },

    # ── 6. MERCADO LIBRE "Hasta que lo logres" (Argentina/LatAm, 2022) ─────
    # Campaña regional de Mercado Libre sobre emprendimiento.
    # YouTube (placeholder — buscar "Mercado Libre hasta que lo logres 2022"):
    {
        "slug":     "mercado-libre-hasta-que-lo-logres-2022",
        "brand":    "Mercado Libre",
        "country":  "AR",
        "year":     2022,
        "youtube_id": "dQw4w9WgXcQ",   # placeholder
        "categories": [("Retail", "Retail")],
        "translations": {
            "es": {
                "title": "Mercado Libre: la plataforma que se vende como filosofía de vida",
                "analysis_text": (
                    "<p>Mercado Libre tiene una presencia tan dominante en el e-commerce "
                    "latinoamericano que su reto de comunicación es inusual: no necesita "
                    "convencer a nadie de que existe. Lo que necesita es mantener relevancia "
                    "emocional frente a Amazon, que avanza en la región con precios agresivos. "
                    "La respuesta de Mercado Libre es apostar por el origen: somos de aquí, "
                    "entendemos cómo piensan los latinoamericanos.</p>"
                    "<p>«Hasta que lo logres» es una campaña de perseverancia y emprendimiento "
                    "que conecta el acto de vender en la plataforma con valores culturales "
                    "profundos: la resistencia ante la adversidad, el ingenio como solución. "
                    "El insight es real y resonante; cualquier pequeño vendedor en LATAM se "
                    "reconoce en esas historias.</p>"
                    "<p>El riesgo: cuando una marca de tecnología habla de «humanidad» y "
                    "«emprendimiento», el escéptico detecta instrumentalización. Mercado Libre "
                    "lo mitiga con casos reales y sin sobreproducción. La autenticidad de la "
                    "ejecución es lo que convierte el mensaje en algo más que eslogan.</p>"
                ),
            },
            "en": {
                "title": "Mercado Libre: The Platform That Sells Itself as a Life Philosophy",
                "analysis_text": (
                    "<p>Mercado Libre has such dominant presence in Latin American e-commerce "
                    "that its communication challenge is unusual: it doesn't need to convince "
                    "anyone it exists. What it needs is to maintain emotional relevance against "
                    "Amazon, which is advancing in the region with aggressive pricing. Mercado "
                    "Libre's answer is to bet on origin: we're from here, we understand how "
                    "Latin Americans think.</p>"
                    "<p>«Hasta que lo logres» (Until You Make It) is a campaign of perseverance "
                    "and entrepreneurship that connects the act of selling on the platform to "
                    "deep cultural values: resilience against adversity, ingenuity as solution. "
                    "The insight is real and resonant; any small seller in LATAM recognizes "
                    "themselves in those stories.</p>"
                    "<p>The risk: when a tech brand talks about «humanity» and «entrepreneurship,» "
                    "skeptics detect instrumentalization. Mercado Libre mitigates this with real "
                    "cases and without overproduction. The authenticity of the execution is what "
                    "turns the message into more than a slogan.</p>"
                ),
            },
        },
    },

    # ── 7. NIKE "You Can't Stop Us" (EE.UU., 2020) ──────────────────────────
    # Spot viral del año COVID. Pantalla dividida con atletas en paralelo.
    # YouTube oficial: https://www.youtube.com/watch?v=WvncJNxXJb4  (*real)
    {
        "slug":     "nike-you-cant-stop-us-2020",
        "brand":    "Nike",
        "country":  "US",
        "year":     2020,
        "youtube_id": "WvncJNxXJb4",
        "categories": [("Deportes", "Sports")],
        "translations": {
            "es": {
                "title": "Nike 'You Can't Stop Us': edición y atletismo como argumento",
                "analysis_text": (
                    "<p>En el contexto de la pandemia del COVID-19, Nike publicó uno de los "
                    "spots más técnicamente brillantes de la historia reciente de la publicidad. "
                    "«You Can't Stop Us» usa pantalla dividida para emparejar a 53 atletas en "
                    "acciones que se complementan a la perfección, creando la ilusión de un "
                    "único movimiento ininterrumpido. El mérito de producción es excepcional: "
                    "la edición tardó meses en construirse cuadro a cuadro.</p>"
                    "<p>Pero el spot es más que un ejercicio técnico. La selección de atletas "
                    "es deliberadamente diversa en género, deporte, raza y nivel de "
                    "reconocimiento. El mensaje no es «nuestros productos son mejores» sino "
                    "«el deporte une lo que el mundo separa». En tiempos de confinamiento y "
                    "polarización, ese mensaje tenía urgencia real.</p>"
                    "<p>La crítica válida es que Nike, como todas las grandes marcas de ropa "
                    "deportiva, tiene problemas de cadena de suministro que contradicen los "
                    "valores que anuncia. Eso no hace que el spot sea menos brillante como "
                    "pieza comunicacional, pero sí hace que el escrutinio sobre la autenticidad "
                    "de la marca sea mayor.</p>"
                ),
            },
            "en": {
                "title": "Nike 'You Can't Stop Us': Editing and Athleticism as Argument",
                "analysis_text": (
                    "<p>In the context of the COVID-19 pandemic, Nike released one of the most "
                    "technically brilliant spots in recent advertising history. «You Can't Stop "
                    "Us» uses split-screen to pair 53 athletes in perfectly complementary "
                    "actions, creating the illusion of a single uninterrupted movement. The "
                    "production merit is exceptional: the edit took months to construct "
                    "frame-by-frame.</p>"
                    "<p>But the spot is more than a technical exercise. The athlete selection is "
                    "deliberately diverse in gender, sport, race, and recognition level. The "
                    "message isn't «our products are better» but «sport unites what the world "
                    "divides.» In times of lockdown and polarization, that message carried "
                    "real urgency.</p>"
                    "<p>The valid critique is that Nike, like all major sportswear brands, has "
                    "supply chain issues that contradict the values it announces. That doesn't "
                    "make the spot less brilliant as a communication piece, but it does mean "
                    "scrutiny on the brand's authenticity is higher.</p>"
                ),
            },
        },
    },

    # ── 8. DOVE "Real Beauty Sketches" (EE.UU., 2013) ───────────────────────
    # Una de las piezas más virales de la historia. Cannes Lions Grand Prix.
    # YouTube oficial: https://www.youtube.com/watch?v=XpaOjMXyJGk  (*real)
    {
        "slug":     "dove-real-beauty-sketches-2013",
        "brand":    "Dove",
        "country":  "US",
        "year":     2013,
        "youtube_id": "XpaOjMXyJGk",
        "categories": [("Salud y belleza", "Health & Beauty")],
        "translations": {
            "es": {
                "title": "Dove Real Beauty Sketches: la campaña que cambió cómo las marcas hablan de belleza",
                "analysis_text": (
                    "<p>«Real Beauty Sketches» de Dove es, por métricas de impacto, una de "
                    "las campañas más exitosas de la historia moderna de la publicidad: fue "
                    "vista más de 163 millones de veces en su primer mes, ganó el Grand Prix "
                    "en Cannes Lions y generó cobertura editorial equivalente a cientos de "
                    "millones en medios pagados. El concepto es simple: un retratista forense "
                    "dibuja a mujeres según como ellas mismas se describen, y luego según como "
                    "las describen extraños. Los retratos son radicalmente distintos.</p>"
                    "<p>La fortaleza del spot es que el insight es irrefutablemente real: las "
                    "mujeres suelen ser más severas consigo mismas que los demás. Al hacer eso "
                    "visible con metodología neutral —el retratista no sabe cuál es el "
                    "propósito— la pieza elude el cinismo habitual hacia la publicidad de "
                    "belleza. La verdad observada tiene más peso que cualquier eslogan.</p>"
                    "<p>La crítica académica —y es válida— es la paradoja de que una marca "
                    "de belleza lucre con el mensaje de que no necesitas productos de belleza "
                    "para ser hermosa. Dove ha respondido a esto con más profundidad que sus "
                    "competidoras, pero la tensión nunca desaparece del todo. Es el límite "
                    "estructural de la «purpose advertising» cuando el propósito y el modelo "
                    "de negocio no coinciden perfectamente.</p>"
                ),
            },
            "en": {
                "title": "Dove Real Beauty Sketches: The Campaign That Changed How Brands Talk About Beauty",
                "analysis_text": (
                    "<p>Dove's «Real Beauty Sketches» is, by impact metrics, one of the most "
                    "successful campaigns in modern advertising history: it was viewed over 163 "
                    "million times in its first month, won the Grand Prix at Cannes Lions, and "
                    "generated editorial coverage equivalent to hundreds of millions in paid "
                    "media. The concept is simple: a forensic sketch artist draws women based "
                    "on how they describe themselves, then based on how strangers describe them. "
                    "The portraits are radically different.</p>"
                    "<p>The spot's strength is that the insight is irrefutably real: women are "
                    "often harsher on themselves than others are. By making this visible with "
                    "neutral methodology — the artist doesn't know the purpose — the piece "
                    "sidesteps the usual cynicism toward beauty advertising. Observed truth "
                    "carries more weight than any slogan.</p>"
                    "<p>The academic critique — and it's valid — is the paradox of a beauty "
                    "brand profiting from the message that you don't need beauty products to be "
                    "beautiful. Dove has responded to this with more depth than its competitors, "
                    "but the tension never fully disappears. It's the structural limit of "
                    "«purpose advertising» when the purpose and the business model don't "
                    "perfectly align.</p>"
                ),
            },
        },
    },

    # ── 9. GLORIA "Soy Peruano" (Perú, 2023) ───────────────────────────────
    # Gloria Perú — campaña de orgullo nacional vinculada a la gastronomía peruana.
    # YouTube (placeholder — buscar "Gloria Peru spot 2023"):
    {
        "slug":     "gloria-peru-soy-peruano-2023",
        "brand":    "Gloria",
        "country":  "PE",
        "year":     2023,
        "youtube_id": "dQw4w9WgXcQ",   # placeholder
        "categories": [("Alimentos", "Food")],
        "translations": {
            "es": {
                "title": "Gloria y el orgullo nacional: la leche que se vende como identidad",
                "analysis_text": (
                    "<p>Gloria es la marca de lácteos más dominante del Perú, con una "
                    "penetración de hogar que roza el monopolio en muchas categorías. En ese "
                    "escenario, el reto publicitario no es convencer —casi todos ya compran "
                    "Gloria— sino mantener la relevancia emocional para defenderse de marcas "
                    "premium internacionales que intentan ganar espacio en el segmento alto.</p>"
                    "<p>La estrategia de asociar Gloria a la gastronomía peruana —uno de los "
                    "activos identitarios más potentes del país en la última década— es "
                    "inteligente porque ancla la marca a un orgullo que está en expansión. "
                    "El crecimiento global de la cocina peruana hace que cualquier marca que "
                    "se posicione dentro de ese ecosistema tenga viento a favor.</p>"
                    "<p>El talón de Aquiles de Gloria es la controversia pública recurrente "
                    "sobre la calidad de sus productos y los procesos de producción. Una "
                    "campaña de «orgullo peruano» es más vulnerable cuando existe una brecha "
                    "entre la imagen proyectada y la percepción real en medios y redes sociales. "
                    "El riesgo reputacional es el verdadero brief sin resolver.</p>"
                ),
            },
            "en": {
                "title": "Gloria and National Pride: The Milk That Sells as Identity",
                "analysis_text": (
                    "<p>Gloria is Peru's most dominant dairy brand, with household penetration "
                    "approaching monopoly in many categories. In that scenario, the advertising "
                    "challenge isn't to convince — almost everyone already buys Gloria — but to "
                    "maintain emotional relevance against international premium brands trying to "
                    "gain ground in the upper segment.</p>"
                    "<p>The strategy of associating Gloria with Peruvian gastronomy — one of the "
                    "country's most powerful identity assets of the last decade — is smart "
                    "because it anchors the brand to an expanding pride. The global growth of "
                    "Peruvian cuisine means any brand that positions itself within that ecosystem "
                    "has the wind at its back.</p>"
                    "<p>Gloria's Achilles' heel is the recurring public controversy around its "
                    "product quality and production processes. A «Peruvian pride» campaign is "
                    "more vulnerable when there's a gap between the projected image and the real "
                    "perception in media and social networks. The reputational risk is the real "
                    "unresolved brief.</p>"
                ),
            },
        },
    },

    # ── 10. CORONA "La cerveza más fina" / Beach spot (México, 2021) ────────
    # Corona — campaña global con identidad mexicana y playa. Alta recordación global.
    # YouTube (placeholder — buscar "Corona cerveza spot 2021 playa"):
    {
        "slug":     "corona-cerveza-mas-fina-2021",
        "brand":    "Corona",
        "country":  "MX",
        "year":     2021,
        "youtube_id": "dQw4w9WgXcQ",   # placeholder
        "categories": [("Bebidas", "Beverages")],
        "translations": {
            "es": {
                "title": "Corona: el territorio del 'descanso ganado' y por qué es genial",
                "analysis_text": (
                    "<p>Corona es un fenómeno de marca que merece estudio independientemente "
                    "de si te gusta la cerveza. En pocas décadas pasó de ser una marca mexicana "
                    "de consumo masivo a convertirse en el símbolo global del «descanso "
                    "merecido»: ese momento al final del día en que uno se sienta frente al mar "
                    "con una cerveza fría. El insight es atemporal y la ejecución siempre "
                    "disciplinada.</p>"
                    "<p>Lo que distingue a Corona de otras cervezas que usan playas y puestas "
                    "de sol es la consistencia total del sistema visual: la botella siempre "
                    "aparece sobre el horizonte, con el cielo como fondo, en silencio o con "
                    "música minimalista. Esa coherencia acumulada durante décadas hace que "
                    "el logo sea casi innecesario. El formato <em>es</em> la marca.</p>"
                    "<p>La pandemia del COVID-19 generó una crisis de imagen involuntaria "
                    "por la coincidencia de nombre, pero Corona la navegó sin cambios de "
                    "plataforma —una señal de confianza estratégica bien fundada en la "
                    "solidez del territorio construido. Pocas marcas habrían sobrevivido "
                    "ese nivel de ruido sin alterar el curso.</p>"
                ),
            },
            "en": {
                "title": "Corona: The 'Earned Rest' Territory and Why It's Brilliant",
                "analysis_text": (
                    "<p>Corona is a brand phenomenon worth studying regardless of whether you "
                    "like beer. In a few decades it went from being a Mexican mass-market brand "
                    "to becoming the global symbol of «earned rest»: that moment at the end of "
                    "the day when you sit down by the sea with a cold beer. The insight is "
                    "timeless and the execution always disciplined.</p>"
                    "<p>What distinguishes Corona from other beers that use beaches and sunsets "
                    "is total visual system consistency: the bottle always appears against the "
                    "horizon, with sky as background, in silence or with minimalist music. That "
                    "consistency accumulated over decades makes the logo almost unnecessary. "
                    "The format <em>is</em> the brand.</p>"
                    "<p>The COVID-19 pandemic created an involuntary image crisis due to the "
                    "name coincidence, but Corona navigated it without platform changes — a "
                    "signal of well-founded strategic confidence in the solidity of the built "
                    "territory. Few brands would have survived that level of noise without "
                    "altering course.</p>"
                ),
            },
        },
    },

]


def seed2():
    app = create_app()
    with app.app_context():

        for data in SAMPLE_ADS:
            if Ad.query.filter_by(slug=data["slug"]).first():
                print(f"  skip (ya existe): {data['slug']}")
                continue

            ad = Ad(
                slug=data["slug"],
                brand=data["brand"],
                country=data["country"],
                year=data["year"],
                youtube_id=data["youtube_id"],
                video_source_type="youtube",
                video_source_value=data["youtube_id"],
                status="published",
            )
            db.session.add(ad)
            db.session.flush()

            # Assign categories
            for name_es, name_en in data.get("categories", []):
                cat = get_or_create_category(name_es, name_en)
                if cat not in ad.categories:
                    ad.categories.append(cat)

            # Translations
            for lang, td in data["translations"].items():
                db.session.add(AdTranslation(
                    ad_id=ad.id,
                    language=lang,
                    title=td["title"],
                    analysis_text=td["analysis_text"],
                ))
            print(f"  añadido: {data['slug']}")

        db.session.commit()
        print("seed2 completado — 10 anuncios procesados.")


if __name__ == "__main__":
    seed2()
