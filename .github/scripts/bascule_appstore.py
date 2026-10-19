"""Bascule du site de la bêta TestFlight vers l'App Store, le jour de la sortie d'eSportly.

Ne fait rien tant qu'Apple ne publie pas l'app (recherche publique de l'App Store, identifiant 6819243569).
Ensuite, en une fois et dans les 5 langues : boutons et liens vers l'App Store, FAQ (page et données
structurées), QR code de l'accueil, formulaire « Me prévenir de la sortie » retiré, pages presse,
`version.json` (`storeURL`, lu par l'app et par match.html / tv-equipes.html), phrase sur le compteur de
clics TestFlight retirée de la confidentialité. Une seconde exécution ne change plus rien.

    python3 .github/scripts/bascule_appstore.py            # vérifie la sortie, puis bascule
    python3 .github/scripts/bascule_appstore.py --essai    # montre ce qui changerait, sans rien écrire
    python3 .github/scripts/bascule_appstore.py --forcer   # bascule sans attendre l'App Store
"""
import json
import pathlib
import re
import sys
import urllib.request

APP_ID = "6819243569"
STORE = f"https://apps.apple.com/app/id{APP_ID}"
ROOT = pathlib.Path(__file__).resolve().parents[2]

# Lien de la bêta, qui passe par le compteur de clics du serveur.
BETA_LINK = re.compile(r'https://lmavqchwevcvvneblqld\.supabase\.co/functions/v1/visite\?p=[^"]*?&amp;go=testflight')

# Textes simples, toutes pages confondues (les plus longs d'abord).
TEXTS = [
    # Français
    ("Bêta publique gratuite, eSportly+ offert pendant les tests. Il te faut l'app TestFlight d'Apple (gratuite).",
     "Gratuit sur l'App Store, eSportly+ en option."),
    ("rejoins la bêta pour être prévenu", "télécharge l'app pour être prévenu"),
    ("Tester la bêta sur iPhone", "Télécharger sur l'App Store"),
    ("tester la bêta sur iPhone", "télécharger eSportly sur l'App Store"),
    ("Rejoindre la bêta", "Télécharger l'app"),
    ("En attendant, tu peux ", "Tu peux déjà "),
    ("(gratuit, eSportly+ offert pendant les tests)", "(gratuit)"),
    ("Bêta publique ouverte, sortie sur l’App Store à venir", "Disponible sur l’App Store"),
    ("Pas encore l'app ? Elle arrive sur l'App Store pour iPhone et iPad.", "Pas encore l'app ? Elle est gratuite sur l'App Store."),
    ('alt="QR code du lien de la bêta"', 'alt="QR code d\'eSportly sur l\'App Store"'),
    ("pour ouvrir la bêta.", "pour ouvrir eSportly sur l'App Store."),
    # Anglais
    ("Free public beta, eSportly+ included while testing. You need Apple's free TestFlight app.",
     "Free on the App Store, eSportly+ optional."),
    ("join the beta to get alerts", "get the app to get alerts"),
    ("Try the beta on iPhone", "Download on the App Store"),
    ("try the beta on iPhone", "download eSportly on the App Store"),
    ("Join the beta", "Get the app"),
    ("Meanwhile, you can ", "You can already "),
    ("(free, eSportly+ included while testing)", "(free)"),
    ("Public beta open, App Store launch coming", "Available on the App Store"),
    ('alt="QR code for the beta link"', 'alt="QR code for eSportly on the App Store"'),
    ("to open the beta.", "to open eSportly on the App Store."),
    # Espagnol
    ("Beta pública gratuita, eSportly+ incluido durante las pruebas. Necesitas la app gratuita TestFlight de Apple.",
     "Gratis en el App Store, eSportly+ opcional."),
    ("únete a la beta para recibir avisos", "descarga la app para recibir avisos"),
    ("Prueba la beta en iPhone", "Descárgala en el App Store"),
    ("Únete a la beta", "Descarga la app"),
    ("Beta pública abierta, llegada al App Store próximamente", "Disponible en el App Store"),
    ('alt="Código QR del enlace de la beta"', 'alt="Código QR de eSportly en el App Store"'),
    ("para abrir la beta.", "para abrir eSportly en el App Store."),
    # Allemand
    ("Kostenlose öffentliche Beta, eSportly+ während des Tests inklusive. Du brauchst die kostenlose TestFlight-App von Apple.",
     "Kostenlos im App Store, eSportly+ optional."),
    ("mit der Beta nichts verpassen", "mit der App nichts verpassen"),
    ("Teste die Beta auf dem iPhone", "Im App Store laden"),
    ("Zur Beta", "App laden"),
    ("Öffentliche Beta offen, Start im App Store in Kürze", "Im App Store erhältlich"),
    ('alt="QR-Code des Beta-Links"', 'alt="QR-Code für eSportly im App Store"'),
    ("um die Beta zu öffnen.", "um eSportly im App Store zu öffnen."),
    # Carte des prix d'eSportly+ : « offert pendant la bêta » n'a plus de sens.
    ("<li>Offert pendant la bêta</li>", ""),
    ("<li>Free during the beta</li>", ""),
    ("<li>Gratis durante la beta</li>", ""),
    ("<li>Kostenlos während der Beta</li>", ""),
    ("<li>Grátis durante a beta</li>", ""),
    # Portugais du Brésil
    ("Beta pública gratuita, eSportly+ incluído durante os testes. Você precisa do app gratuito TestFlight, da Apple.",
     "Grátis na App Store, eSportly+ opcional."),
    ("entre na beta para receber alertas", "baixe o app para receber alertas"),
    ("Teste a beta no iPhone", "Baixe na App Store"),
    ("Entrar na beta", "Baixar o app"),
    ("Beta pública aberta, lançamento na App Store em breve", "Disponível na App Store"),
    ('alt="QR code do link da beta"', 'alt="QR code do eSportly na App Store"'),
    ("para abrir a beta.", "para abrir o eSportly na App Store."),
]

# FAQ « Comment tester la bêta ? » : question, réponse de la page, réponse des données structurées.
CONTACT = '<a href="mailto:contact@protojo.fr">contact@protojo.fr</a>'
FAQ = [
    ("Comment tester la bêta", "Comment installer eSportly&nbsp;?",
     f'Télécharge-la gratuitement <a href="{STORE}">sur l\'App Store</a>. eSportly+ est en option. Pour nous dire ce qui ne va pas, écris-nous à {CONTACT}.',
     f"Télécharge-la gratuitement sur l'App Store : {STORE}. eSportly+ est en option."),
    ("How do I try the beta?", "How do I get eSportly?",
     f'Download it for free <a href="{STORE}">on the App Store</a>. eSportly+ is optional. To report a problem, write to {CONTACT}.',
     f"Download it for free on the App Store: {STORE}. eSportly+ is optional."),
    ("¿Cómo pruebo la beta?", "¿Cómo consigo eSportly?",
     f'Descárgala gratis <a href="{STORE}">en el App Store</a>. eSportly+ es opcional. Para avisarnos de un problema, escríbenos a {CONTACT}.',
     f"Descárgala gratis en el App Store: {STORE}. eSportly+ es opcional."),
    ("Wie teste ich die Beta?", "Wie bekomme ich eSportly?",
     f'Lade sie kostenlos <a href="{STORE}">im App Store</a>. eSportly+ ist optional. Um ein Problem zu melden, schreib uns an {CONTACT}.',
     f"Lade sie kostenlos im App Store: {STORE}. eSportly+ ist optional."),
    ("Como testo a beta?", "Como baixo o eSportly?",
     f'Baixe grátis <a href="{STORE}">na App Store</a>. O eSportly+ é opcional. Para relatar um problema, escreva para {CONTACT}.',
     f"Baixe grátis na App Store: {STORE}. O eSportly+ é opcional."),
]

# Phrase de la confidentialité sur le compteur de clics vers TestFlight (le lien ne passe plus par le serveur).
PRIVACY = [
    r" Nous comptons de la même façon les clics vers la bêta TestFlight,[^<]*?sans rien garder sur toi\.",
    r" We count clicks to the TestFlight beta the same way,[^<]*?keeping nothing about you\.",
    r" Contamos de la misma forma los clics hacia la beta de TestFlight,[^<]*?sin guardar nada sobre ti\.",
    r" Auf dieselbe Weise zählen wir Klicks zur TestFlight-Beta,[^<]*?ohne etwas über dich zu speichern\.",
    r" Contamos da mesma forma os cliques para a beta do TestFlight,[^<]*?sem guardar nada sobre você\.",
]


def app_is_live() -> bool:
    url = f"https://itunes.apple.com/lookup?id={APP_ID}&country=fr"
    with urllib.request.urlopen(url, timeout=20) as response:
        return json.load(response).get("resultCount", 0) > 0


def switch(text: str) -> str:
    text = BETA_LINK.sub(STORE, text)
    for old, new in TEXTS:
        text = text.replace(old, new)
    for question, new_question, answer, structured in FAQ:
        q = re.escape(question).replace(r"\ ", r"(?:\s|&nbsp;)*")
        text = re.sub(rf"<dt>{q}(?:&nbsp;| )?\??</dt><dd>.*?</dd>",
                      lambda _: f"<dt>{new_question}</dt><dd>{answer}</dd>", text, flags=re.S)
        text = re.sub(rf'("name":\s*"){q} ?\??("\s*,\s*"acceptedAnswer":\s*\{{\s*"@type":\s*"Answer",\s*"text":\s*")[^"]*(")',
                      lambda m: f"{m.group(1)}{new_question.replace('&nbsp;', ' ')}{m.group(2)}{structured}{m.group(3)}", text)
    # Le QR code de l'accueil et le formulaire « Me prévenir de la sortie » (inutile une fois l'app sortie).
    text = text.replace('src="qr-beta.svg"', 'src="qr-app-store.svg"')
    text = re.sub(r'<form class="signup".*?</form>', "", text, flags=re.S)
    for pattern in PRIVACY:
        text = re.sub(pattern, "", text)
    return text


def main() -> int:
    trial = "--essai" in sys.argv
    if "--forcer" not in sys.argv and not trial and not app_is_live():
        print("eSportly n'est pas encore sur l'App Store : rien à faire.")
        return 0
    changed = 0
    for path in sorted(ROOT.rglob("*.html")):
        if ".git" in path.parts:
            continue
        before = path.read_text()
        after = switch(before)
        if after != before:
            changed += 1
            if not trial:
                path.write_text(after)
    version = ROOT / "version.json"
    info = json.loads(version.read_text())
    if info.get("storeURL") != STORE:
        info["storeURL"] = STORE
        changed += 1
        if not trial:
            version.write_text(json.dumps(info, indent=2) + "\n")
    print(f"{changed} fichier(s) {'à changer' if trial else 'changé(s)'}.")
    # Ce qui reste et qui parle encore de la bêta : à relire à la main.
    # Les notes de version (« 1.1 · bêta publique ») restent : c'est l'historique.
    leftovers = re.compile(r"go=testflight|testflight\.apple|TestFlight|\bbêta\b(?! publique)|\bbeta\b(?! pública)|(?<!public )\bBeta\b(?!, Oktober)", re.I)
    for path in sorted(ROOT.rglob("*.html")):
        if ".git" in path.parts:
            continue
        text = switch(path.read_text()) if trial else path.read_text()
        for match in leftovers.finditer(text):
            snippet = re.sub(r"\s+", " ", text[max(0, match.start() - 60):match.end() + 60])
            print(f"  reste {path.relative_to(ROOT)} : …{snippet}…")
    return 0


if __name__ == "__main__":
    sys.exit(main())
