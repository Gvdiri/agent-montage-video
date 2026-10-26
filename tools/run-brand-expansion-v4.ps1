$ErrorActionPreference = "Stop"

$env:ELEVENLABS_API_KEY = [Environment]::GetEnvironmentVariable(
    "ELEVENLABS_API_KEY",
    "User"
)

if ([string]::IsNullOrWhiteSpace($env:ELEVENLABS_API_KEY)) {
    throw "ELEVENLABS_API_KEY is not configured for this user."
}

$nodePath = Join-Path $env:USERPROFILE (
    ".cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe"
)

& $nodePath (Join-Path $PSScriptRoot "generate-brand-expansion-v4.mjs")

if ($null -ne $LASTEXITCODE -and $LASTEXITCODE -ne 0) {
    throw "Brand expansion generation failed with exit code $LASTEXITCODE."
}
