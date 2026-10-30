with open('services/llm_service.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_s = "Je suis très motivé par l'idée de rejoindre {company} et je suis sincèrement inspiré par votre vision et les projets que vous portez. Votre parcours et votre expertise dans le domaine sont pour moi une source de motivation."
new_s = "Je suis très motivé par l'idée de rejoindre {company} et je suis sincèrement intéressé par vos projets innovants. L'expertise technique développée au sein de vos équipes représente pour moi un environnement idéal pour mon PFE."

text = text.replace(old_s, new_s)
with open('services/llm_service.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated line 229 in llm_service.py")
