param(
    [string]$RepositoryName = "MagicCoinSnapper",
    [string]$OutputPath = "bin/Release/github-pages",
    [switch]$SkipPublish
)

$ErrorActionPreference = "Stop"

function Set-BaseHref {
    param(
        [string]$Html,
        [string]$BasePath
    )

    $basePattern = '<base href="[^"]*" />'
    if ($Html -notmatch $basePattern) {
        throw "Im HTML wurde kein base-href gefunden."
    }

    return [System.Text.RegularExpressions.Regex]::Replace(
        $Html,
        $basePattern,
        "<base href=`"$BasePath`" />",
        1
    )
}

function Set-ServiceWorkerBase {
    param(
        [string]$Content,
        [string]$BasePath
    )

    $basePattern = 'const base = "[^"]*";'
    if ($Content -notmatch $basePattern) {
        throw "Im service-worker.published.js wurde kein const base = `"...`" gefunden."
    }

    return [System.Text.RegularExpressions.Regex]::Replace(
        $Content,
        $basePattern,
        "const base = `"$BasePath`";",
        1
    )
}

if ([string]::IsNullOrWhiteSpace($RepositoryName)) {
    throw "Der Repository-Name darf nicht leer sein."
}

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$projectPath = Join-Path $projectRoot "MagicCoinSnapper.csproj"

if ([System.IO.Path]::IsPathRooted($OutputPath)) {
    $resolvedOutputPath = $OutputPath
}
else {
    $resolvedOutputPath = Join-Path $projectRoot $OutputPath
}

$projectRootFullPath = [System.IO.Path]::GetFullPath($projectRoot)
$resolvedOutputFullPath = [System.IO.Path]::GetFullPath($resolvedOutputPath)
if (-not $resolvedOutputFullPath.StartsWith($projectRootFullPath, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Der Ausgabeordner muss innerhalb des Projektordners liegen: $resolvedOutputFullPath"
}

if ((Test-Path $resolvedOutputFullPath) -and -not $SkipPublish) {
    Remove-Item -LiteralPath $resolvedOutputFullPath -Recurse -Force
}

$basePath = "/$RepositoryName/"
$utf8WithoutBom = [System.Text.UTF8Encoding]::new($false)
$sourceIndexPath = Join-Path $projectRoot "wwwroot/index.html"
$sourceServiceWorkerPath = Join-Path $projectRoot "wwwroot/service-worker.published.js"
$originalSourceIndexHtml = [System.IO.File]::ReadAllText($sourceIndexPath, [System.Text.Encoding]::UTF8)
$originalSourceServiceWorker = [System.IO.File]::ReadAllText($sourceServiceWorkerPath, [System.Text.Encoding]::UTF8)

if (-not $SkipPublish) {
    $publishArguments = @(
        "publish",
        $projectPath,
        "--configuration",
        "Release",
        "--output",
        $resolvedOutputFullPath
    )

    try {
        $buildSourceIndexHtml = Set-BaseHref -Html $originalSourceIndexHtml -BasePath $basePath
        [System.IO.File]::WriteAllText($sourceIndexPath, $buildSourceIndexHtml, $utf8WithoutBom)

        $buildSourceServiceWorker = Set-ServiceWorkerBase -Content $originalSourceServiceWorker -BasePath $basePath
        [System.IO.File]::WriteAllText($sourceServiceWorkerPath, $buildSourceServiceWorker, $utf8WithoutBom)

        & dotnet @publishArguments
        if ($LASTEXITCODE -ne 0) {
            exit $LASTEXITCODE
        }
    }
    finally {
        [System.IO.File]::WriteAllText($sourceIndexPath, $originalSourceIndexHtml, $utf8WithoutBom)
        [System.IO.File]::WriteAllText($sourceServiceWorkerPath, $originalSourceServiceWorker, $utf8WithoutBom)
    }
}

$publishPath = Join-Path $resolvedOutputFullPath "wwwroot"
if (-not (Test-Path $publishPath)) {
    throw "Der veröffentlichte wwwroot-Ordner wurde nicht gefunden: $publishPath"
}

$indexPath = Join-Path $publishPath "index.html"
$notFoundPath = Join-Path $publishPath "404.html"
$noJekyllPath = Join-Path $publishPath ".nojekyll"

$indexHtml = Get-Content $indexPath -Raw -Encoding UTF8
$expectedBaseHref = "<base href=`"$basePath`" />"
if ($indexHtml -notmatch [System.Text.RegularExpressions.Regex]::Escape($expectedBaseHref)) {
    throw "Der veröffentlichte base-href ist nicht korrekt: $basePath"
}

$publishedServiceWorkerPath = Join-Path $publishPath "service-worker.js"
if (-not (Test-Path $publishedServiceWorkerPath)) {
    throw "Der veröffentlichte service-worker.js wurde nicht gefunden: $publishedServiceWorkerPath"
}
$publishedServiceWorker = Get-Content $publishedServiceWorkerPath -Raw -Encoding UTF8
$expectedServiceWorkerBase = "const base = `"$basePath`";"
if ($publishedServiceWorker -notmatch [System.Text.RegularExpressions.Regex]::Escape($expectedServiceWorkerBase)) {
    throw "Der veröffentlichte service-worker base ist nicht korrekt: $basePath"
}

Copy-Item -Path $indexPath -Destination $notFoundPath -Force
New-Item -Path $noJekyllPath -ItemType File -Force | Out-Null

Write-Output "GitHub-Pages-Releasebuild vorbereitet: $publishPath"
