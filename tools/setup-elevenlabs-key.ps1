$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "Configuration ElevenLabs pour Hyperframes" -ForegroundColor Cyan
Write-Host "La cle reste sur cet ordinateur et ne sera pas affichee." -ForegroundColor DarkGray
Write-Host ""

$secureKey = Read-Host "Colle la cle API ElevenLabs puis appuie sur Entree" -AsSecureString
$keyPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)

try {
    $plainKey = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($keyPointer)

    if ([string]::IsNullOrWhiteSpace($plainKey)) {
        throw "Aucune cle n'a ete saisie."
    }

    [Environment]::SetEnvironmentVariable("ELEVENLABS_API_KEY", $plainKey.Trim(), "User")
}
finally {
    if ($keyPointer -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($keyPointer)
    }
    $plainKey = $null
}

Write-Host ""
Write-Host "Cle enregistree. Tu peux fermer cette fenetre et dire a Codex : cle prete." -ForegroundColor Green
Write-Host ""
Read-Host "Appuie sur Entree pour fermer"
