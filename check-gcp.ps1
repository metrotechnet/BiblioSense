# Diagnostic BiblioSense - Connexion GCP
Write-Host "Diagnostic BiblioSense - Connexion GCP" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green

# 1. Vérifier Google Cloud CLI
Write-Host ""
Write-Host "1. Verification Google Cloud CLI..." -ForegroundColor Yellow
try {
    gcloud --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Google Cloud CLI est installe" -ForegroundColor Green
        
        # Configuration actuelle
        Write-Host "Configuration actuelle:" -ForegroundColor Yellow
        gcloud config list
        
        # Projets disponibles
        Write-Host "Projets disponibles:" -ForegroundColor Yellow
        gcloud projects list
        
    } else {
        Write-Host "Google Cloud CLI n'est pas installe" -ForegroundColor Red
    }
} catch {
    Write-Host "Google Cloud CLI n'est pas disponible" -ForegroundColor Red
    Write-Host "Telechargez depuis: https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
}

# 2. Variables d'environnement
Write-Host ""
Write-Host "2. Variables d'environnement..." -ForegroundColor Yellow
$vars = @("GOOGLE_CLOUD_PROJECT", "GCP_PROJECT", "OPENAI_API_KEY")
foreach ($var in $vars) {
    $value = [Environment]::GetEnvironmentVariable($var)
    if ($value) {
        if ($var -eq "OPENAI_API_KEY") {
            Write-Host "$var = sk-***...masque" -ForegroundColor Green
        } else {
            Write-Host "$var = $value" -ForegroundColor Green
        }
    } else {
        Write-Host "$var = (non defini)" -ForegroundColor Red
    }
}

# 3. Test application
Write-Host ""
Write-Host "3. Test application BiblioSense..." -ForegroundColor Yellow
try {
    $result = python -c "from app import GCP_PROJECT_ID; print('Projet:', GCP_PROJECT_ID)" 2>&1
    Write-Host $result -ForegroundColor Cyan
} catch {
    Write-Host "Erreur lors du test de l'application" -ForegroundColor Red
}

Write-Host ""
Write-Host "Diagnostic termine!" -ForegroundColor Green
