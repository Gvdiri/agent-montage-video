#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generateur d'ecrans d'interface reutilisables - Hyperframes.

Pourquoi ce fichier existe :

La doctrine de retention designe la cause n1 des montages mous : "un schema dessine
est un aveu qu'on n'a rien de reel a montrer". Le probleme n'etait pas le schema,
c'etait le vide de la bibliotheque. Ici on fabrique le stock d'ecrans GENERIQUES
qui manquait - un terminal qui tourne, une conversation avec une IA, un tableau de
bord, une boite de reception - reutilisables d'une video a l'autre.

Contrainte levee par le createur le 2026-09-10 : ces ecrans n'ont pas a etre des
captures reelles. Ils sont generiques et ne portent aucune marque : ils illustrent,
ils n'affirment rien. (Fabriquer l'ecran d'un produit NOMME et le presenter comme
sa vraie interface reste exclu - ca, c'est une affirmation factuelle.)

Decision de conception - LES ECRANS SONT CLAIRS :
la reference qui performe a un panneau de preuve a 223/255 de luminance contre
94/255 sur le visage. Nos cartes graphite sur fond graphite ecrasaient ce contraste
"et rendaient le cadre mou" (EDITING_SYSTEM.md). Donc : fond clair par defaut.
Seuls le terminal et l'editeur de code restent sombres - ils le sont pour de vrai.

Rendu : Chrome headless -> PNG. Sortie dans asset-library/broll/.

Usage :
    python tools/generate-ui-screens.py [--only terminal,chat,...] [--list]
"""
import os
import sys
import json
import shutil
import argparse
import subprocess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio-analysis-pkgs"))
import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
BROLL = os.path.join(ROOT, "asset-library", "broll")
TMP = os.path.join(ROOT, "temp", "_ui-screens-html")

CHROME = None
for c in [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
          r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
          os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")]:
    if os.path.isfile(c):
        CHROME = c
        break

DESKTOP = (1600, 1000)
PHONE = (760, 1520)

_faits = []

# --------------------------------------------------------------------------- CSS
CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',Inter,system-ui,-apple-system,sans-serif;
     -webkit-font-smoothing:antialiased;overflow:hidden}
.app{width:100vw;height:100vh;display:flex;flex-direction:column;background:#FFF}
/* --- chrome de fenetre --- */
.bar{height:44px;background:#F0F1F3;border-bottom:1px solid #E1E3E6;
     display:flex;align-items:center;padding:0 16px;gap:8px;flex-shrink:0}
.dot{width:12px;height:12px;border-radius:50%}
.url{flex:1;height:28px;background:#FFF;border:1px solid #E1E3E6;border-radius:8px;
     display:flex;align-items:center;padding:0 12px;font-size:13px;color:#6B7280;margin-left:12px}
/* --- structure --- */
.body{flex:1;display:flex;min-height:0}
.side{width:250px;background:#FAFAFB;border-right:1px solid #EBEDEF;padding:18px 12px;flex-shrink:0}
.main{flex:1;padding:28px 34px;overflow:hidden;background:#FFF}
.brandmark{width:26px;height:26px;border-radius:7px;background:#111827;flex-shrink:0}
.navi{display:flex;align-items:center;gap:10px;padding:9px 12px;border-radius:8px;
      font-size:14px;color:#4B5563;margin-bottom:2px}
.navi.on{background:#EEF1F4;color:#111827;font-weight:600}
.ico{width:16px;height:16px;border-radius:4px;background:#C4CAD1;flex-shrink:0}
.navi.on .ico{background:#111827}
h1{font-size:27px;color:#0F172A;letter-spacing:-.5px;margin-bottom:6px;font-weight:700}
.sub{font-size:14px;color:#6B7280;margin-bottom:26px}
.card{background:#FFF;border:1px solid #EBEDEF;border-radius:14px;padding:20px;
      box-shadow:0 1px 3px rgba(16,24,40,.05)}
.row{display:flex;gap:16px}
.tag{display:inline-flex;align-items:center;gap:6px;font-size:12px;font-weight:600;
     padding:4px 10px;border-radius:999px}
.ok{background:#E7F6EC;color:#137333}
.warn{background:#FEF3E2;color:#B54708}
.info{background:#E6F4FD;color:#0B6FA4}
.bad{background:#FDECEC;color:#B42318}
.kpi{font-size:38px;font-weight:700;color:#0F172A;letter-spacing:-1.2px}
.kpil{font-size:13px;color:#6B7280;margin-bottom:8px}
.up{font-size:13px;color:#137333;font-weight:600}
.dn{font-size:13px;color:#B42318;font-weight:600}
table{width:100%;border-collapse:collapse;font-size:14px}
th{text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.6px;
   color:#98A2B3;padding:10px 12px;border-bottom:1px solid #EBEDEF;font-weight:600}
td{padding:13px 12px;border-bottom:1px solid #F2F4F6;color:#344054}
.av{width:30px;height:30px;border-radius:50%;flex-shrink:0}
/* --- sombre : terminal et editeur --- */
.dark{background:#0C1117;color:#C9D3DD}
.term{font-family:'Cascadia Code',Consolas,monospace;font-size:15.5px;line-height:1.75;
      padding:26px 30px;white-space:pre-wrap}
.c-g{color:#4ADE80}.c-b{color:#38BDF8}.c-y{color:#FBBF24}.c-r{color:#F87171}
.c-m{color:#6B7A8C}.c-w{color:#E6EDF3}.c-p{color:#C084FC}
"""


def html(inner, w, h, extra=""):
    return ("<!doctype html><html><head><meta charset='utf-8'>"
            "<style>%s\nhtml,body{width:%dpx;height:%dpx}\n%s</style></head>"
            "<body>%s</body></html>" % (CSS, w, h, extra, inner))


def bar(url="", light=True):
    bg = "#F0F1F3" if light else "#161B22"
    bd = "#E1E3E6" if light else "#232A33"
    u = ("<div class='url' style='background:%s;border-color:%s;color:%s'>%s</div>"
         % ("#FFF" if light else "#0D1117", bd, "#6B7280" if light else "#7D8590", url)) if url else ""
    return ("<div class='bar' style='background:%s;border-color:%s'>"
            "<div class='dot' style='background:#F35C4E'></div>"
            "<div class='dot' style='background:#F5BE4F'></div>"
            "<div class='dot' style='background:#5FC454'></div>%s</div>" % (bg, bd, u))


def side(items, actif=0, titre="Espace"):
    n = "".join("<div class='navi%s'><div class='ico'></div>%s</div>"
                % (" on" if i == actif else "", t) for i, t in enumerate(items))
    return ("<div class='side'><div style='display:flex;align-items:center;gap:10px;"
            "padding:0 12px 20px'><div class='brandmark'></div>"
            "<div style='font-size:14.5px;font-weight:700;color:#0F172A'>%s</div></div>%s</div>"
            % (titre, n))


def _recadrer(chemin, marge=44, mini=320):
    """Coupe le vide en bas de l'ecran.

    Pourquoi : un canevas fixe laissait jusqu'a 70 % du cadre vide (constate sur
    les terminaux). Or EDITING_SYSTEM interdit une carte de preuve qui laisse
    "la majorite du cadre vertical vide" - c'est ce qui rend le cadre mou.

    Methode : on compare chaque ligne de pixels a la toute derniere ligne. Une
    ligne vide est identique a celle du bas (meme bande laterale, meme fond) ;
    une ligne qui porte du contenu en differe. Ca marche donc aussi sur les
    ecrans a barre laterale, ou un simple test "ligne uniforme" echouerait.
    """
    im = Image.open(chemin).convert("RGB")
    a = np.asarray(im)
    h = a.shape[0]
    ref = a[h - 1]
    fin = h
    for y in range(h - 1, -1, -1):
        if not np.array_equal(a[y], ref):
            fin = y + 1
            break
    fin = max(min(fin + marge, h), mini)
    if fin < h:
        im.crop((0, 0, a.shape[1], fin)).save(chemin, optimize=True)
    return fin


def rendre(nom, sous_dossier, inner, taille, desc, extra="", recadrer=True):
    if CHROME is None:
        print("  ! Chrome introuvable")
        return False
    w, h = taille
    # On rend haut, puis on recadre sur le contenu reel : la hauteur du canevas
    # n'a plus besoin d'etre devinee ecran par ecran.
    h_rendu = max(h, 2400) if recadrer else h
    os.makedirs(TMP, exist_ok=True)
    hp = os.path.join(TMP, nom.replace(".png", ".html"))
    with open(hp, "w", encoding="utf-8") as fh:
        fh.write(html(inner, w, h_rendu, extra))
    d = os.path.join(BROLL, sous_dossier)
    os.makedirs(d, exist_ok=True)
    out = os.path.join(d, nom)
    r = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--force-device-scale-factor=1", "--screenshot=%s" % out,
                        "--window-size=%d,%d" % (w, h_rendu), "--virtual-time-budget=1500",
                        "file:///%s" % hp.replace("\\", "/")],
                       capture_output=True, text=True, timeout=90)
    if not os.path.isfile(out):
        print("  ! echec %s : %s" % (nom, (r.stderr or "")[:160]))
        return False
    hf = _recadrer(out) if recadrer else h
    _faits.append(dict(fichier=nom, dossier=sous_dossier, description=desc,
                       largeur=w, hauteur=int(hf)))
    print("  %-46s %4dx%-5d %s" % (nom, w, hf, desc))
    return True


# ===================================================================== TERMINAL
def bloc_terminal():
    print("\n[02-ecrans-generiques/terminal-code]")
    d = "02-ecrans-generiques/terminal-code"

    def term(nom, corps, desc):
        rendre(nom, d, "<div class='app dark'>%s<div class='term'>%s</div></div>"
               % (bar("", light=False), corps), DESKTOP, desc)

    term("ecran_terminal-agent-execute_01.png",
         "<span class='c-m'>~/projet</span> <span class='c-g'>❯</span> <span class='c-w'>agent run --tache \"relancer les devis en attente\"</span>\n\n"
         "<span class='c-b'>→</span> Lecture du CRM…            <span class='c-g'>✓</span> 43 fiches\n"
         "<span class='c-b'>→</span> Filtre : devis &gt; 7 jours   <span class='c-g'>✓</span> 12 retenues\n"
         "<span class='c-b'>→</span> Rédaction des relances…    <span class='c-g'>✓</span> 12 messages\n"
         "<span class='c-b'>→</span> Envoi programmé 09:00      <span class='c-g'>✓</span>\n\n"
         "<span class='c-g'>✓ Terminé en 11,4 s</span>  <span class='c-m'>· 12 relances · 0 erreur</span>\n"
         "<span class='c-m'>~/projet</span> <span class='c-g'>❯</span> <span style='background:#4ADE80;color:#0C1117'>&nbsp;</span>",
         "un agent qui execute une tache de bout en bout, avec le detail des etapes")

    term("ecran_terminal-installation_02.png",
         "<span class='c-m'>~/projet</span> <span class='c-g'>❯</span> <span class='c-w'>npm install</span>\n\n"
         "<span class='c-m'>⠹</span> Résolution des dépendances\n"
         "<span class='c-g'>✓</span> 284 paquets installés <span class='c-m'>en 6 s</span>\n\n"
         "<span class='c-m'>~/projet</span> <span class='c-g'>❯</span> <span class='c-w'>npm run build</span>\n\n"
         "  <span class='c-b'>vite</span> <span class='c-m'>v6.0.1</span>  construction production\n"
         "  <span class='c-g'>✓</span> 1 247 modules transformés\n"
         "  <span class='c-m'>dist/index.html</span>          <span class='c-y'>1,4 ko</span>\n"
         "  <span class='c-m'>dist/assets/app.js</span>     <span class='c-y'>184,2 ko</span>\n\n"
         "<span class='c-g'>✓ construit en 3,81 s</span>",
         "installation puis build - le geste technique generique")

    term("ecran_terminal-tests-verts_03.png",
         "<span class='c-m'>~/projet</span> <span class='c-g'>❯</span> <span class='c-w'>npm test</span>\n\n"
         "<span style='background:#137333;color:#fff'> PASS </span> <span class='c-m'>src/</span><span class='c-w'>panier.test.js</span>\n"
         "<span style='background:#137333;color:#fff'> PASS </span> <span class='c-m'>src/</span><span class='c-w'>paiement.test.js</span>\n"
         "<span style='background:#137333;color:#fff'> PASS </span> <span class='c-m'>src/</span><span class='c-w'>relance.test.js</span>\n\n"
         "Suites  <span class='c-g'>3 réussies</span><span class='c-m'>, 3 au total</span>\n"
         "Tests   <span class='c-g'>47 réussis</span><span class='c-m'>, 47 au total</span>\n"
         "Durée   <span class='c-w'>2,146 s</span>",
         "suite de tests entierement verte - la preuve que ca marche")

    term("ecran_terminal-erreur_04.png",
         "<span class='c-m'>~/projet</span> <span class='c-g'>❯</span> <span class='c-w'>node traiter.js</span>\n\n"
         "<span class='c-r'>✖ Erreur : limite de contexte dépassée</span>\n"
         "  <span class='c-m'>à</span> traiter.js<span class='c-m'>:42:17</span>\n"
         "  <span class='c-m'>reçu</span> <span class='c-y'>218 400</span> <span class='c-m'>jetons ·</span> <span class='c-m'>maximum</span> <span class='c-y'>200 000</span>\n\n"
         "<span class='c-y'>⚠</span> <span class='c-m'>Piste : découper l'entrée en lots de 50 lignes.</span>",
         "une erreur a l'ecran - le negatif, la ou ca casse")

    term("ecran_terminal-git-log_05.png",
         "<span class='c-m'>~/projet</span> <span class='c-g'>❯</span> <span class='c-w'>git log --oneline -6</span>\n\n"
         "<span class='c-y'>a7f2e91</span> <span class='c-w'>Automatise la relance des devis</span>\n"
         "<span class='c-y'>3b81c04</span> <span class='c-w'>Branche le CRM sur le workflow</span>\n"
         "<span class='c-y'>e94d772</span> <span class='c-w'>Corrige le fuseau horaire des envois</span>\n"
         "<span class='c-y'>1c05af8</span> <span class='c-w'>Ajoute le garde-fou anti-doublon</span>\n"
         "<span class='c-y'>8de3b16</span> <span class='c-w'>Premier jet du connecteur</span>\n"
         "<span class='c-y'>0091ffa</span> <span class='c-w'>Initialisation</span>",
         "historique de commits - le travail qui s'accumule")

    # Editeur de code
    code = ("<div style='display:flex;height:100%'>"
            "<div style='width:230px;background:#0D1117;border-right:1px solid #1C2229;padding:16px 10px;"
            "font-size:13px;color:#7D8590;font-family:Consolas,monospace'>"
            "<div style='color:#E6EDF3;margin-bottom:12px;font-weight:600'>PROJET</div>"
            + "".join("<div style='padding:5px 8px;%s'>%s</div>"
                      % ("background:#1C2229;color:#E6EDF3;border-radius:5px" if s == "relance.js" else "", s)
                      for s in ["index.js", "crm.js", "relance.js", "planning.js", "utils.js"])
            + "</div><div class='term' style='flex:1'>"
              "<span class='c-m'> 1</span>  <span class='c-p'>export async function</span> <span class='c-y'>relancerDevis</span>(<span class='c-b'>options</span>) {\n"
              "<span class='c-m'> 2</span>    <span class='c-p'>const</span> devis = <span class='c-p'>await</span> crm.<span class='c-y'>lister</span>({ statut: <span class='c-g'>'en_attente'</span> });\n"
              "<span class='c-m'> 3</span>    <span class='c-p'>const</span> anciens = devis.<span class='c-y'>filter</span>(d =&gt; d.jours &gt; <span class='c-y'>7</span>);\n"
              "<span class='c-m'> 4</span>\n"
              "<span class='c-m'> 5</span>    <span class='c-p'>for</span> (<span class='c-p'>const</span> d <span class='c-p'>of</span> anciens) {\n"
              "<span class='c-m'> 6</span>      <span class='c-p'>const</span> message = <span class='c-p'>await</span> ia.<span class='c-y'>rediger</span>(d);\n"
              "<span class='c-m'> 7</span>      <span class='c-p'>await</span> envoi.<span class='c-y'>programmer</span>(message, <span class='c-g'>'09:00'</span>);\n"
              "<span class='c-m'> 8</span>    }\n"
              "<span class='c-m'> 9</span>\n"
              "<span class='c-m'>10</span>    <span class='c-p'>return</span> { relances: anciens.length };\n"
              "<span class='c-m'>11</span>  }\n"
              "</div></div>")
    rendre("ecran_editeur-code_06.png", d, "<div class='app dark'>%s%s</div>" % (bar("", light=False), code),
           DESKTOP, "editeur de code, fichier ouvert - le geste de construire")


# ========================================================================= CHAT
def bloc_chat():
    print("\n[02-ecrans-generiques/chat-ia]")
    d = "02-ecrans-generiques/chat-ia"

    def msg(qui, txt, large=False):
        if qui == "u":
            return ("<div style='display:flex;justify-content:flex-end;margin-bottom:20px'>"
                    "<div style='max-width:62%%;background:#F0F2F5;border-radius:16px 16px 4px 16px;"
                    "padding:14px 18px;font-size:15.5px;color:#111827;line-height:1.55'>%s</div></div>" % txt)
        return ("<div style='display:flex;gap:14px;margin-bottom:22px'>"
                "<div class='brandmark' style='width:30px;height:30px;border-radius:9px'></div>"
                "<div style='max-width:%s;font-size:15.5px;color:#1F2937;line-height:1.68'>%s</div></div>"
                % ("88%" if large else "76%", txt))

    def chat(nom, contenu, desc, saisie="Écris ton message…"):
        inner = ("<div class='app'>%s"
                 "<div style='padding:36px 60px 8px'>%s</div>"
                 "<div style='padding:18px 60px 26px;background:#FFF'>"
                 "<div style='border:1px solid #DDE1E6;border-radius:14px;padding:15px 18px;"
                 "font-size:15px;color:#9AA3AD;display:flex;align-items:center;justify-content:space-between'>"
                 "<span>%s</span><div style='width:30px;height:30px;border-radius:8px;background:#111827'></div>"
                 "</div></div></div>" % (bar("assistant.local/conversation"), contenu, saisie))
        rendre(nom, d, inner, DESKTOP, desc)

    chat("ecran_chat-role-contexte_01.png",
         msg("u", "T'es expert en négociation commerciale. Voilà ma situation : un client trouve mon devis trop cher. Sors-moi 3 réponses en une phrase chacune.")
         + msg("a", "<b>1.</b> « Le prix reflète le périmètre — dites-moi lequel on réduit et je réajuste. »<br><br>"
                    "<b>2.</b> « Comparons ce que ça vous coûte de ne rien faire pendant six mois. »<br><br>"
                    "<b>3.</b> « Je peux étaler en trois fois, le montant ne bouge pas. »", large=True),
         "prompt avec role + contexte + format, et une reponse structuree")

    chat("ecran_chat-question-vague_02.png",
         msg("u", "Écris-moi un post")
         + msg("a", "Bien sûr ! Voici un post :<br><br>« L'innovation est au cœur de notre démarche. "
                    "Nous mettons l'humain au centre pour construire ensemble le monde de demain. »"),
         "la demande trop vague et le resultat generique - le negatif a opposer")

    chat("ecran_chat-sources_03.png",
         msg("u", "Donne-moi tes sources, et dis-moi ce que tu ne sais pas.")
         + msg("a", "Sur les 3 chiffres cités :<br><br>"
                    "• Le 1<sup>er</sup> vient d'un rapport public de février — <span style='color:#137333'>vérifiable</span><br>"
                    "• Le 2<sup>e</sup>, je l'ai déduit d'une moyenne — <span style='color:#B54708'>à confirmer</span><br>"
                    "• Le 3<sup>e</sup>, <span style='color:#B42318'>je ne sais pas</span>, je ne l'invente pas.", large=True),
         "une IA qui cite ses sources et admet ce qu'elle ignore")

    chat("ecran_chat-analyse-fichier_04.png",
         "<div style='display:flex;justify-content:flex-end;margin-bottom:16px'>"
         "<div style='background:#FFF;border:1px solid #E1E4E8;border-radius:12px;padding:13px 16px;"
         "display:flex;align-items:center;gap:12px'>"
         "<div style='width:34px;height:34px;border-radius:8px;background:#E7F6EC;display:grid;"
         "place-items:center;font-size:11px;font-weight:700;color:#137333'>CSV</div>"
         "<div><div style='font-size:14px;color:#111827;font-weight:600'>export-ventes-2026.csv</div>"
         "<div style='font-size:12px;color:#6B7280'>2 418 lignes · 184 ko</div></div></div></div>"
         + msg("u", "Où part mon argent ?")
         + msg("a", "Trois postes pèsent <b>71 %</b> de tes dépenses :<br><br>"
                    "• Publicité — 12 480 € <span style='color:#B42318'>(+34 % vs T3)</span><br>"
                    "• Abonnements outils — 4 210 € <span style='color:#6B7280'>(19 outils)</span><br>"
                    "• Sous-traitance — 3 900 €<br><br>"
                    "Sur les abonnements, <b>6 outils</b> n'ont pas servi depuis 60 jours.", large=True),
         "un fichier depose et analyse - montrable, contrairement a une promesse vague")

    chat("ecran_chat-etapes-agent_05.png",
         msg("u", "Trie ma boîte mail et réponds aux demandes de devis.")
         + "<div style='margin-left:44px;margin-bottom:20px'>"
           + "".join("<div style='display:flex;align-items:center;gap:11px;padding:9px 0;font-size:14.5px;color:#374151'>"
                     "<div style='width:19px;height:19px;border-radius:50%%;background:#E7F6EC;color:#137333;"
                     "display:grid;place-items:center;font-size:12px'>✓</div>%s</div>" % s
                     for s in ["Lecture de 128 messages non lus",
                               "Classement en 4 catégories",
                               "9 demandes de devis identifiées",
                               "9 réponses rédigées, en attente de validation"])
           + "</div>"
         + msg("a", "C'est prêt. <b>9 réponses</b> t'attendent en brouillon — je n'envoie rien sans ton feu vert."),
         "un agent qui montre ses etapes une par une")

    # Version telephone
    rendre("ecran_chat-telephone_06.png", d,
           "<div class='app'><div style='height:52px;background:#FFF;border-bottom:1px solid #EEF0F2;"
           "display:flex;align-items:center;justify-content:center;font-size:16px;font-weight:600;"
           "color:#111827'>Assistant</div>"
           "<div style='padding:22px 18px 4px'>"
           + msg("u", "Résume-moi ce contrat en 3 points.")
           + msg("a", "<b>1.</b> Engagement 12 mois, résiliable à 3 mois.<br><br>"
                      "<b>2.</b> Révision tarifaire possible une fois par an.<br><br>"
                      "<b>3.</b> Clause d'exclusivité sur ton secteur.", large=True)
           + msg("u", "Le point 3, c'est risqué pour moi ?")
           + msg("a", "Ça t'interdit de travailler avec un concurrent direct pendant 12 mois. "
                      "Si ton chiffre dépend de ce secteur, c'est le point à renégocier en premier.", large=True)
           + msg("u", "Propose-moi une reformulation.")
           + "</div>"
           "<div style='padding:14px 18px 26px'><div style='border:1px solid #DDE1E6;border-radius:22px;"
           "padding:13px 18px;font-size:15px;color:#9AA3AD'>Message…</div></div></div>",
           PHONE, "la meme conversation, format telephone - plan vertical plein cadre", recadrer=False)


# ==================================================================== DASHBOARD
def bloc_dashboard():
    print("\n[02-ecrans-generiques/dashboard-analytics]")
    d = "02-ecrans-generiques/dashboard-analytics"

    def spark(pts, couleur="#137333", h=54, w=150):
        mx, mn = max(pts), min(pts)
        rg = max(mx - mn, 1e-6)
        pl = " ".join("%.1f,%.1f" % (i * w / (len(pts) - 1), h - (p - mn) / rg * (h - 6) - 3)
                      for i, p in enumerate(pts))
        return ("<svg width='%d' height='%d' style='display:block'>"
                "<polyline points='%s' fill='none' stroke='%s' stroke-width='2.5' "
                "stroke-linecap='round' stroke-linejoin='round'/></svg>" % (w, h, pl, couleur))

    def kpi(lab, val, delta, pts, up=True):
        return ("<div class='card' style='flex:1'><div class='kpil'>%s</div>"
                "<div class='kpi'>%s</div><div class='%s' style='margin:6px 0 12px'>%s</div>%s</div>"
                % (lab, val, "up" if up else "dn", delta, spark(pts, "#137333" if up else "#B42318")))

    def barres(vals, labs, couleur="#111827", h=210):
        mx = max(vals)
        b = "".join(
            "<div style='flex:1;display:flex;flex-direction:column;justify-content:flex-end;"
            "align-items:center;gap:9px'>"
            "<div style='width:64%%;height:%.0fpx;background:%s;border-radius:6px 6px 0 0'></div>"
            "<div style='font-size:12px;color:#98A2B3'>%s</div></div>"
            % (v / mx * h, couleur, l) for v, l in zip(vals, labs))
        return "<div style='display:flex;gap:14px;align-items:flex-end;height:%dpx'>%s</div>" % (h + 26, b)

    rendre("ecran_dashboard-kpi_01.png", d,
           "<div class='app'>%s<div class='body'>%s<div class='main'>"
           "<h1>Vue d'ensemble</h1><div class='sub'>30 derniers jours</div>"
           "<div class='row' style='margin-bottom:22px'>%s%s%s</div>"
           "<div class='card'><div style='font-size:15px;font-weight:600;color:#0F172A;"
           "margin-bottom:18px'>Demandes entrantes par semaine</div>%s</div>"
           "</div></div></div>"
           % (bar("tableau-de-bord.local"),
              side(["Vue d'ensemble", "Contacts", "Campagnes", "Automatisations", "Réglages"], 0, "Espace"),
              kpi("Demandes reçues", "1 284", "+34 % vs période précédente", [12, 18, 15, 24, 22, 31, 38, 44]),
              kpi("Taux de réponse", "94 %", "+11 points", [60, 66, 71, 70, 78, 84, 90, 94]),
              kpi("Temps de réponse", "3 min", "−87 % (était 24 min)", [24, 21, 16, 13, 9, 6, 4, 3], up=False),
              barres([34, 41, 38, 52, 61, 58, 74], ["S1", "S2", "S3", "S4", "S5", "S6", "S7"])),
           DESKTOP, "tableau de bord a 3 KPI et un graphe - le fond de preuve chiffre")

    rendre("ecran_dashboard-courbe-montante_02.png", d,
           "<div class='app'>%s<div class='main' style='padding:44px 56px'>"
           "<h1>Trafic issu des assistants IA</h1><div class='sub'>Mai 2025 → mai 2026</div>"
           "<div class='card' style='padding:30px'>%s"
           "<div style='display:flex;justify-content:space-between;margin-top:14px;font-size:12px;color:#98A2B3'>"
           "<span>mai 2025</span><span>sept.</span><span>janv. 2026</span><span>mai 2026</span></div>"
           "</div>"
           "<div class='row' style='margin-top:22px'>"
           "<div class='card' style='flex:1'><div class='kpil'>Multiplicateur</div><div class='kpi'>× 20</div></div>"
           "<div class='card' style='flex:1'><div class='kpil'>Écart de conversion</div><div class='kpi'>+ 25 %%</div></div>"
           "</div></div></div>"
           % (bar("analytique.local/acquisition"),
              spark([4, 5, 6, 9, 11, 16, 21, 29, 38, 52, 68, 84], "#0B6FA4", h=250, w=1400)),
           DESKTOP, "courbe qui monte fort sur 12 mois - la preuve d'une tendance")

    rendre("ecran_dashboard-entonnoir_03.png", d,
           "<div class='app'>%s<div class='main' style='padding:44px 56px'>"
           "<h1>Entonnoir de conversion</h1><div class='sub'>Ce mois-ci</div><div class='card'>%s</div></div></div>"
           % (bar("tableau-de-bord.local/entonnoir"),
              "".join("<div style='margin-bottom:16px'>"
                      "<div style='display:flex;justify-content:space-between;font-size:14px;"
                      "color:#344054;margin-bottom:7px'><span>%s</span>"
                      "<b style='color:#0F172A'>%s</b></div>"
                      "<div style='height:34px;background:#F2F4F6;border-radius:8px'>"
                      "<div style='height:100%%;width:%d%%;background:%s;border-radius:8px'></div></div></div>"
                      % (l, v, p, c) for l, v, p, c in [
                          ("Vues", "24 800", 100, "#111827"),
                          ("Commentaires", "3 120", 62, "#1F2A37"),
                          ("Messages privés envoyés", "2 940", 48, "#0B6FA4"),
                          ("Guides téléchargés", "1 610", 31, "#0B6FA4"),
                          ("Rendez-vous pris", "184", 12, "#137333")])),
           DESKTOP, "entonnoir en 5 etapes - montre un mecanisme, pas juste un chiffre")

    rendre("ecran_dashboard-avant-apres_04.png", d,
           "<div class='app'>%s<div class='main' style='padding:44px 56px'>"
           "<h1>Avant / après automatisation</h1><div class='sub'>Traitement des demandes entrantes</div>"
           "<div class='row'>"
           "<div class='card' style='flex:1;border-color:#F5C6C2'>"
           "<span class='tag bad'>Avant</span>"
           "<div class='kpi' style='margin:16px 0 4px'>24 min</div>"
           "<div class='kpil'>délai moyen de réponse</div>"
           "<div style='margin-top:20px;font-size:14px;color:#6B7280;line-height:2'>"
           "· tri manuel<br>· réponses réécrites à chaque fois<br>· 3 relances oubliées / semaine</div></div>"
           "<div class='card' style='flex:1;border-color:#B7E0C4'>"
           "<span class='tag ok'>Après</span>"
           "<div class='kpi' style='margin:16px 0 4px'>3 min</div>"
           "<div class='kpil'>délai moyen de réponse</div>"
           "<div style='margin-top:20px;font-size:14px;color:#6B7280;line-height:2'>"
           "· tri automatique<br>· brouillon prêt à valider<br>· relance programmée</div></div>"
           "</div></div></div>" % bar("tableau-de-bord.local/comparaison"),
           DESKTOP, "comparaison avant/apres en rouge et vert - LA paire negatif/positif")


# =================================================================== INBOX / DM
def bloc_inbox():
    print("\n[02-ecrans-generiques/messagerie-inbox] + [08-business-et-preuve]")
    d = "02-ecrans-generiques/messagerie-inbox"

    def mail(exp, obj, apercu, h, lu=True, tag=""):
        return ("<div style='display:flex;gap:14px;padding:15px 12px;border-bottom:1px solid #F2F4F6;"
                "%s'><div class='av' style='background:%s'></div>"
                "<div style='flex:1;min-width:0'>"
                "<div style='display:flex;justify-content:space-between;margin-bottom:3px'>"
                "<span style='font-size:14.5px;color:#111827;font-weight:%s'>%s</span>"
                "<span style='font-size:12px;color:#98A2B3'>%s</span></div>"
                "<div style='font-size:14px;color:#111827;font-weight:%s;margin-bottom:3px'>%s %s</div>"
                "<div style='font-size:13.5px;color:#98A2B3;white-space:nowrap;overflow:hidden;"
                "text-overflow:ellipsis'>%s</div></div></div>"
                % ("background:#FFF" if lu else "background:#F7FAFD",
                   ["#C7D2DE", "#D8CFC4", "#C4D8CE", "#D4C8D8", "#CFD4C4"][hash(exp) % 5],
                   "500" if lu else "700", exp, h, "500" if lu else "700", obj, tag, apercu))

    rendre("ecran_boite-reception_01.png", d,
           "<div class='app'>%s<div class='body'>%s<div class='main' style='padding:20px 26px'>"
           "<h1 style='font-size:22px'>Boîte de réception</h1>"
           "<div class='sub' style='margin-bottom:14px'>128 non lus</div>%s</div></div></div>"
           % (bar("messagerie.local"),
              side(["Réception", "À traiter", "Devis", "Archivé", "Envoyés"], 0, "Courrier"),
              "".join([
                  mail("Camille Roux", "Demande de devis — refonte", "Bonjour, nous cherchons à refondre notre site avant…", "09:12", False, "<span class='tag ok' style='margin-left:6px'>devis</span>"),
                  mail("Yanis B.", "Re: proposition commerciale", "Merci pour l'envoi, je regarde ça cette semaine et…", "08:47", False),
                  mail("Léa Fontaine", "Question sur les délais", "Est-ce qu'on peut tenir la date du 15 ? Le client…", "hier"),
                  mail("Support Outil", "Votre abonnement arrive à échéance", "Votre formule annuelle sera renouvelée le…", "hier", True, "<span class='tag warn' style='margin-left:6px'>facture</span>"),
                  mail("Marc Delaunay", "Retour sur la maquette", "C'est validé de notre côté, tu peux lancer la suite.", "lun."),
                  mail("Newsletter", "5 tendances à suivre ce trimestre", "Au sommaire cette semaine : les agents, la…", "lun."),
              ])),
           DESKTOP, "boite de reception chargee - le probleme avant l'automatisation")

    d2 = "08-business-et-preuve/messages-dm"

    def dm(qui, txt):
        if qui == "m":
            return ("<div style='display:flex;justify-content:flex-end;margin-bottom:11px'>"
                    "<div style='max-width:74%%;background:#111827;color:#FFF;border-radius:20px 20px 5px 20px;"
                    "padding:12px 17px;font-size:15px;line-height:1.5'>%s</div></div>" % txt)
        return ("<div style='display:flex;margin-bottom:11px'>"
                "<div style='max-width:74%%;background:#F0F2F5;color:#111827;border-radius:20px 20px 20px 5px;"
                "padding:12px 17px;font-size:15px;line-height:1.5'>%s</div></div>" % txt)

    rendre("ecran_dm-mot-cle_01.png", d2,
           "<div class='app'><div style='height:60px;background:#FFF;border-bottom:1px solid #EEF0F2;"
           "display:flex;align-items:center;gap:12px;padding:0 18px'>"
           "<div class='av' style='background:#C7D2DE;width:36px;height:36px'></div>"
           "<div><div style='font-size:15.5px;font-weight:600;color:#111827'>nouvelle conversation</div>"
           "<div style='font-size:12.5px;color:#98A2B3'>en ligne</div></div></div>"
           "<div style='padding:20px 16px 4px'>%s</div>"
           "<div style='padding:12px 16px 24px'><div style='border:1px solid #DDE1E6;border-radius:22px;"
           "padding:12px 18px;font-size:15px;color:#9AA3AD'>Message…</div></div></div>"
           % (dm("a", "AGENT")
              + dm("m", "Voilà le guide 👇")
              + dm("m", "Dedans : les 4 tâches à confier en premier, et le modèle de brief à copier.")
              + dm("a", "Merci ! Je regarde ça ce soir 🙏")
              + dm("a", "Question : ça marche aussi si j'ai pas de CRM ?")
              + dm("m", "Oui. Page 4 du guide, il y a la version sans CRM — un tableur suffit.")
              + dm("a", "Parfait, c'est exactement mon cas 👌")
              + dm("m", "Dis-moi ce que tu automatises en premier, ça m'intéresse.")),
           PHONE, "conversation privee declenchee par un mot-cle - le mecanisme du CTA", recadrer=False)

    rendre("ecran_commentaires-mot-cle_02.png", d2,
           "<div class='app'><div style='padding:20px 18px;border-bottom:1px solid #EEF0F2;"
           "font-size:16px;font-weight:600;color:#111827'>Commentaires · 312</div>"
           "<div style='padding:6px 18px 10px'>%s</div></div>"
           % "".join("<div style='display:flex;gap:12px;padding:14px 0;border-bottom:1px solid #F5F6F7'>"
                     "<div class='av' style='background:%s;width:34px;height:34px'></div>"
                     "<div style='flex:1'><div style='font-size:13.5px;color:#98A2B3;margin-bottom:3px'>%s</div>"
                     "<div style='font-size:15.5px;color:#111827;font-weight:%s'>%s</div></div>"
                     "<div style='font-size:12.5px;color:#98A2B3'>%s</div></div>"
                     % (c, n, "700" if t.isupper() else "400", t, q)
                     for n, t, q, c in [
                         ("marie_lgd", "AGENT", "2 min", "#D8CFC4"),
                         ("thomas.b", "AGENT", "4 min", "#C4D8CE"),
                         ("sofia_ml", "trop utile merci", "6 min", "#D4C8D8"),
                         ("k.mercier", "AGENT", "8 min", "#C7D2DE"),
                         ("julien__d", "AGENT", "11 min", "#CFD4C4"),
                         ("nadia.r", "AGENT", "12 min", "#D8CFC4"),
                         ("o.mercier", "AGENT", "14 min", "#C7D2DE"),
                         ("lucie.vd", "AGENT svp", "15 min", "#C4D8CE"),
                         ("hugo_prd", "AGENT", "17 min", "#CFD4C4"),
                         ("claire.mnt", "je teste ça demain", "18 min", "#D4C8D8"),
                         ("samir.k", "AGENT", "21 min", "#D8CFC4"),
                         ("elodie_r", "AGENT", "23 min", "#C7D2DE"),
                         ("mathis.l", "AGENT", "24 min", "#C4D8CE"),
                         ("ines.cds", "AGENT", "26 min", "#CFD4C4"),
                         ("bastien_w", "AGENT", "27 min", "#D4C8D8"),
                         ("amel.z", "franchement bien vu", "29 min", "#D8CFC4"),
                         ("greg.ptt", "AGENT", "31 min", "#C7D2DE"),
                         ("noemie_lb", "AGENT", "33 min", "#C4D8CE"),
                         ("victor.dm", "AGENT", "34 min", "#CFD4C4"),
                     ]),
           PHONE, "fil de commentaires satures du mot-cle - la preuve sociale du CTA", recadrer=False)


# ================================================================ CRM / TABLEUR
def bloc_tableur():
    print("\n[02-ecrans-generiques/tableur-crm] + [08-business-et-preuve]")
    d = "02-ecrans-generiques/tableur-crm"

    lignes = [("Camille Roux", "Refonte site", "4 200 €", "Devis envoyé", "warn", "il y a 9 j"),
              ("Yanis Benali", "Automatisation devis", "6 800 €", "Signé", "ok", "il y a 2 j"),
              ("Léa Fontaine", "Audit process", "2 400 €", "Relancé", "info", "aujourd'hui"),
              ("Marc Delaunay", "Formation équipe", "3 100 €", "Signé", "ok", "il y a 5 j"),
              ("Inès Cardoso", "Intégration CRM", "9 500 €", "Devis envoyé", "warn", "il y a 12 j"),
              ("Paul Ferrand", "Maintenance", "1 200 €", "Perdu", "bad", "il y a 20 j")]

    rendre("ecran_crm-pipeline_01.png", d,
           "<div class='app'>%s<div class='body'>%s<div class='main' style='padding:24px 30px'>"
           "<h1 style='font-size:23px'>Devis en cours</h1>"
           "<div class='sub' style='margin-bottom:16px'>6 dossiers · 27 200 € en jeu</div>"
           "<div class='card' style='padding:0;overflow:hidden'>"
           "<table><thead><tr><th>Client</th><th>Projet</th><th>Montant</th><th>Statut</th><th>Dernier contact</th></tr></thead>"
           "<tbody>%s</tbody></table></div></div></div></div>"
           % (bar("crm.local/devis"),
              side(["Tableau de bord", "Devis", "Clients", "Relances", "Réglages"], 1, "Ventes"),
              "".join("<tr><td style='display:flex;align-items:center;gap:11px'>"
                      "<div class='av' style='background:%s;width:26px;height:26px'></div>%s</td>"
                      "<td>%s</td><td style='font-weight:600;color:#0F172A'>%s</td>"
                      "<td><span class='tag %s'>%s</span></td>"
                      "<td style='color:#98A2B3'>%s</td></tr>"
                      % (["#C7D2DE", "#D8CFC4", "#C4D8CE", "#D4C8D8", "#CFD4C4", "#DDD"][i % 6],
                         n, p, m, c, s, q)
                      for i, (n, p, m, s, c, q) in enumerate(lignes))),
           DESKTOP, "pipeline de devis avec statuts colores - le tableau qu'on automatise")

    rendre("ecran_tableur-donnees_02.png", d,
           "<div class='app'>%s<div class='main' style='padding:0'>"
           "<div style='display:flex;background:#F7F8F9;border-bottom:1px solid #E1E4E8;"
           "font-size:12px;color:#6B7280;font-weight:600'>%s</div>%s</div></div>"
           % (bar("tableur.local/export-ventes"),
              "".join("<div style='%spadding:11px 14px;border-right:1px solid #E8EBEE'>%s</div>"
                      % ("width:56px;text-align:center;" if i == 0 else "flex:1;", c)
                      for i, c in enumerate(["", "A · Date", "B · Client", "C · Produit", "D · Montant", "E · Statut"])),
              "".join("<div style='display:flex;border-bottom:1px solid #F0F2F4;font-size:14px;"
                      "color:#344054;%s'>%s</div>"
                      % ("background:#F7FAFD" if i == 3 else "background:#FFF",
                         "".join("<div style='%spadding:11px 14px;border-right:1px solid #F0F2F4'>%s</div>"
                                 % ("width:56px;text-align:center;color:#98A2B3;background:#F7F8F9;" if j == 0 else "flex:1;", v)
                                 for j, v in enumerate(r)))
                      for i, r in enumerate([
                          ["1", "02/09/2026", "Camille Roux", "Refonte", "4 200 €", "Envoyé"],
                          ["2", "03/09/2026", "Yanis Benali", "Automatisation", "6 800 €", "Signé"],
                          ["3", "05/09/2026", "Léa Fontaine", "Audit", "2 400 €", "Relancé"],
                          ["4", "06/09/2026", "Marc Delaunay", "Formation", "3 100 €", "Signé"],
                          ["5", "08/09/2026", "Inès Cardoso", "Intégration", "9 500 €", "Envoyé"],
                          ["6", "09/09/2026", "Paul Ferrand", "Maintenance", "1 200 €", "Perdu"],
                          ["7", "10/09/2026", "Sonia Ravel", "Refonte", "5 400 €", "Envoyé"],
                      ]))),
           DESKTOP, "tableur brut - la donnee avant traitement, le point de depart")


# ============================================================ VENTES / PAIEMENT
def bloc_ventes():
    print("\n[08-business-et-preuve/notifications-ventes + paiement-facture]")
    d = "08-business-et-preuve/notifications-ventes"

    def notif(titre, sous, montant, t):
        return ("<div style='background:#FFF;border-radius:16px;padding:16px 18px;margin-bottom:12px;"
                "box-shadow:0 6px 22px rgba(16,24,40,.10);display:flex;align-items:center;gap:14px'>"
                "<div style='width:42px;height:42px;border-radius:12px;background:#E7F6EC;color:#137333;"
                "display:grid;place-items:center;font-size:19px'>✓</div>"
                "<div style='flex:1'><div style='font-size:15px;font-weight:700;color:#111827'>%s</div>"
                "<div style='font-size:13px;color:#6B7280'>%s</div></div>"
                "<div style='text-align:right'><div style='font-size:17px;font-weight:700;color:#111827'>%s</div>"
                "<div style='font-size:12px;color:#98A2B3'>%s</div></div></div>" % (titre, sous, montant, t))

    rendre("ecran_notifications-ventes_01.png", d,
           "<div class='app' style='background:#EDEFF2;padding:28px 22px;justify-content:flex-start'>"
           "<div style='font-size:13px;color:#6B7280;margin-bottom:16px;font-weight:600;"
           "text-transform:uppercase;letter-spacing:.7px'>Aujourd'hui</div>%s</div>"
           % (notif("Paiement reçu", "Yanis B. · Automatisation", "6 800 €", "09:41")
              + notif("Paiement reçu", "Marc D. · Formation", "3 100 €", "08:12")
              + notif("Nouveau client", "Sonia R. · Refonte", "5 400 €", "hier")
              + notif("Paiement reçu", "Léa F. · Audit", "2 400 €", "hier")
              + notif("Paiement reçu", "Inès C. · Intégration", "9 500 €", "hier")
              + notif("Nouveau client", "Paul F. · Maintenance", "1 200 €", "lun.")
              + notif("Paiement reçu", "Camille R. · Refonte", "4 200 €", "lun.")
              + notif("Paiement reçu", "Thomas B. · Audit", "2 800 €", "dim.")),
           PHONE, "notifications de paiement empilees - la preuve de resultat", recadrer=False)

    rendre("ecran_facture-payee_02.png", "08-business-et-preuve/paiement-facture",
           "<div class='app'>%s<div class='main' style='padding:50px 70px'>"
           "<div style='display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:36px'>"
           "<div><div style='font-size:12px;color:#98A2B3;text-transform:uppercase;letter-spacing:.8px;"
           "font-weight:600;margin-bottom:8px'>Facture</div>"
           "<div style='font-size:30px;font-weight:700;color:#0F172A;letter-spacing:-.8px'>2026-0184</div></div>"
           "<span class='tag ok' style='font-size:14px;padding:9px 18px'>✓ Payée</span></div>"
           "<div class='card' style='padding:0;overflow:hidden;margin-bottom:24px'>"
           "<table><thead><tr><th>Prestation</th><th style='text-align:right'>Montant</th></tr></thead><tbody>"
           "<tr><td>Automatisation du traitement des devis</td><td style='text-align:right'>5 400 €</td></tr>"
           "<tr><td>Connexion CRM et messagerie</td><td style='text-align:right'>1 400 €</td></tr>"
           "</tbody></table></div>"
           "<div style='display:flex;justify-content:flex-end;gap:60px;font-size:15px;color:#6B7280'>"
           "<div style='text-align:right;line-height:2.1'>Sous-total<br>TVA 20 %%<br>"
           "<b style='color:#0F172A;font-size:19px'>Total</b></div>"
           "<div style='text-align:right;line-height:2.1;color:#0F172A'>6 800 €<br>1 360 €<br>"
           "<b style='font-size:19px'>8 160 €</b></div></div></div></div>" % bar("facturation.local"),
           DESKTOP, "facture marquee payee - la conclusion d'un cycle")


# ==================================================== CALENDRIER / KANBAN
def bloc_planning():
    print("\n[02-ecrans-generiques/calendrier-taches]")
    d = "02-ecrans-generiques/calendrier-taches"

    cols = [("À faire", ["Trier la boîte mail", "Relancer 3 devis", "Préparer le brief"], "#98A2B3"),
            ("Automatisé", ["Tri des messages", "Relance à J+7", "Résumé de réunion",
                            "Réponses types", "Recopie CRM"], "#0B6FA4"),
            ("Terminé", ["Connexion du CRM", "Modèle de relance"], "#137333")]
    rendre("ecran_kanban-automatise_01.png", d,
           "<div class='app'>%s<div class='main' style='padding:34px 40px'>"
           "<h1>Ce qui tourne tout seul</h1><div class='sub'>Semaine du 7 septembre</div>"
           "<div style='display:flex;gap:18px;align-items:flex-start'>%s</div></div></div>"
           % (bar("taches.local/tableau"),
              "".join("<div style='flex:1;background:#F7F8F9;border-radius:14px;padding:15px'>"
                      "<div style='display:flex;align-items:center;gap:8px;margin-bottom:14px'>"
                      "<div style='width:8px;height:8px;border-radius:50%%;background:%s'></div>"
                      "<div style='font-size:13.5px;font-weight:700;color:#344054'>%s</div>"
                      "<div style='font-size:12px;color:#98A2B3'>%d</div></div>%s</div>"
                      % (c, t, len(items),
                         "".join("<div style='background:#FFF;border:1px solid #EBEDEF;border-radius:10px;"
                                 "padding:13px 14px;margin-bottom:9px;font-size:14px;color:#344054;"
                                 "box-shadow:0 1px 2px rgba(16,24,40,.04)'>%s</div>" % i for i in items))
                      for t, items, c in cols)),
           DESKTOP, "tableau kanban avec une colonne 'automatise' bien remplie")

    heures = ["08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00"]
    ev = {1: ("Appel Camille", "#E6F4FD", "#0B6FA4"), 3: ("Atelier équipe", "#E7F6EC", "#137333"),
          6: ("Point client", "#FEF3E2", "#B54708")}
    rendre("ecran_calendrier-semaine_02.png", d,
           "<div class='app'>%s<div class='main' style='padding:30px 36px'>"
           "<h1 style='font-size:23px'>Cette semaine</h1><div class='sub'>7 — 11 septembre</div>"
           "<div class='card' style='padding:0;overflow:hidden'>"
           "<div style='display:flex;border-bottom:1px solid #EBEDEF;background:#FAFAFB'>"
           "<div style='width:78px'></div>%s</div>%s</div></div></div>"
           % (bar("agenda.local"),
              "".join("<div style='flex:1;padding:13px;text-align:center;font-size:13px;"
                      "font-weight:600;color:#344054'>%s</div>" % j
                      for j in ["Lun 7", "Mar 8", "Mer 9", "Jeu 10", "Ven 11"]),
              "".join("<div style='display:flex;border-bottom:1px solid #F2F4F6;height:62px'>"
                      "<div style='width:78px;padding:8px 12px;font-size:12px;color:#98A2B3;"
                      "border-right:1px solid #F2F4F6'>%s</div>%s</div>"
                      % (h, "".join("<div style='flex:1;border-right:1px solid #F5F6F7;padding:4px'>%s</div>"
                                    % (("<div style='background:%s;color:%s;border-radius:7px;padding:7px 9px;"
                                        "font-size:12.5px;font-weight:600;height:100%%'>%s</div>"
                                        % (ev[i][1], ev[i][2], ev[i][0])) if (i in ev and j == i % 5) else "")
                                    for j in range(5)))
                      for i, h in enumerate(heures))),
           DESKTOP, "agenda de la semaine - le temps, la ressource qu'on recupere")


BLOCS = {"terminal": bloc_terminal, "chat": bloc_chat, "dashboard": bloc_dashboard,
         "inbox": bloc_inbox, "tableur": bloc_tableur, "ventes": bloc_ventes,
         "planning": bloc_planning}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None)
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        print("\n".join(BLOCS))
        return 0
    if CHROME is None:
        print("Chrome introuvable — impossible de rendre les ecrans.")
        return 1
    for n in ([x.strip() for x in a.only.split(",")] if a.only else list(BLOCS)):
        if n not in BLOCS:
            print("bloc inconnu : %s" % n)
            return 1
        BLOCS[n]()
    with open(os.path.join(BROLL, "_manifeste-ecrans.json"), "w", encoding="utf-8") as fh:
        json.dump({"genere_par": "tools/generate-ui-screens.py", "ecrans": _faits},
                  fh, ensure_ascii=False, indent=2)
    if os.path.isdir(TMP):
        shutil.rmtree(TMP, ignore_errors=True)   # hygiene : le HTML intermediaire ne survit pas
    print("\n%d ecrans produits" % len(_faits))
    return 0


if __name__ == "__main__":
    sys.exit(main())
