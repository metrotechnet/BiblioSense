# Script de configuration pour BiblioSense
# Définit les variables d'environnement nécessaires

# Configuration du projet Google Cloud
$PROJECT_ID = "metrotechnet-bibliosense"  # Remplacez par votre vrai ID de projet

Write-Host "Configuration de BiblioSense" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green

# Définir les variables d'environnement pour la session PowerShell actuelle
$env:GCP_PROJECT = $PROJECT_ID
$env:GOOGLE_CLOUD_PROJECT = $PROJECT_ID

Write-Host "Variables d'environnement configurées:" -ForegroundColor Yellow
Write-Host "   GCP_PROJECT = $PROJECT_ID" -ForegroundColor Cyan
Write-Host "   GOOGLE_CLOUD_PROJECT = $PROJECT_ID" -ForegroundColor Cyan

# Vérifier si la clé OpenAI est définie
if ($env:OPENAI_API_KEY) {
    Write-Host "OPENAI_API_KEY est définie" -ForegroundColor Green
} else {
    Write-Host "OPENAI_API_KEY n'est pas définie" -ForegroundColor Yellow
    Write-Host "Veuillez définir votre clé OpenAI:" -ForegroundColor Yellow
    Write-Host 'Exemple: $env:OPENAI_API_KEY = "votre-cle-api"' -ForegroundColor Cyan
}

Write-Host ""
Write-Host "Vous pouvez maintenant lancer l'application:" -ForegroundColor Green
Write-Host "   python app.py" -ForegroundColor Cyan
