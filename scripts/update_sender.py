import sys

def update_sender():
    with open('services/email_sender.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Localized badge
    old_en = 'attachment_notice = "📎 Resume (PDF) & Portfolio Dossier (PDF) attached"'
    new_en = '''badge_text = "🏆 Ex-President RoboThings • Robotics Competition Winner"
        attachment_notice = "📎 Resume (PDF) & Portfolio Dossier (PDF) attached"'''

    old_fr = 'attachment_notice = "📎 CV (PDF) & Dossier Portfolio (PDF) joints"'
    new_fr = '''badge_text = "🏆 Ex-Président RoboThings • Lauréat Compétitions Robotiques"
        attachment_notice = "📎 CV (PDF) & Dossier Portfolio (PDF) joints"'''

    content = content.replace(old_en, new_en)
    content = content.replace(old_fr, new_fr)

    # In HTML template, add badge under school_text
    old_school = '''                                <div style="font-size: 12px; color: #64748b; margin-top: 1px;">
                                    {school_text}
                                </div>'''

    new_school = '''                                <div style="font-size: 12px; color: #64748b; margin-top: 1px;">
                                    {school_text}
                                </div>
                                <div style="font-size: 11.5px; color: #d97706; font-weight: 600; margin-top: 3px;">
                                    {badge_text}
                                </div>'''

    content = content.replace(old_school, new_school)

    with open('services/email_sender.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("services/email_sender.py updated successfully!")

if __name__ == '__main__':
    update_sender()
