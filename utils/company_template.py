import os

# Map institute names to their logo URLs (used for PDF generation via WeasyPrint)
PARTNER_LOGO_URLS = {
    "IIT Kanpur": "https://raw.githubusercontent.com/aarrraaaavvvvv1/Interview_Questions_Generator_New/refs/heads/main/assets/logos/iitk-accredian-banner.png",
    "IIT Guwahati": "https://raw.githubusercontent.com/aarrraaaavvvvv1/Interview_Questions_Generator_New/refs/heads/main/assets/logos/iitg-accredian-banner.png",
    "Default": "https://accredian.com/wp-content/uploads/2020/12/Accredian-Logo-1.png"
}

# Map institute names to local file paths (used for Word/Docx generation)
# IMPORTANT: These files must exist locally in the 'assets/logos/' directory.
PARTNER_LOGOS = {
    "IIT Kanpur": os.path.join("assets", "logos", "iitk-accredian-banner.png"),
    "IIT Guwahati": os.path.join("assets", "logos", "iitg-accredian-banner.png"),
    "Default": os.path.join("assets", "logos", "accredian-logo.png")
}
