import re

def clean_portfolio_and_links(text: str) -> str:
    if not text:
        return ""
    
    # 1. Traitement ligne par ligne : élimination de toute ligne qui mentionne le portfolio avec un lien ou qui est une invite de lien
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        # Si la ligne contient une URL ou un lien markdown lié au portfolio / site / projets
        if re.search(r'https?://', stripped, re.I):
            # Si la ligne entière sert à introduire le lien ou est un lien
            if any(k in stripped.lower() for k in ["portfolio", "projet", "project", "lien", "link", "site", "consulter", "retrouver", "découvrir", "explorer", "explore", "view", "check"]):
                continue
            # Sinon supprimer l'URL de la ligne
            stripped = re.sub(r'https?://\S+', '', stripped).strip()
            if not stripped or stripped in [":", "-", "•", "–"]:
                continue
        # Si la ligne est un bouton ou lien markdown résiduel [Texte](URL)
        if re.search(r'^\s*\[[^\]]+\]\([^\)]+\)\s*$', stripped):
            continue
        # Si la ligne est un reliquat orphelin type 'Portfolio :', 'Mon portfolio :', 'Lien :'
        if re.search(r'^(?:(?:mon\s+|notre\s+)?(?:portfolio|projets?|site\s+web|lien|link)|check\s+(?:out\s+)?(?:my\s+)?portfolio)\s*[:–-]?\s*$', stripped, re.I):
            continue
        cleaned_lines.append(line)
        
    text = "\n".join(cleaned_lines)
    
    # 2. Supprimer les liens Markdown inline [Texte](URL)
    text = re.sub(r'\[(?:Explorer|Explore|Consulter|Voir|Mon|My)?[^\]]*portfolio[^\]]*\]\([^\)]+\)', '', text, flags=re.I)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # 3. Supprimer toute URL brute restante
    text = re.sub(r'https?://[^\s<>"]+', '', text, flags=re.I)
    
    # 4. Supprimer phrases orphelines résiduelles
    text = re.sub(r'(?:disponible\s+ici|consulter\s+sur|accessible\s+sur|à\s+l[\'’]adresse|at)\s*[:.]?', '', text, flags=re.I)
    text = re.sub(r'(?:mon\s+)?portfolio\s+(?:en\s+ligne|interactif|technique)\s*[:–-]?\s*', '', text, flags=re.I)
    text = re.sub(r'(?:online|interactive)\s+portfolio\s*[:–-]?\s*', '', text, flags=re.I)
    
    # 5. Supprimer lignes orphelines restantes
    final_lines = []
    for l in text.split("\n"):
        s = l.strip()
        if s in [":", "-", "•", "–", ".", ".."]:
            continue
        final_lines.append(l)
        
    text = "\n".join(final_lines)
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    return text

tests = [
    "Vous pouvez consulter mon portfolio sur https://portfolio-mohammed-hsiny-ux7z.vercel.app/",
    "Mon portfolio est disponible ici : https://portfolio-mohammed-hsiny-ux7z.vercel.app/",
    "[Explorer mon Portfolio Interactif ↗](https://portfolio-mohammed-hsiny-ux7z.vercel.app/)",
    "Retrouvez mes projets sur mon portfolio en ligne : https://portfolio-mohammed-hsiny-ux7z.vercel.app/",
    "Portfolio : https://portfolio-mohammed-hsiny-ux7z.vercel.app/",
    "Lien vers mon portfolio : https://portfolio-mohammed-hsiny-ux7z.vercel.app/",
    "Check my portfolio at https://portfolio-mohammed-hsiny-ux7z.vercel.app/",
    "Je vous invite à consulter mon portfolio [ici](https://portfolio-mohammed-hsiny-ux7z.vercel.app/).",
    "Voici mes travaux.\nhttps://portfolio-mohammed-hsiny-ux7z.vercel.app/\nMerci.",
    "Mon CV ainsi que mon dossier de projets sont joints à ce message pour votre consultation."
]

for t in tests:
    print("INPUT :", t)
    res = clean_portfolio_and_links(t)
    print("OUTPUT:", repr(res))
    assert "http" not in res
    assert "vercel.app" not in res
    print("OK!")
    print("-" * 40)

print("ALL TESTS PASSED PERFECTLY!")
