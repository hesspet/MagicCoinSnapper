$ErrorActionPreference = "Stop"

# Pfade
$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$projectFile = Join-Path $projectRoot "MagicCoinSnapper.csproj"
$publishDir  = Join-Path $projectRoot "bin\IisExpress"
$publishWwwroot = Join-Path $publishDir "wwwroot"

# IIS Express
$iisExe = "${env:ProgramFiles}\IIS Express\iisexpress.exe"
$vsConfigSrc = Join-Path $projectRoot ".vs\MagicCoinSnapper\config\applicationhost.config"
$workConfig  = Join-Path $publishDir "applicationhost.test.config"

# Ports (ueber launchSettings.json IISExpress-Profil)
$httpPort  = 36643
$httpsPort = 44332
$httpUrl   = "http://localhost:$httpPort"
$httpsUrl  = "https://localhost:$httpsPort"

# --- ngrok-Reste beenden ---
Get-Process -Name "ngrok" -ErrorAction SilentlyContinue | Stop-Process -Force

# --- 1) Projekt veroeffentlichen (erzeugt vollstaendigen wwwroot + web.config) ---
Write-Host "Veroeffentliche MagicCoinSnapper fuer IIS Express ..."
$publishArgs = @("publish", $projectFile, "-c", "Debug", "-o", $publishDir)
& dotnet @publishArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host "Die Veroeffentlichung ist fehlgeschlagen (Exit $LASTEXITCODE)."
    Read-Host "Enter zum Beenden"
    exit 1
}
if (-not (Test-Path (Join-Path $publishWwwroot "index.html"))) {
    Write-Host "Der veroeffentlichte wwwroot-Ordner enthaelt keine index.html: $publishWwwroot"
    Read-Host "Enter zum Beenden"
    exit 1
}

# --- 2) Arbeits-ApplicationHost.config mit Site + HTTPS-Bindung erzeugen ---
if (-not (Test-Path $vsConfigSrc)) {
    Write-Host "Keine IIS-Express-Konfiguration gefunden: $vsConfigSrc"
    Write-Host "Oeffne das Projekt einmal in Visual Studio mit dem IISExpress-Profil, damit die Konfiguration angelegt wird."
    Read-Host "Enter zum Beenden"
    exit 1
}

if (-not (Test-Path $publishDir)) { New-Item -ItemType Directory -Path $publishDir -Force | Out-Null }
Copy-Item -LiteralPath $vsConfigSrc -Destination $workConfig -Force

[xml]$cfg = Get-Content $workConfig -Raw
$sites = $cfg.configuration.'system.applicationHost'.sites
$existing = $sites.site | Where-Object { $_.name -eq "MagicCoinSnapper" }
if ($existing) { [void]$sites.RemoveChild($existing) }

$site = $cfg.CreateElement("site")
$site.SetAttribute("name", "MagicCoinSnapper")
$site.SetAttribute("id", "2")
$app = $cfg.CreateElement("application")
$app.SetAttribute("path", "/")
$app.SetAttribute("applicationPool", "Clr4IntegratedAppPool")
$vd = $cfg.CreateElement("virtualDirectory")
$vd.SetAttribute("path", "/")
$vd.SetAttribute("physicalPath", $publishWwwroot)
[void]$app.AppendChild($vd)
[void]$site.AppendChild($app)
$bindings = $cfg.CreateElement("bindings")
$bHttp = $cfg.CreateElement("binding")
$bHttp.SetAttribute("protocol", "http")
$bHttp.SetAttribute("bindingInformation", ":${httpPort}:localhost")
$bHttps = $cfg.CreateElement("binding")
$bHttps.SetAttribute("protocol", "https")
$bHttps.SetAttribute("bindingInformation", ":${httpsPort}:localhost")
[void]$bindings.AppendChild($bHttp)
[void]$bindings.AppendChild($bHttps)
[void]$site.AppendChild($bindings)
[void]$sites.AppendChild($site)

$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($workConfig, $cfg.OuterXml, $utf8NoBom)

# --- 3) IIS Express starten ---
Write-Host "Starte IIS Express: $httpsUrl"
$iisCommand = "& '$iisExe' /config:'$workConfig' /site:MagicCoinSnapper /systray:false"
Start-Process -FilePath "powershell.exe" -ArgumentList @(
    "-NoExit",
    "-NoProfile",
    "-ExecutionPolicy",
    "Bypass",
    "-Command",
    $iisCommand
)

# --- 4) Warten bis HTTPS verfuegbar ist ---
Write-Host "Warte auf lokale Anwendung ..."
$deadline = (Get-Date).AddSeconds(45)
$appReady = $false

do {
    try {
        $response = Invoke-WebRequest -Uri $httpsUrl -UseBasicParsing -TimeoutSec 2 -SkipCertificateCheck
        if ($response.StatusCode -lt 500) {
            $appReady = $true
            break
        }
    }
    catch {
        Start-Sleep -Seconds 1
    }
} while ((Get-Date) -lt $deadline)

if (-not $appReady) {
    Write-Host "Die lokale Anwendung war nach 45 Sekunden unter $httpsUrl nicht erreichbar."
    Write-Host "Pruefe das geoeffnete IIS-Express-Fenster auf Startfehler."
    Write-Host "Hinweis: HTTPS-Ports muessen im Bereich 44300-44399 liegen (IIS-Express-Zertifikat)."
    Read-Host "Enter zum Beenden"
    exit 1
}

Write-Host "Anwendung ist verfuegbar unter:"
Write-Host "  $httpsUrl  (HTTPS, fuer Kameratests)"
Write-Host "  $httpUrl   (HTTP)"

# --- 5) ngrok fuer Smartphone-Tests ---
$ngrokCommand = Get-Command ngrok -ErrorAction SilentlyContinue
if (-not $ngrokCommand) {
    Write-Host "ngrok wurde nicht im PATH gefunden. Oeffne lokale Browser-Adresse."
    Start-Process $httpsUrl
    Write-Host "Fuer Smartphone-Kameratests installiere ngrok und starte diese Datei erneut."
    Read-Host "Enter zum Beenden"
    exit 0
}

Write-Host "Starte ngrok-Tunnel fuer Smartphone-Tests ..."
Start-Process -FilePath "powershell.exe" -ArgumentList @(
    "-NoExit",
    "-NoProfile",
    "-ExecutionPolicy",
    "Bypass",
    "-Command",
    "ngrok http https://localhost:$httpsPort"
)

Write-Host "Warte auf oeffentliche HTTPS-Adresse von ngrok ..."
$deadline = (Get-Date).AddSeconds(30)
$publicUrl = $null

do {
    try {
        $tunnels = (Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -TimeoutSec 2).tunnels
        $httpsTunnel = $tunnels | Where-Object { $_.proto -eq "https" } | Select-Object -First 1
        if ($httpsTunnel.public_url) {
            $publicUrl = $httpsTunnel.public_url
            break
        }
    }
    catch {
        Start-Sleep -Seconds 1
    }
} while ((Get-Date) -lt $deadline)

if ($publicUrl) {
    Write-Host "Oeffne $publicUrl im Browser."
    Start-Process $publicUrl
    Write-Host ""
    Write-Host "Smartphone-Test: Oeffne diese Adresse auf dem Smartphone:"
    Write-Host $publicUrl
}
else {
    Write-Host "ngrok wurde gestartet, aber die HTTPS-Adresse konnte nicht automatisch gelesen werden."
    Write-Host "Falls ngrok nach einem Authtoken fragt, fuehre einmalig aus:"
    Write-Host "ngrok config add-authtoken DEIN_TOKEN"
    Write-Host ""
    Write-Host "Oeffne http://127.0.0.1:4040 und kopiere dort die HTTPS-Adresse."
    Start-Process "http://127.0.0.1:4040"
    Start-Process $httpsUrl
}

Read-Host "Enter zum Beenden"
