$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv is not installed or is not on PATH. Install it with: winget install --id astral-sh.uv"
}

uv sync
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

function Read-InstallerSetting($Prompt, $Default) {
    $value = Read-Host "$Prompt [$Default]"
    if ([string]::IsNullOrWhiteSpace($value)) { return $Default }
    return $value.Trim()
}

$currentSettings = @{}
$configPath = Join-Path $PSScriptRoot ".env"
if (Test-Path $configPath) {
    foreach ($line in [System.IO.File]::ReadAllLines($configPath)) {
        if ($line -match '^\s*([^#=\s]+)\s*=(.*)$') {
            $currentSettings[$Matches[1]] = $Matches[2].Trim().Trim('"').Trim("'")
        }
    }
}
function Get-InstallerDefault($Name, $Default) {
    $value = $currentSettings[$Name]
    if ([string]::IsNullOrWhiteSpace($value)) { return $Default }
    return $value
}

Write-Host ""
Write-Host "Choose the default interface:"
Write-Host "1. GUI dialogs"
Write-Host "2. CLI only"
$interfaceDefault = if ($currentSettings["SUBTITLE_INTERFACE"] -eq "cli") { "2" } else { "1" }
$interfaceChoice = Read-InstallerSetting "Default interface" $interfaceDefault
$interface = if ($interfaceChoice -eq "2" -or $interfaceChoice -eq "cli") { "cli" } else { "gui" }

Write-Host ""
Write-Host "Choose the default Whisper model:"
Write-Host "1. large-v3 (best quality, more resources)"
Write-Host "2. medium"
Write-Host "3. small"
Write-Host "4. tiny (fastest, lower quality)"
$modelDefault = switch ($currentSettings["SUBTITLE_WHISPER_MODEL"]) {
    "medium" { "2" }
    "small" { "3" }
    "tiny" { "4" }
    default { "1" }
}
$modelChoice = Read-InstallerSetting "Whisper model" $modelDefault
$whisperModel = switch ($modelChoice) {
    "2" { "medium" }
    "3" { "small" }
    "4" { "tiny" }
    default { "large-v3" }
}

Write-Host ""
Write-Host "Choose the default Whisper device:"
Write-Host "1. CPU with int8 (recommended default)"
Write-Host "2. CUDA with float16 (requires a working CUDA setup)"
$deviceDefault = if ($currentSettings["SUBTITLE_WHISPER_DEVICE"] -eq "cuda") { "2" } else { "1" }
$deviceChoice = Read-InstallerSetting "Whisper device" $deviceDefault
$device = if ($deviceChoice -eq "2") { "cuda" } else { "cpu" }
$computeType = if ($device -eq "cuda") { "float16" } else { "int8" }

$cpuThreads = Read-InstallerSetting "Whisper CPU threads" (Get-InstallerDefault "SUBTITLE_WHISPER_CPU_THREADS" "12")
if ($cpuThreads -notmatch '^\d+$' -or [int]$cpuThreads -lt 1) {
    throw "Whisper CPU threads must be a positive integer."
}
$ollamaModel = Read-InstallerSetting "Ollama model" (Get-InstallerDefault "SUBTITLE_OLLAMA_MODEL" "translategemma")
$ollamaUrl = Read-InstallerSetting "Ollama generate URL" (Get-InstallerDefault "SUBTITLE_OLLAMA_URL" "http://localhost:11434/api/generate")

if ($interface -eq "gui") {
    uv run python -c "import tkinter"
    if ($LASTEXITCODE -ne 0) {
        throw "GUI mode needs Tkinter. Install Python with Tk support or rerun setup and choose CLI only."
    }
}

$settings = @(
    "SUBTITLE_INTERFACE=$interface",
    "SUBTITLE_WHISPER_MODEL=$whisperModel",
    "SUBTITLE_WHISPER_DEVICE=$device",
    "SUBTITLE_WHISPER_COMPUTE_TYPE=$computeType",
    "SUBTITLE_WHISPER_CPU_THREADS=$cpuThreads",
    "SUBTITLE_OLLAMA_MODEL=$ollamaModel",
    "SUBTITLE_OLLAMA_URL=$ollamaUrl"
)

$saveSettings = Read-InstallerSetting "Save these choices in .env for future runs? (y/n)" "n"
foreach ($setting in $settings) {
    $name, $value = $setting -split "=", 2
    [Environment]::SetEnvironmentVariable($name, $value, "Process")
}
if ($saveSettings -match "^(y|yes)$") {
    [System.IO.File]::WriteAllLines(
        (Join-Path $PSScriptRoot ".env"),
        $settings,
        [System.Text.UTF8Encoding]::new($false)
    )
    Write-Host ""
    Write-Host "Configuration saved to .env (ignored by Git)."
} else {
    Write-Host ""
    Write-Host "Choices apply only to this setup session; any existing .env was left unchanged."
}

Write-Host ""
Write-Host "Environment ready. Choose a tool to run:"
Write-Host "1. Transcribe audio/video or a YouTube URL"
Write-Host "2. Universal Translator (choose source and target languages)"
Write-Host "Press Enter to finish setup only."
$choice = Read-Host "Choice"

switch ($choice) {
    "1" { uv run subtitle-transcribe; exit $LASTEXITCODE }
    "2" { uv run universaltranslator; exit $LASTEXITCODE }
    default { Write-Host "Setup complete. Run setup.ps1 again or use the commands in README.md." }
}