import os

# Map institute names to their logo URLs (Used for PDF generation via WeasyPrint)
PARTNER_LOGO_URLS = {
    "IIT Kanpur": "https://raw.githubusercontent.com/aarrraaaavvvvv1/logo/refs/heads/main/IITK%3BACCREDIAN%20LOGO.png",
    "IIT Guwahati": "https://raw.githubusercontent.com/aarrraaaavvvvv1/Interview_Questions_Generator_New/refs/heads/main/assets/logos/iitg-accredian-banner.jpg%20.png",
    "Default": "https://accredian.com/wp-content/uploads/2020/12/Accredian-Logo-1.png"
}

# Map institute names to local file paths (Used for Word/Docx generation)
# IMPORTANT: These files must exist locally in the 'assets/logos/' directory for Word generation to work.
PARTNER_LOGOS = {
    # Updated local filename to match the new URL's filename
    "IIT Kanpur": os.path.join("assets", "logos", "IITK;ACCREDIAN LOGO.png"),
    "IIT Guwahati": os.path.join("assets", "logos", "iitg-accredian-banner.jpg .png"),
    "Default": os.path.join("assets", "logos", "accredian-logo.png")
}
