# -*- coding: utf-8 -*-
"""
Liste curatee des marques a avoir en bibliotheque - Hyperframes.

Critere d'entree : "est-ce qu'une de nos videos pourrait prononcer ce nom ?"
On couvre donc la niche IA/automatisation en profondeur, ET les secteurs des
clients potentiels (commerce, immobilier, sante, RH, transport...), parce qu'un
Reel qui parle d'automatisation pour une TPE cite les outils de cette TPE.

Les noms sont ecrits en clair ; `fetch-logos-massif.py` les resout contre la liste
reelle des icones disponibles. Un nom qui ne matche pas est signale, pas devine.

Le dossier de sortie porte le prefixe numerique : il ordonne l'affichage.
"""

SECTEURS = {

    "01-ia-modeles": [
        "Anthropic", "Claude", "OpenAI", "Google Gemini", "Mistral AI", "Perplexity",
        "Hugging Face", "Ollama", "Meta", "xAI", "Cohere", "Stability AI", "Replicate",
        "Together AI", "Groq", "LangChain", "LlamaIndex", "Weights & Biases", "Kaggle",
        "TensorFlow", "PyTorch", "Keras", "scikit-learn", "NumPy", "pandas", "OpenCV",
        "ONNX", "NVIDIA", "Google Colab", "Jupyter", "Gradio", "Streamlit", "Roboflow",
        "DeepL", "ElevenLabs", "Runway", "Midjourney", "Leonardo AI", "Civitai",
        "Comfy", "Qdrant", "Pinecone", "Chroma", "Milvus", "Weaviate", "Modal",
        "Vercel", "OpenAI Gym", "Databricks", "Snowflake",
    ],

    "02-automatisation-nocode": [
        "n8n", "Zapier", "Make", "Airtable", "Notion", "Retool", "Bubble", "Glide",
        "Softr", "Coda", "Baserow", "NocoDB", "Appsmith", "Budibase", "ToolJet",
        "Node-RED", "Apache Airflow", "Prefect", "Temporal", "Camunda", "Activepieces",
        "Pipedream", "Integromat", "IFTTT", "Automattic", "Webflow", "Framer",
        "Typeform", "Tally", "Jotform", "Google Forms", "SurveyMonkey", "Calendly",
        "Cal.com", "Zoho", "Monday", "ClickUp", "Smartsheet", "Process Street",
    ],

    "03-dev-langages": [
        "Python", "JavaScript", "TypeScript", "Node.js", "Deno", "Bun", "React",
        "Next.js", "Vue.js", "Nuxt", "Svelte", "Angular", "Astro", "Remix", "Solid",
        "Qwik", "Vite", "Webpack", "esbuild", "Rollup", "Babel", "ESLint", "Prettier",
        "Jest", "Vitest", "Cypress", "Playwright", "Puppeteer", "Selenium", "Storybook",
        "Tailwind CSS", "Bootstrap", "Sass", "PostCSS", "Three.js", "D3.js", "Chart.js",
        "GSAP", "Framer Motion", "Lottie", "Electron", "Tauri", "Capacitor", "Ionic",
        "React Native", "Expo", "Flutter", "Dart", "Swift", "Kotlin", "Java", "Go",
        "Rust", "C", "C++", "C Sharp", ".NET", "PHP", "Laravel", "Symfony", "Ruby",
        "Ruby on Rails", "Django", "Flask", "FastAPI", "Express", "NestJS", "Spring",
        "Scala", "Elixir", "Phoenix Framework", "Haskell", "Clojure", "Lua", "Perl",
        "R", "Julia", "MATLAB", "GraphQL", "Apollo GraphQL", "tRPC", "Prisma",
        "Drizzle", "Sequelize", "SQLAlchemy", "OpenAPI Initiative", "Swagger", "Postman",
        "Insomnia", "Bruno", "HTTPie", "cURL", "JSON", "YAML", "Markdown", "HTML5",
        "CSS", "WebAssembly", "Vim", "Neovim", "Emacs", "Zed Industries",
    ],

    "04-dev-outils": [
        "GitHub", "GitLab", "Bitbucket", "Git", "GitHub Actions", "GitHub Copilot",
        "Visual Studio Code", "Visual Studio", "JetBrains", "IntelliJ IDEA", "PyCharm",
        "WebStorm", "PhpStorm", "Android Studio", "Xcode", "Sublime Text", "Atom",
        "Eclipse IDE", "Docker", "Kubernetes", "Helm", "Terraform", "Ansible", "Vagrant",
        "Podman", "Jenkins", "CircleCI", "Travis CI", "Drone", "Argo", "Sentry",
        "Datadog", "New Relic", "Grafana", "Prometheus", "Kibana", "Elastic", "Splunk",
        "Sonarqube", "Snyk", "Dependabot", "Renovate", "npm", "Yarn", "pnpm", "Homebrew",
        "Chocolatey", "Nix", "Bash", "PowerShell", "GNU Bash", "Linux", "Ubuntu",
        "Debian", "Fedora", "Arch Linux", "Red Hat", "CentOS", "Alpine Linux",
        "Raspberry Pi", "Arduino", "Qwiklabs",
    ],

    "05-cloud-infra": [
        "Amazon Web Services", "Google Cloud", "Microsoft Azure", "Cloudflare",
        "Vercel", "Netlify", "Heroku", "DigitalOcean", "Linode", "Vultr", "Hetzner",
        "OVH", "Scaleway", "Fly.io", "Railway", "Render", "Supabase", "Firebase",
        "PlanetScale", "Neon", "Upstash", "Deno Deploy", "Cloud Foundry", "OpenStack",
        "VMware", "Proxmox", "Nginx", "Apache", "Caddy", "Traefik", "HAProxy",
        "Let's Encrypt", "Namecheap", "GoDaddy", "Gandi", "Porkbun", "Squarespace",
    ],

    "06-donnees": [
        "PostgreSQL", "MySQL", "MariaDB", "SQLite", "MongoDB", "Redis", "Cassandra",
        "Neo4j", "InfluxDB", "ClickHouse", "DuckDB", "Elasticsearch", "Apache Kafka",
        "RabbitMQ", "Apache Spark", "Apache Hadoop", "dbt", "Metabase", "Superset",
        "Looker", "Tableau", "Power BI", "Qlik", "Amplitude", "Mixpanel", "Segment",
        "Google Analytics", "Matomo", "Plausible Analytics", "Fathom", "Hotjar",
        "PostHog", "Snowflake", "BigQuery",
    ],

    "07-design-creatif": [
        "Figma", "Sketch", "InVision", "Framer", "Penpot", "Affinity Designer",
        "Affinity Photo", "Affinity Publisher", "Inkscape", "GIMP", "Krita",
        "Blender", "Autodesk", "Cinema 4D", "Unity", "Unreal Engine", "Godot Engine",
        "Spline", "Rive", "Lottie Files", "Dribbble", "Behance", "Awwwards",
        "Unsplash", "Pexels", "Pixabay", "Iconify", "Font Awesome", "Google Fonts",
        "Adobe Fonts", "Material Design", "Ant Design", "Chakra UI", "Radix UI",
        "shadcn/ui", "Storyblok", "Contentful", "Sanity", "Strapi", "Prismic",
    ],

    "08-video-audio": [
        "Adobe After Effects", "Adobe Premiere Pro", "Adobe Photoshop",
        "Adobe Illustrator", "Adobe Lightroom", "Adobe Audition", "Adobe Creative Cloud",
        "DaVinci Resolve", "Final Cut Pro", "CapCut", "OBS Studio", "Streamlabs",
        "Descript", "Riverside.fm", "Loom", "Camtasia", "Kdenlive", "Shotcut",
        "HandBrake", "FFmpeg", "VLC media player", "Audacity", "Ableton Live",
        "FL Studio", "Logic Pro", "Pro Tools", "Reaper", "Bitwig", "Spotify",
        "SoundCloud", "Bandcamp", "Epidemic Sound", "Artlist", "Splice", "Shazam",
        "Apple Music", "Deezer", "Tidal", "YouTube Music", "Podcast Index",
    ],

    "09-productivite": [
        "Notion", "Obsidian", "Evernote", "Roam Research", "Logseq", "Bear",
        "Apple Notes", "Google Keep", "Todoist", "Things", "TickTick", "Microsoft To Do",
        "Trello", "Asana", "Jira", "Confluence", "Linear", "Height", "Basecamp",
        "Wrike", "Teamwork", "Miro", "Mural", "FigJam", "Whimsical", "Excalidraw",
        "Draw.io", "Lucid", "Mermaid", "Obsidian Publish", "Readwise", "Pocket",
        "Instapaper", "Raycast", "Alfred", "Rectangle", "1Password", "Bitwarden",
        "LastPass", "Dashlane", "KeePassXC", "Proton", "Proton Mail", "Proton VPN",
        "Dropbox", "Box", "Google Drive", "OneDrive", "iCloud", "Mega", "pCloud",
        "Syncthing", "Nextcloud", "Zotero", "Mendeley",
    ],

    "10-communication": [
        "Slack", "Microsoft Teams", "Discord", "Zoom", "Google Meet", "Webex",
        "Skype", "Telegram", "WhatsApp", "Signal", "Messenger", "WeChat", "LINE",
        "Viber", "Element", "Matrix", "Mattermost", "Rocket.chat", "Twilio",
        "SendGrid", "Mailgun", "Postmark", "Resend", "Brevo", "Mailchimp",
        "ConvertKit", "Beehiiv", "Substack", "Ghost", "Intercom", "Crisp", "Zendesk",
        "Freshdesk", "Help Scout", "Front", "Gmail", "Microsoft Outlook",
        "Thunderbird", "Fastmail", "Zoho Mail", "Spark",
    ],

    "11-reseaux-sociaux": [
        "Instagram", "TikTok", "YouTube", "X", "Facebook", "Threads", "Snapchat",
        "Pinterest", "Reddit", "Tumblr", "Mastodon", "Bluesky", "Twitch", "Kick",
        "Vimeo", "Dailymotion", "Rumble", "Clubhouse", "BeReal", "Medium",
        "Dev.to", "Hashnode", "Hacker News", "Product Hunt", "Indie Hackers",
        "Stack Overflow", "Quora", "Discourse", "Buffer", "Hootsuite", "Later",
        "Metricool", "Sprout Social",
    ],

    "12-commerce-paiement": [
        "Shopify", "WooCommerce", "PrestaShop", "Magento", "BigCommerce", "Squarespace",
        "Wix", "Etsy", "Amazon", "eBay", "Alibaba", "AliExpress", "Temu", "Shein",
        "Stripe", "PayPal", "Square", "Adyen", "Mollie", "Klarna", "Visa",
        "Mastercard", "American Express", "Revolut", "N26", "Wise", "Qonto",
        "Lydia", "Monzo", "Curve", "Coinbase", "Binance", "Kraken", "Ledger",
        "Bitcoin", "Ethereum", "Solana", "Tether", "Chainlink", "Polygon",
        "Gumroad", "Lemon Squeezy", "Paddle", "Chargebee", "Recurly",
    ],

    "13-marketing-crm": [
        "HubSpot", "Salesforce", "Pipedrive", "Zoho CRM", "Close", "Copper",
        "ActiveCampaign", "Klaviyo", "Braze", "Customer.io", "Iterable",
        "Google Ads", "Meta", "Google Tag Manager", "Semrush", "Ahrefs", "Moz",
        "Screaming Frog", "Similarweb", "Hotjar", "Optimizely", "VWO",
        "Unbounce", "Instapage", "Leadpages", "ClickFunnels", "Systeme.io",
        "Kajabi", "Teachable", "Thinkific", "Podia", "Circle", "Skool",
        "Patreon", "Ko-fi", "Buy Me a Coffee",
    ],

    "14-google-microsoft-apple": [
        "Google", "Google Chrome", "Google Drive", "Google Docs", "Google Sheets",
        "Google Slides", "Google Forms", "Google Calendar", "Google Maps",
        "Google Photos", "Google Play", "Google Meet", "Google Keep",
        "Google Classroom", "Google Cloud", "Google Search Console", "YouTube Studio",
        "Microsoft", "Microsoft Excel", "Microsoft Word", "Microsoft PowerPoint",
        "Microsoft Outlook", "Microsoft OneNote", "Microsoft SharePoint",
        "Microsoft OneDrive", "Microsoft Edge", "Windows", "Xbox",
        "Apple", "macOS", "iOS", "Safari", "App Store", "Apple Pay", "Apple Podcasts",
        "TestFlight", "Home Assistant",
    ],

    "15-navigateurs-materiel": [
        "Firefox", "Brave", "Opera", "Vivaldi", "Arc", "Tor Browser", "DuckDuckGo",
        "Ecosia", "Qwant", "Startpage", "Chromium", "WebKit",
        "Samsung", "Sony", "LG", "Dell", "HP", "Lenovo", "ASUS", "Acer", "MSI",
        "Razer", "Logitech", "Corsair", "SteelSeries", "Anker", "Belkin",
        "Intel", "AMD", "Qualcomm", "ARM", "Broadcom", "Western Digital", "Seagate",
        "Sandisk", "Kingston Technology", "Crucial", "GoPro", "DJI", "Canon", "Nikon",
        "Fujifilm", "Panasonic", "Sennheiser", "Bose", "Sonos", "Rode", "Shure",
        "Elgato", "Blackmagic Design",
    ],

    "16-education-medias": [
        "Coursera", "Udemy", "edX", "Khan Academy", "Duolingo", "Codecademy",
        "freeCodeCamp", "Pluralsight", "LinkedIn Learning", "Skillshare",
        "DataCamp", "Brilliant", "Anki", "Quizlet", "Notion", "Wikipedia",
        "Wikimedia", "arXiv", "ORCID", "Google Scholar", "ResearchGate",
        "TED", "Netflix", "Disney+", "Prime Video", "Hulu", "Max", "Crunchyroll",
        "Le Monde", "The New York Times", "The Guardian", "Bloomberg", "Reuters",
        "TechCrunch", "Wired", "Ars Technica", "The Verge", "Hacker Noon",
    ],

    "17-secteurs-clients": [
        "Uber", "Uber Eats", "Deliveroo", "DoorDash", "Just Eat", "Lyft", "Bolt",
        "BlaBlaCar", "Airbnb", "Booking.com", "Expedia", "Tripadvisor", "Trivago",
        "Ryanair", "Air France", "Lufthansa", "Emirates", "SNCF", "Eurostar",
        "FedEx", "DHL", "UPS", "La Poste", "Chronopost", "Colissimo",
        "IKEA", "Carrefour", "Leroy Merlin", "Decathlon", "Zalando", "ASOS",
        "Nike", "Adidas", "Zara", "H&M", "Uniqlo", "Sephora", "L'Oreal",
        "McDonald's", "Starbucks", "Burger King", "Domino's Pizza", "Deliveroo",
        "Tesla", "BMW", "Mercedes", "Audi", "Volkswagen", "Renault", "Peugeot",
        "Toyota", "Ford", "Porsche",
    ],

    "18-securite-identite": [
        "Auth0", "Okta", "Keycloak", "Clerk", "Firebase", "OAuth", "JSON Web Tokens",
        "NordVPN", "ExpressVPN", "Surfshark", "Mullvad", "ProtonVPN", "Tailscale",
        "WireGuard", "OpenVPN", "Cloudflare", "HashiCorp Vault", "Snyk",
        "OWASP", "Kali Linux", "Wireshark", "Metasploit", "Burp Suite",
        "Have I Been Pwned", "YubiKey", "Authy", "Google Authenticator",
    ],

    "19-jeux-divertissement": [
        "Steam", "Epic Games", "PlayStation", "Xbox", "Nintendo", "Nintendo Switch",
        "Itch.io", "GOG.com", "Roblox", "Minecraft", "Riot Games", "Valve",
        "Ubisoft", "Electronic Arts", "Rockstar Games", "Square Enix", "Sega",
        "Capcom", "Bandai Namco", "Twitch", "Kick", "Discord",
    ],

    "20-symboles-formats": [
        "PDF", "Microsoft Excel", "CSV", "JSON", "XML", "Markdown", "LaTeX",
        "QR Code", "RSS", "Bluetooth", "Wi-Fi", "USB", "HDMI", "Thunderbolt",
        "Creative Commons", "Open Source Initiative", "GNU", "Linux Foundation",
        "W3C", "Unicode", "IEEE", "ISO", "GitHub Sponsors", "Open Collective",
    ],
}
