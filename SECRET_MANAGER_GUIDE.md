# Configuration Google Secret Manager pour BiblioSense

## Étapes pour configurer Secret Manager

### 1. Créer le secret
Exécutez le script PowerShell (après avoir modifié PROJECT_ID) :
```powershell
.\create-secret.ps1
```

### 2. Vérifier les permissions
Assurez-vous que le service account Cloud Run a les permissions :
```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:YOUR_PROJECT_ID-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### 3. Déployer l'application
```powershell
.\deploy-gcp.ps1
```

## Avantages de Secret Manager

✅ **Sécurité** : Les secrets sont chiffrés et rotationnés automatiquement
✅ **Audit** : Traçabilité complète des accès aux secrets
✅ **Gestion centralisée** : Un seul endroit pour tous vos secrets
✅ **Permissions granulaires** : Contrôle d'accès précis

## Développement local

Pour le développement local, l'application utilisera automatiquement la variable d'environnement `.env` si Secret Manager n'est pas disponible.

## Dépannage

### Erreur "Permission denied"
```bash
gcloud auth application-default login
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="user:your-email@domain.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Erreur "Secret not found"
Vérifiez que le secret existe :
```bash
gcloud secrets list --project=YOUR_PROJECT_ID
```
