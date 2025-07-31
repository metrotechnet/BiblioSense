# Script pour configurer le projet GCP pour BiblioSense
# Vérifie si le projet existe et le configure si nécessaire

$PROJECT_ID = "bibliosense"
$BILLING_ACCOUNT = ""  # Vous devrez remplir ceci

Write-Host "🔧 Configuration du projet GCP: $PROJECT_ID" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green

# Vérifier si le projet existe
Write-Host "🔍 Vérification de l'existence du projet..." -ForegroundColor Yellow
$projectExists = gcloud projects describe $PROJECT_ID 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Le projet $PROJECT_ID existe" -ForegroundColor Green
} else {
    Write-Host "❌ Le projet $PROJECT_ID n'existe pas" -ForegroundColor Red
    Write-Host "📝 Création du projet..." -ForegroundColor Yellow
    
    # Créer le projet
    gcloud projects create $PROJECT_ID --name="BiblioSense"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Erreur lors de la création du projet" -ForegroundColor Red
        Write-Host "💡 Le nom du projet est peut-être déjà pris. Essayez un autre nom." -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host "✅ Projet créé avec succès" -ForegroundColor Green
    
    # Si vous avez un compte de facturation, décommentez et configurez :
    # Write-Host "💳 Configuration de la facturation..." -ForegroundColor Yellow
    # gcloud billing projects link $PROJECT_ID --billing-account=$BILLING_ACCOUNT
}

# Définir le projet par défaut
Write-Host "🎯 Configuration du projet par défaut..." -ForegroundColor Yellow
gcloud config set project $PROJECT_ID

# Activer les APIs nécessaires
Write-Host "🔌 Activation des APIs nécessaires..." -ForegroundColor Yellow
$apis = @(
    "secretmanager.googleapis.com",
    "cloudbuild.googleapis.com",
    "run.googleapis.com",
    "containerregistry.googleapis.com"
)

foreach ($api in $apis) {
    Write-Host "   Activation de $api..." -ForegroundColor Cyan
    gcloud services enable $api --project=$PROJECT_ID
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ $api activée" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Erreur pour $api" -ForegroundColor Red
    }
}

# Vérifier les permissions
Write-Host "🔐 Vérification des permissions..." -ForegroundColor Yellow
$currentUser = gcloud config get-value account
Write-Host "   Utilisateur actuel: $currentUser" -ForegroundColor Cyan

# Donner les permissions nécessaires
Write-Host "🔑 Attribution des rôles nécessaires..." -ForegroundColor Yellow
$roles = @(
    "roles/secretmanager.admin",
    "roles/cloudbuild.builds.editor",
    "roles/run.admin",
    "roles/storage.admin"
)

foreach ($role in $roles) {
    Write-Host "   Attribution du rôle $role..." -ForegroundColor Cyan
    gcloud projects add-iam-policy-binding $PROJECT_ID --member="user:$currentUser" --role=$role
}

Write-Host "✅ Configuration terminée!" -ForegroundColor Green
Write-Host "🚀 Vous pouvez maintenant utiliser:" -ForegroundColor Cyan
Write-Host "   .\create-secret.ps1" -ForegroundColor White
Write-Host "   .\deploy-gcp.ps1" -ForegroundColor White
