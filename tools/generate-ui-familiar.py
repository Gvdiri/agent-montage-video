#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Ecrans familiers - Hyperframes.

Demande explicite du createur (2026-09-10) : quand on montre une conversation ou
une notification, il faut que ce soit **familier**. Une bulle de chat generique ne
declenche rien ; une conversation WhatsApp, un message prive Instagram, une
notification de paiement Stripe ou Revolut, ca se reconnait en un quart de seconde
et ca rend le plan credible.

Ce qu'on fait ici : reproduire l'IDIOME VISUEL de la plateforme (couleurs, forme
des bulles, en-tete, accuses de lecture) pour illustrer une situation.
Ce qu'on ne fait pas : fabriquer une **annonce officielle** attribuee a une marque,
ni un ecran de produit presente comme une preuve de ce que fait ce produit. La
difference : ici la marque est le DECOR d'une conversation banale, pas la SOURCE
d'une affirmation.

Format telephone 760x1520, sans recadrage : ces ecrans servent de plan 9:16 plein
cadre.

Usage :
    python tools/generate-ui-familiar.py [--only whatsapp,stripe] [--liste]
"""
import os
import sys
import json
import shutil
import argparse
import subprocess

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
BROLL = os.path.join(ROOT, "asset-library", "broll")
TMP = os.path.join(ROOT, "temp", "_familiar-html")
LOGOS = os.path.join(BROLL, "09-marques-et-logos")

CHROME = None
for c in [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
          r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"]:
    if os.path.isfile(c):
        CHROME = c
        break

W, H = 760, 1520
_faits = []


def logo_svg(slug, couleur=None, taille=22):
    """Injecte un logo officiel de la bibliotheque, redimensionne."""
    for r, _, fs in os.walk(LOGOS):
        f = "logo_%s_couleur.svg" % slug
        if f in fs:
            s = open(os.path.join(r, f), encoding="utf-8").read()
            s = s.replace("<svg ", "<svg width='%d' height='%d' style='display:block' " % (taille, taille), 1)
            if couleur:
                import re
                s = re.sub(r'fill="#[0-9A-Fa-f]{6}"', 'fill="%s"' % couleur, s, count=1)
            return s
    return ""


CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
     -webkit-font-smoothing:antialiased}
.tel{width:100vw;height:100vh;display:flex;flex-direction:column;overflow:hidden}
.statut{height:46px;display:flex;align-items:center;justify-content:space-between;
        padding:0 26px;font-size:15px;font-weight:600;flex-shrink:0}
.statut .droite{display:flex;align-items:center;gap:6px;font-size:13px}
.zone{flex:1;overflow:hidden;display:flex;flex-direction:column}
.zone.bas{justify-content:flex-end}   /* messagerie : les messages s'empilent vers le bas */
.saisie{flex-shrink:0}
.av{border-radius:50%;flex-shrink:0}
"""


def statut(couleur="#111", fond="transparent"):
    return ("<div class='statut' style='color:%s;background:%s'>"
            "<span>9:41</span><span class='droite'>▮▮▮ ᯤ ▮</span></div>" % (couleur, fond))


def rendre(nom, sous_dossier, inner, desc, extra=""):
    os.makedirs(TMP, exist_ok=True)
    hp = os.path.join(TMP, nom.replace(".png", ".html"))
    with open(hp, "w", encoding="utf-8") as fh:
        fh.write("<!doctype html><html><head><meta charset='utf-8'><style>%s\n"
                 "html,body{width:%dpx;height:%dpx}\n%s</style></head><body>%s</body></html>"
                 % (CSS, W, H, extra, inner))
    d = os.path.join(BROLL, sous_dossier)
    os.makedirs(d, exist_ok=True)
    out = os.path.join(d, nom)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=1", "--screenshot=%s" % out,
                    "--window-size=%d,%d" % (W, H), "--virtual-time-budget=1400",
                    "file:///%s" % hp.replace("\\", "/")],
                   capture_output=True, text=True, timeout=90)
    if not os.path.isfile(out):
        print("  ! echec %s" % nom)
        return
    _faits.append(dict(fichier=nom, dossier=sous_dossier, description=desc))
    print("  %-46s %s" % (nom, desc))


# ==================================================================== WHATSAPP
def bloc_whatsapp():
    print("\n[WhatsApp]")
    d = "08-business-et-preuve/messages-dm"
    VERT_ENV = "#D9FDD3"
    FOND = "#EFE7DE"

    def bulle(txt, moi=True, heure="09:41", lu=True):
        if moi:
            return ("<div style='display:flex;justify-content:flex-end;margin-bottom:8px'>"
                    "<div style='max-width:78%%;background:%s;border-radius:9px 2px 9px 9px;"
                    "padding:8px 11px 6px;font-size:16.5px;color:#111B21;line-height:1.35;"
                    "box-shadow:0 1px 1px rgba(11,20,26,.13);position:relative'>%s"
                    "<span style='font-size:11.5px;color:#667781;float:right;margin:6px 0 -2px 10px'>"
                    "%s <span style='color:%s'>✓✓</span></span></div></div>"
                    % (VERT_ENV, txt, heure, "#53BDEB" if lu else "#667781"))
        return ("<div style='display:flex;margin-bottom:8px'>"
                "<div style='max-width:78%%;background:#FFF;border-radius:2px 9px 9px 9px;"
                "padding:8px 11px 6px;font-size:16.5px;color:#111B21;line-height:1.35;"
                "box-shadow:0 1px 1px rgba(11,20,26,.13)'>%s"
                "<span style='font-size:11.5px;color:#667781;float:right;margin:6px 0 -2px 10px'>%s</span>"
                "</div></div>" % (txt, heure))

    entete = ("<div style='background:#008069;color:#FFF;padding:0 14px;height:64px;"
              "display:flex;align-items:center;gap:12px;flex-shrink:0'>"
              "<span style='font-size:22px'>‹</span>"
              "<div class='av' style='width:40px;height:40px;background:#C7D2DE'></div>"
              "<div style='flex:1'><div style='font-size:17px;font-weight:600'>Camille — Fleuriste</div>"
              "<div style='font-size:12.5px;opacity:.85'>en ligne</div></div>"
              "<span style='font-size:19px;opacity:.9'>⋮</span></div>")

    saisie = ("<div class='saisie' style='background:%s;padding:8px 10px 26px;display:flex;gap:8px;"
              "align-items:center'><div style='flex:1;background:#FFF;border-radius:22px;padding:11px 16px;"
              "font-size:16px;color:#8696A0'>Message</div>"
              "<div style='width:46px;height:46px;border-radius:50%%;background:#008069;display:grid;"
              "place-items:center;color:#FFF;font-size:19px'>➤</div></div>" % FOND)

    rendre("familier_whatsapp-demande-client.png", d,
           "<div class='tel' style='background:%s'>%s%s"
           "<div class='zone bas' style='padding:14px 12px 6px'>"
           "<div style='text-align:center;margin-bottom:14px'><span style='background:#E2F7CB;"
           "color:#54656F;font-size:12.5px;padding:5px 12px;border-radius:8px'>AUJOURD'HUI</span></div>"
           "%s</div>%s</div>"
           % (FOND, statut("#FFF", "#008069"), entete,
              bulle("Bonjour, vous livrez sur Lyon 6 samedi matin ?", moi=False, heure="09:38")
              + bulle("Bonjour Camille 👋 Oui, créneau 9h-12h dispo samedi.", heure="09:38")
              + bulle("Il me faudrait 40 pièces pour un mariage.", moi=False, heure="09:39")
              + bulle("Noté. Je vous envoie le devis dans la minute.", heure="09:40")
              + bulle("Devis #2026-0184 — 40 compositions — 1 240 €", heure="09:41")
              + bulle("Parfait, je valide 🙏", moi=False, heure="09:41")
              + bulle("Vous pouvez livrer avant 10h ?", moi=False, heure="09:42")
              + bulle("Oui, 9h30 sur place. Je vous mets le créneau.", heure="09:42")
              + bulle("Top. Merci pour la réactivité 👌", moi=False, heure="09:43")
              + bulle("Avec plaisir. Bon mariage à vos clients 🌿", heure="09:43"),
              saisie),
           "conversation WhatsApp : une demande client traitee en 3 minutes")

    rendre("familier_whatsapp-relance-auto.png", d,
           "<div class='tel' style='background:%s'>%s%s"
           "<div class='zone bas' style='padding:14px 12px 6px'>"
           "<div style='text-align:center;margin-bottom:14px'><span style='background:#E2F7CB;"
           "color:#54656F;font-size:12.5px;padding:5px 12px;border-radius:8px'>HIER</span></div>%s</div>%s</div>"
           % (FOND, statut("#FFF", "#008069"),
              entete.replace("Camille — Fleuriste", "Yanis — Menuiserie").replace("en ligne", "vu à 08:12"),
              bulle("Devis envoyé le 2 septembre 👆", heure="08:00")
              + bulle("Bonjour Yanis, je reviens vers vous : le devis tient jusqu'à vendredi.", heure="08:00")
              + bulle("Ah oui pardon, ça m'était sorti de la tête.", moi=False, heure="08:11")
              + bulle("On part dessus. Vous m'envoyez le bon de commande ?", moi=False, heure="08:12")
              + bulle("C'est parti 👌", heure="08:12")
              + bulle("Bon de commande #BC-0912 envoyé par mail.", heure="08:13")
              + bulle("Reçu. Je signe et je vous renvoie ce matin.", moi=False, heure="08:15")
              + bulle("Nickel. Démarrage possible dès lundi.", heure="08:15")
              + bulle("Ça marche. À lundi 👍", moi=False, heure="08:16"),
              saisie),
           "relance automatique a J+7 qui debloque un devis oublie")


# =================================================================== INSTAGRAM
def bloc_instagram():
    print("\n[Instagram]")
    d = "08-business-et-preuve/messages-dm"
    BLEU = "#3797F0"

    def bulle(txt, moi=True):
        if moi:
            return ("<div style='display:flex;justify-content:flex-end;margin-bottom:7px'>"
                    "<div style='max-width:74%%;background:%s;color:#FFF;border-radius:22px;"
                    "padding:11px 16px;font-size:16px;line-height:1.4'>%s</div></div>" % (BLEU, txt))
        return ("<div style='display:flex;gap:9px;margin-bottom:7px;align-items:flex-end'>"
                "<div class='av' style='width:26px;height:26px;background:#D8CFC4'></div>"
                "<div style='max-width:74%%;background:#EFEFEF;color:#000;border-radius:22px;"
                "padding:11px 16px;font-size:16px;line-height:1.4'>%s</div></div>" % txt)

    entete = ("<div style='padding:0 14px;height:60px;display:flex;align-items:center;gap:12px;"
              "border-bottom:1px solid #DBDBDB;flex-shrink:0;background:#FFF'>"
              "<span style='font-size:24px'>‹</span>"
              "<div class='av' style='width:34px;height:34px;background:#C4D8CE'></div>"
              "<div style='flex:1'><div style='font-size:16px;font-weight:600'>marie_lgd</div>"
              "<div style='font-size:12.5px;color:#8E8E8E'>Marie Legrand</div></div>"
              "%s</div>" % logo_svg("instagram", taille=24))

    rendre("familier_instagram-dm-motcle.png", d,
           "<div class='tel' style='background:#FFF'>%s%s<div class='zone bas' style='padding:16px 14px 6px'>%s</div>"
           "<div class='saisie' style='padding:10px 14px 26px'>"
           "<div style='border:1px solid #DBDBDB;border-radius:22px;padding:12px 18px;font-size:16px;"
           "color:#8E8E8E'>Envoyer un message…</div></div></div>"
           % (statut("#000", "#FFF"), entete,
              bulle("AGENT", moi=False)
              + bulle("Salut Marie 👋 Voilà le guide 👇")
              + "<div style='display:flex;justify-content:flex-end;margin-bottom:7px'>"
                "<div style='background:#FAFAFA;border:1px solid #DBDBDB;border-radius:16px;"
                "padding:14px;width:74%;display:flex;gap:12px;align-items:center'>"
                "<div style='width:44px;height:44px;border-radius:10px;background:#111827;color:#FFF;"
                "display:grid;place-items:center;font-size:11px;font-weight:700'>PDF</div>"
                "<div><div style='font-size:14.5px;font-weight:600;color:#000'>Guide-AGENT.pdf</div>"
                "<div style='font-size:12.5px;color:#8E8E8E'>12 pages · 1,4 Mo</div></div></div></div>"
              + bulle("Dedans : les 4 tâches à confier en premier, et le brief à copier-coller.")
              + bulle("Merci !! Je regarde ça ce soir 🙏", moi=False)
              + bulle("Ça marche aussi sans CRM ?", moi=False)
              + bulle("Oui — page 4, la version tableur. C'est le cas le plus courant.")
              + bulle("Parfait, c'est exactement ma situation 👌", moi=False)
              + bulle("Par contre je code pas du tout, c'est bloquant ?", moi=False)
              + bulle("Non. Tout ce qu'il y a dedans se branche sans une ligne de code.")
              + bulle("Le plus dur c'est de choisir quoi automatiser en premier — d'où la page 2.")
              + bulle("Ok je m'y mets ce week-end. Merci vraiment 🙏", moi=False)
              + bulle("Avec plaisir. Dis-moi ce que tu automatises en premier, ça m'intéresse.")),
           "message prive Instagram declenche par le mot-cle : le mecanisme du CTA")

    # Commentaires Instagram
    def commentaire(pseudo, txt, t, likes, coul):
        return ("<div style='display:flex;gap:12px;padding:11px 0'>"
                "<div class='av' style='width:34px;height:34px;background:%s'></div>"
                "<div style='flex:1'><div style='font-size:14.5px;line-height:1.42;color:#000'>"
                "<b>%s</b> %s</div>"
                "<div style='font-size:12.5px;color:#8E8E8E;margin-top:5px'>%s · %s J'aime · Répondre</div>"
                "</div><div style='color:#8E8E8E;font-size:13px;padding-top:4px'>♡</div></div>"
                % (coul, pseudo, txt, t, likes))

    coms = [("marie_lgd", "<b>AGENT</b>", "2 min", "3", "#D8CFC4"),
            ("thomas.b", "<b>AGENT</b>", "4 min", "1", "#C4D8CE"),
            ("sofia_ml", "trop utile merci 🙏", "6 min", "12", "#D4C8D8"),
            ("k.mercier", "<b>AGENT</b>", "8 min", "0", "#C7D2DE"),
            ("julien__d", "<b>AGENT</b>", "11 min", "2", "#CFD4C4"),
            ("nadia.r", "<b>AGENT</b> svp", "12 min", "0", "#D8CFC4"),
            ("o.mercier", "<b>AGENT</b>", "14 min", "1", "#C7D2DE"),
            ("lucie.vd", "je teste ça demain", "15 min", "8", "#C4D8CE"),
            ("hugo_prd", "<b>AGENT</b>", "17 min", "0", "#CFD4C4"),
            ("claire.mnt", "<b>AGENT</b>", "18 min", "0", "#D4C8D8"),
            ("samir.k", "<b>AGENT</b>", "21 min", "4", "#D8CFC4"),
            ("elodie_r", "<b>AGENT</b>", "23 min", "0", "#C7D2DE")]

    rendre("familier_instagram-commentaires.png", d,
           "<div class='tel' style='background:#FFF'>%s"
           "<div style='padding:16px;border-bottom:1px solid #DBDBDB;text-align:center;"
           "font-size:16px;font-weight:600;position:relative'>Commentaires"
           "<span style='position:absolute;left:16px;top:14px;font-size:22px;font-weight:400'>‹</span></div>"
           "<div class='zone' style='padding:4px 16px'>%s</div>"
           "<div class='saisie' style='padding:12px 16px 26px;border-top:1px solid #EFEFEF;"
           "display:flex;gap:12px;align-items:center'>"
           "<div class='av' style='width:32px;height:32px;background:#C7D2DE'></div>"
           "<div style='flex:1;font-size:15px;color:#8E8E8E'>Ajouter un commentaire…</div></div></div>"
           % (statut("#000", "#FFF"), "".join(commentaire(*c) for c in coms)),
           "fil de commentaires Instagram sature du mot-cle - preuve sociale du CTA")


# ==================================================================== DISCORD
def bloc_discord():
    print("\n[Discord]")
    d = "02-ecrans-generiques/chat-ia"

    def msg(auteur, coul, heure, txt, av):
        return ("<div style='display:flex;gap:14px;padding:9px 16px'>"
                "<div class='av' style='width:40px;height:40px;background:%s'></div>"
                "<div style='flex:1'>"
                "<div style='margin-bottom:3px'><span style='color:%s;font-weight:600;font-size:15.5px'>%s</span>"
                "<span style='color:#949BA4;font-size:12px;margin-left:9px'>%s</span></div>"
                "<div style='color:#DBDEE1;font-size:15.5px;line-height:1.45'>%s</div></div></div>"
                % (av, coul, auteur, heure, txt))

    canaux = "".join("<div style='color:%s;font-size:15px;padding:6px 9px;border-radius:5px;%s'>"
                     "<span style='opacity:.5;margin-right:6px'>#</span>%s</div>"
                     % ("#F2F3F5" if a else "#949BA4",
                        "background:#404249" if a else "", n)
                     for n, a in [("annonces", False), ("automatisations", True),
                                  ("aide-n8n", False), ("veille-ia", False),
                                  ("vos-workflows", False), ("hors-sujet", False)])

    rendre("familier_discord-communaute.png", d,
           "<div class='tel' style='background:#313338'>%s"
           "<div style='display:flex;flex:1;overflow:hidden'>"
           "<div style='width:190px;background:#2B2D31;padding:12px 8px;flex-shrink:0'>"
           "<div style='color:#F2F3F5;font-weight:700;font-size:15px;padding:6px 9px 14px'>Communauté IA</div>"
           "%s</div>"
           "<div style='flex:1;display:flex;flex-direction:column;overflow:hidden'>"
           "<div style='height:48px;border-bottom:1px solid #26282C;display:flex;align-items:center;"
           "padding:0 16px;color:#F2F3F5;font-weight:600;font-size:15.5px'>"
           "<span style='opacity:.4;margin-right:7px;font-size:19px'>#</span>automatisations</div>"
           "<div style='flex:1;padding:10px 0;display:flex;flex-direction:column;justify-content:flex-end'>%s</div>"
           "<div style='padding:10px 16px 26px'><div style='background:#383A40;border-radius:8px;"
           "padding:12px 16px;color:#6D6F78;font-size:15px'>Envoyer un message dans #automatisations</div>"
           "</div></div></div></div>"
           % (statut("#F2F3F5", "#2B2D31"), canaux,
              msg("Yanis", "#5865F2", "09:12", "Quelqu'un a déjà branché n8n sur une boîte Gmail pro ?", "#D8CFC4")
              + msg("Marie", "#3BA55D", "09:14", "Oui, j'ai le workflow. Tu veux le JSON ?", "#C4D8CE")
              + msg("Yanis", "#5865F2", "09:14", "Carrément 🙏", "#D8CFC4")
              + msg("Marie", "#3BA55D", "09:15", "Je te l'envoie. 3 nœuds : trigger, filtre, réponse.", "#C4D8CE")
              + msg("Thomas", "#EB459E", "09:21", "Ça tourne chez moi depuis 2 mois, zéro incident.", "#CFD4C4")),
           "serveur Discord d'une communaute - l'entraide autour de l'outil")


# ============================================================== NOTIFICATIONS
def bloc_notifications():
    print("\n[Notifications]")
    d = "08-business-et-preuve/notifications-ventes"

    def notif(icone, appli, titre, corps, t, fond="#FFF"):
        return ("<div style='background:rgba(255,255,255,.94);border-radius:20px;padding:14px 16px;"
                "margin-bottom:10px;display:flex;gap:13px;align-items:flex-start;"
                "box-shadow:0 4px 18px rgba(0,0,0,.10)'>"
                "<div style='width:40px;height:40px;border-radius:10px;background:%s;display:grid;"
                "place-items:center;flex-shrink:0'>%s</div>"
                "<div style='flex:1;min-width:0'>"
                "<div style='display:flex;justify-content:space-between;align-items:baseline'>"
                "<span style='font-size:13.5px;font-weight:600;color:#3C3C43;opacity:.75'>%s</span>"
                "<span style='font-size:12.5px;color:#3C3C43;opacity:.5'>%s</span></div>"
                "<div style='font-size:15.5px;font-weight:600;color:#000;margin-top:2px'>%s</div>"
                "<div style='font-size:15px;color:#000;opacity:.82;line-height:1.35'>%s</div>"
                "</div></div>" % (fond, icone, appli, t, titre, corps))

    fond_ecran = ("background:linear-gradient(160deg,#2C3E50 0%,#4A6076 42%,#8397AB 100%)")

    rendre("familier_notifications-paiements.png", d,
           "<div class='tel' style='%s'>%s"
           "<div style='text-align:center;color:#FFF;padding:22px 0 30px'>"
           "<div style='font-size:17px;opacity:.9;font-weight:500'>mardi 10 septembre</div>"
           "<div style='font-size:82px;font-weight:300;letter-spacing:-2px;line-height:1.05'>9:41</div></div>"
           "<div class='zone' style='padding:0 12px'>%s</div></div>"
           % (fond_ecran, statut("#FFF"),
              notif(logo_svg("stripe", "#FFFFFF", 22), "STRIPE", "Paiement reçu — 6 800,00 €",
                    "Yanis B. · Automatisation devis", "à l'instant", "#635BFF")
              + notif(logo_svg("stripe", "#FFFFFF", 22), "STRIPE", "Paiement reçu — 3 100,00 €",
                      "Marc D. · Formation équipe", "il y a 12 min", "#635BFF")
              + notif(logo_svg("shopify", "#FFFFFF", 22), "SHOPIFY", "Nouvelle commande #1284",
                      "2 articles · 148,00 €", "il y a 24 min", "#5E8E3E")
              + notif(logo_svg("stripe", "#FFFFFF", 22), "STRIPE", "Paiement reçu — 2 400,00 €",
                      "Léa F. · Audit process", "il y a 1 h", "#635BFF")
              + notif("<span style='color:#FFF;font-size:19px'>✉</span>", "MAIL",
                      "Camille Roux", "Demande de devis — refonte du site", "il y a 2 h", "#2F7CF6")),
           "ecran verrouille sature de notifications de paiement - la preuve de resultat")

    rendre("familier_notifications-travail-nuit.png", d,
           "<div class='tel' style='%s'>%s"
           "<div style='text-align:center;color:#FFF;padding:22px 0 30px'>"
           "<div style='font-size:17px;opacity:.9;font-weight:500'>mercredi 11 septembre</div>"
           "<div style='font-size:82px;font-weight:300;letter-spacing:-2px;line-height:1.05'>3:12</div></div>"
           "<div class='zone' style='padding:0 12px'>%s</div></div>"
           % ("background:linear-gradient(165deg,#0B1016 0%,#161F2A 50%,#243244 100%)", statut("#FFF"),
              notif(logo_svg("n8n", "#FFFFFF", 22), "N8N", "Workflow terminé",
                    "12 relances envoyées · 0 erreur", "à l'instant", "#EA4B71")
              + notif(logo_svg("n8n", "#FFFFFF", 22), "N8N", "Workflow terminé",
                      "128 messages triés en 4 catégories", "il y a 8 min", "#EA4B71")
              + notif(logo_svg("gmail", "#FFFFFF", 22), "GMAIL", "9 brouillons prêts",
                      "En attente de ta validation", "il y a 9 min", "#D93025")
              + notif(logo_svg("slack", "#FFFFFF", 22), "SLACK", "#automatisations",
                      "Le rapport de nuit est dispo", "il y a 22 min", "#4A154B")),
           "3 h du matin : le systeme travaille pendant que tu dors")


# ======================================================================= MAIL
def bloc_mail():
    print("\n[Gmail]")
    d = "02-ecrans-generiques/messagerie-inbox"

    def ligne(exp, obj, apercu, h, lu, tag=""):
        return ("<div style='display:flex;gap:14px;padding:13px 16px;border-bottom:1px solid #F1F3F4;"
                "background:%s'>"
                "<div class='av' style='width:38px;height:38px;background:%s;color:#FFF;display:grid;"
                "place-items:center;font-size:16px;font-weight:600'>%s</div>"
                "<div style='flex:1;min-width:0'>"
                "<div style='display:flex;justify-content:space-between'>"
                "<span style='font-size:15px;color:#202124;font-weight:%s'>%s</span>"
                "<span style='font-size:12.5px;color:%s;font-weight:%s'>%s</span></div>"
                "<div style='font-size:14.5px;color:#202124;font-weight:%s;margin:2px 0'>%s%s</div>"
                "<div style='font-size:13.5px;color:#5F6368;white-space:nowrap;overflow:hidden;"
                "text-overflow:ellipsis'>%s</div></div></div>"
                % ("#FFF" if lu else "#F2F6FC",
                   ["#5B7C99", "#8E7B62", "#5F8C73", "#8A6E8F", "#7C8659"][hash(exp) % 5],
                   exp[0].upper(), "400" if lu else "700", exp,
                   "#5F6368" if lu else "#1A73E8", "400" if lu else "700", h,
                   "400" if lu else "700", obj, tag, apercu))

    rendre("familier_gmail-boite-reception.png", d,
           "<div class='tel' style='background:#FFF'>%s"
           "<div style='padding:12px 16px;display:flex;align-items:center;gap:14px;flex-shrink:0'>"
           "<span style='font-size:22px;color:#5F6368'>☰</span>"
           "<div style='flex:1;background:#F1F3F4;border-radius:24px;padding:11px 18px;"
           "font-size:15px;color:#5F6368'>Rechercher dans les messages</div>"
           "<div class='av' style='width:32px;height:32px;background:#C7D2DE'></div></div>"
           "<div style='padding:6px 16px 10px;font-size:13px;color:#5F6368;font-weight:600'>"
           "BOÎTE DE RÉCEPTION · 128 non lus</div>"
           "<div class='zone'>%s</div></div>"
           % (statut("#202124", "#FFF"),
              ligne("Camille Roux", "Demande de devis — refonte", "Bonjour, nous cherchons à refondre notre site avant…", "09:12", False,
                    " <span style='background:#E6F4EA;color:#137333;font-size:11px;padding:2px 7px;border-radius:4px;margin-left:6px'>devis</span>")
              + ligne("Yanis Benali", "Re: proposition commerciale", "Merci pour l'envoi, je regarde ça cette semaine…", "08:47", False)
              + ligne("Léa Fontaine", "Question sur les délais", "Est-ce qu'on peut tenir la date du 15 ?", "08:02", False)
              + ligne("Marc Delaunay", "Retour sur la maquette", "C'est validé de notre côté, tu peux lancer.", "hier", True)
              + ligne("Inès Cardoso", "Relance — intégration CRM", "Je me permets de revenir vers vous concernant…", "hier", False,
                      " <span style='background:#FEF7E0;color:#B06000;font-size:11px;padding:2px 7px;border-radius:4px;margin-left:6px'>relance</span>")
              + ligne("Paul Ferrand", "Facture septembre", "Vous trouverez ci-joint la facture du mois…", "lun.", True)
              + ligne("Sonia Ravel", "Devis accepté ✅", "C'est bon pour nous, on signe. Quand peut-on…", "lun.", False)
              + ligne("Newsletter IA", "5 outils à tester ce mois-ci", "Au sommaire : les agents, la mémoire longue…", "dim.", True)),
           "boite Gmail chargee - le probleme avant l'automatisation")


BLOCS = {"whatsapp": bloc_whatsapp, "instagram": bloc_instagram, "discord": bloc_discord,
         "notifications": bloc_notifications, "mail": bloc_mail}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None)
    ap.add_argument("--liste", action="store_true")
    a = ap.parse_args()
    if a.liste:
        print("\n".join(BLOCS))
        return 0
    if CHROME is None:
        print("Chrome introuvable")
        return 1
    for n in ([x.strip() for x in a.only.split(",")] if a.only else list(BLOCS)):
        if n not in BLOCS:
            print("bloc inconnu : %s" % n)
            return 1
        BLOCS[n]()
    with open(os.path.join(BROLL, "_manifeste-familier.json"), "w", encoding="utf-8") as fh:
        json.dump({"genere_par": "tools/generate-ui-familiar.py",
                   "principe": "idiome visuel de la plateforme pour illustrer une situation ; "
                               "jamais une annonce officielle attribuee a une marque",
                   "ecrans": _faits}, fh, ensure_ascii=False, indent=2)
    shutil.rmtree(TMP, ignore_errors=True)
    print("\n%d ecrans familiers produits" % len(_faits))
    return 0


if __name__ == "__main__":
    sys.exit(main())
