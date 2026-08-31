import sys
from typing import Dict, Any, List
from datetime import datetime
from config import CandidateProfile, SMTPSettings
from services.storage_service import get_all_contacts, get_db_connection
from services.email_sender import send_single_email

def compute_company_analytics() -> Dict[str, Any]:
    """Computes deliverability, bounce rates, and quality score per company."""
    contacts = get_all_contacts()
    
    total_contacts = len(contacts)
    sent_count = sum(1 for c in contacts if c.get("status") == "sent")
    bounced_count = sum(1 for c in contacts if c.get("status") == "bounced")
    approved_count = sum(1 for c in contacts if c.get("status") == "approved")
    pending_count = sum(1 for c in contacts if c.get("status") in ["pending", "failed"])
    
    company_stats: Dict[str, Dict[str, int]] = {}
    
    for c in contacts:
        raw_company = c.get("company", "").strip() or "Société Non Spécifiée"
        # Normalize company name capitalization
        comp = raw_company.title()
        
        if comp not in company_stats:
            company_stats[comp] = {
                "total": 0,
                "sent": 0,
                "bounced": 0,
                "approved": 0,
                "pending": 0
            }
            
        st = c.get("status", "pending")
        company_stats[comp]["total"] += 1
        if st == "sent":
            company_stats[comp]["sent"] += 1
        elif st == "bounced":
            company_stats[comp]["bounced"] += 1
        elif st == "approved":
            company_stats[comp]["approved"] += 1
        else:
            company_stats[comp]["pending"] += 1

    # Format list with realistic deliverability scores
    company_list: List[Dict[str, Any]] = []
    for comp, st in company_stats.items():
        processed = st["sent"] + st["bounced"]
        waiting = st["approved"] + st["pending"]
        
        if processed == 0:
            quality = "Non testée (0 envoyé)"
            quality_color = "#64748b"
            stars = "⏳ En attente"
            success_rate_str = "—"
            success_rate_num = 0.0
            bounce_rate_num = 0.0
        else:
            success_rate_num = round((st["sent"] / processed * 100), 1)
            bounce_rate_num = round((st["bounced"] / processed * 100), 1)
            success_rate_str = f"{success_rate_num}%"
            
            if st["bounced"] == 0:
                if waiting > 0:
                    quality = f"Partiellement envoyée ({st['sent']}/{st['total']})"
                    quality_color = "#0ea5e9"
                    stars = "🟢 0 bounce (En cours)"
                else:
                    quality = "Tous envoyés (0 bounce)"
                    quality_color = "#16a34a"
                    stars = "🟢 0 bounce (Délivré)"
            elif success_rate_num >= 50:
                quality = f"Bounces partiels ({st['bounced']} rejetés)"
                quality_color = "#d97706"
                stars = "⚠️ Alertes Bounces"
            else:
                quality = f"Bounces majeurs ({st['bounced']} rejetés)"
                quality_color = "#dc2626"
                stars = "🔴 Faux Emails"
            
        company_list.append({
            "company": comp,
            "total": st["total"],
            "sent": st["sent"],
            "bounced": st["bounced"],
            "approved": st["approved"],
            "pending": st["pending"],
            "waiting": waiting,
            "processed": processed,
            "success_rate_str": success_rate_str,
            "success_rate": success_rate_num,
            "bounce_rate": bounce_rate_num,
            "quality": quality,
            "quality_color": quality_color,
            "stars": stars
        })
        
    # Sort by processed descending, then total descending
    company_list.sort(key=lambda x: (x["processed"], x["total"]), reverse=True)
    
    total_processed = sent_count + bounced_count
    global_success_rate = round((sent_count / total_processed * 100), 1) if total_processed > 0 else 0.0
    global_bounce_rate = round((bounced_count / total_processed * 100), 1) if total_processed > 0 else 0.0
    
    return {
        "total_contacts": total_contacts,
        "sent_count": sent_count,
        "bounced_count": bounced_count,
        "approved_count": approved_count,
        "pending_count": pending_count,
        "total_processed": total_processed,
        "global_success_rate": global_success_rate,
        "global_bounce_rate": global_bounce_rate,
        "companies": company_list,
        "generated_at": datetime.now().strftime("%d/%m/%Y à %H:%M")
    }

def build_quality_report_html(analytics: Dict[str, Any], profile: CandidateProfile) -> str:
    """Generates a high-end corporate HTML email report with deliverability score per company."""
    
    table_rows = []
    for c in analytics["companies"]:
        if c["processed"] > 0 or c["total"] >= 3:
            table_rows.append(f"""
            <tr style="border-bottom: 1px solid #e2e8f0; font-size: 13.5px;">
                <td style="padding: 10px 12px; font-weight: 600; color: #1e293b;">{c['company']}</td>
                <td style="padding: 10px 12px; text-align: center; color: #475569;">{c['total']}</td>
                <td style="padding: 10px 12px; text-align: center; font-weight: 700; color: #15803d;">{c['sent']}</td>
                <td style="padding: 10px 12px; text-align: center; font-weight: 700; color: #b91c1c;">{c['bounced']}</td>
                <td style="padding: 10px 12px; text-align: center; color: #2563eb;">{c['approved']}</td>
                <td style="padding: 10px 12px; text-align: center;">
                    <span style="display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: 600; background-color: {c['quality_color']}15; color: {c['quality_color']}; border: 1px solid {c['quality_color']}40;">
                        {c['stars']} {c['quality']} ({c['success_rate']}%)
                    </span>
                </td>
            </tr>
            """)
            
    rows_html = "".join(table_rows)
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px; }}
            .container {{ max-width: 780px; margin: 0 auto; background: #ffffff; border-radius: 10px; border: 1px solid #e2e8f0; box-shadow: 0 4px 12px rgba(0,0,0,0.05); overflow: hidden; }}
            .header {{ background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%); color: #ffffff; padding: 24px 30px; }}
            .header h1 {{ margin: 0 0 6px 0; font-size: 22px; font-weight: 700; letter-spacing: -0.3px; }}
            .header p {{ margin: 0; font-size: 13.5px; opacity: 0.85; }}
            .content {{ padding: 26px 30px; }}
            .kpi-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 25px; }}
            .kpi-card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px; text-align: center; }}
            .kpi-val {{ font-size: 22px; font-weight: 800; margin-bottom: 4px; }}
            .kpi-lbl {{ font-size: 12px; color: #64748b; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
            th {{ background-color: #f1f5f9; color: #475569; text-align: left; padding: 10px 12px; font-size: 12px; text-transform: uppercase; font-weight: 700; border-bottom: 2px solid #cbd5e1; }}
            .footer {{ background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 16px 30px; font-size: 12px; color: #64748b; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 Rapport d'Évaluation de la Qualité des Données & Délivrabilité</h1>
                <p>Rapport d'audit généré le <strong>{analytics['generated_at']}</strong> pour <strong>{profile.name}</strong></p>
            </div>
            
            <div class="content">
                <h3 style="margin-top: 0; color: #0f172a; font-size: 16px;">📈 Synthèse Globale de la Base de Contacts :</h3>
                
                <table style="margin-bottom: 25px; width: 100%;">
                    <tr>
                        <td style="padding: 10px; width: 25%;">
                            <div class="kpi-card">
                                <div class="kpi-val" style="color: #0f172a;">{analytics['total_contacts']}</div>
                                <div class="kpi-lbl">Total Contacts</div>
                            </div>
                        </td>
                        <td style="padding: 10px; width: 25%;">
                            <div class="kpi-card">
                                <div class="kpi-val" style="color: #16a34a;">{analytics['sent_count']}</div>
                                <div class="kpi-lbl">🚀 Envoyés & Délivrés</div>
                            </div>
                        </td>
                        <td style="padding: 10px; width: 25%;">
                            <div class="kpi-card">
                                <div class="kpi-val" style="color: #dc2626;">{analytics['bounced_count']}</div>
                                <div class="kpi-lbl">❌ Address Not Found</div>
                            </div>
                        </td>
                        <td style="padding: 10px; width: 25%;">
                            <div class="kpi-card">
                                <div class="kpi-val" style="color: #2563eb;">{analytics['approved_count']}</div>
                                <div class="kpi-lbl">⏳ Prêts à Envoyer</div>
                            </div>
                        </td>
                    </tr>
                </table>

                <div style="background-color: #eff6ff; border-left: 4px solid #3b82f6; padding: 14px 18px; border-radius: 6px; margin-bottom: 25px; font-size: 13.5px; color: #1e3a8a; line-height: 1.5;">
                    <strong>💡 Évaluation du Vendeur de Données :</strong><br/>
                    - Taux de délivrabilité effectif : <strong>{analytics['global_success_rate']}%</strong> de contacts valides.<br/>
                    - Taux de rejet (bounces) : <strong>{analytics['global_bounce_rate']}%</strong> d'adresses introuvables.<br/>
                    - Toutes les adresses rejetées ont été <strong>automatiquement bannies</strong> et purgées pour protéger la réputation de votre compte Gmail.
                </div>

                <h3 style="color: #0f172a; font-size: 16px; margin-bottom: 8px;">🏢 Bilan Détaillé par Entreprise / Société :</h3>
                
                <table>
                    <thead>
                        <tr>
                            <th>Entreprise</th>
                            <th style="text-align: center;">Total</th>
                            <th style="text-align: center;">Délivrés</th>
                            <th style="text-align: center;">Rejetés</th>
                            <th style="text-align: center;">Restants</th>
                            <th style="text-align: center;">Qualité Data</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
            </div>
            
            <div class="footer">
                Rapport de délivrabilité généré automatiquement par <strong>AI Cold Outreach Engine</strong> pour {profile.name} ({profile.email}).
            </div>
        </div>
    </body>
    </html>
    """

from services.email_sender import send_html_email

def send_quality_report_email(smtp: SMTPSettings, profile: CandidateProfile) -> Dict[str, Any]:
    """Computes analytics and sends the HTML quality report directly to candidate's email."""
    if not smtp.app_password:
        return {"success": False, "message": "Mot de passe d'application manquant."}
        
    analytics = compute_company_analytics()
    html_report = build_quality_report_html(analytics, profile)
    
    subject = f"📊 Rapport d'Évaluation Data & Délivrabilité par Société ({analytics['sent_count']} envoyés | {analytics['bounced_count']} rejetés)"
    
    res = send_html_email(
        settings=smtp,
        recipient_email=profile.email,
        subject=subject,
        html_content=html_report
    )
    
    return {
        "success": res.success,
        "message": f"Rapport de qualité envoyé avec succès à {profile.email} !" if res.success else f"Erreur d'envoi du rapport : {res.message}",
        "analytics": analytics
    }
