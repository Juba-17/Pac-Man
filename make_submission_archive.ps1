# Builds the single archive that has to be uploaded for one phase:
#     the video, the report, the code and the contribution statement.
#
# Easiest way: double-click make_phase1_archive.bat (or make_phase2_archive.bat).
# By hand:     powershell -ExecutionPolicy Bypass -File make_submission_archive.ps1 -Phase 1
#
# The archive is written next to this script as CSAI301_PacMan_Phase<N>.zip.
# Nothing in the project folder is changed.
param([Parameter(Mandatory = $true)][ValidateSet(1, 2)][int]$Phase)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$phaseDir = Join-Path $root "Phase$Phase"
$name = "CSAI301_PacMan_Phase$Phase"
$target = Join-Path $root "$name.zip"
$videoTypes = ".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v", ".wmv"

# ---- what goes into the archive: (file on disk, path inside the archive) ----
$items = New-Object System.Collections.Generic.List[object]
function Add-Folder([string]$folder, [string]$inside, [string[]]$skipFolders) {
    foreach ($file in Get-ChildItem $folder -Recurse -File) {
        $relative = $file.FullName.Substring($folder.Length + 1)
        $parts = $relative.Split("\")
        $skip = $false
        foreach ($part in $parts) { if ($skipFolders -contains $part) { $skip = $true } }
        if ($skip -or $relative -like "results\*_quick\*") { continue }
        $entry = "$name/$inside/" + $relative.Replace("\", "/")
        $items.Add(@($file.FullName, $entry))
    }
}
Add-Folder (Join-Path $phaseDir "code") "code" @("__pycache__", ".pytest_cache")
Add-Folder (Join-Path $phaseDir "report") "report" @()
Add-Folder (Join-Path $phaseDir "contribution") "contribution" @()
$videos = @(Get-ChildItem (Join-Path $phaseDir "video") -File | Where-Object { $videoTypes -contains $_.Extension.ToLower() })
foreach ($video in $videos) {
    $entry = "$name/video/" + $video.Name
    $items.Add(@($video.FullName, $entry))
}

# ---- write the zip (entry names with forward slashes, so it opens correctly everywhere) ----
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
if (Test-Path $target) { Remove-Item $target -Force }
$zip = [System.IO.Compression.ZipFile]::Open($target, [System.IO.Compression.ZipArchiveMode]::Create)
try {
    foreach ($item in $items) {
        [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
            $zip, $item[0], $item[1], [System.IO.Compression.CompressionLevel]::Optimal) | Out-Null
    }
}
finally { $zip.Dispose() }

# ---- summary ----
$size = [math]::Round((Get-Item $target).Length / 1MB, 1)
Write-Host ""
Write-Host "Written: $target  ($size MB, $($items.Count) files)"
foreach ($part in "code", "report", "contribution", "video") {
    $count = @($items | Where-Object { $_[1] -like "$name/$part/*" }).Count
    Write-Host ("  {0,-13} {1} files" -f $part, $count)
}
if ($videos.Count -eq 0) {
    Write-Host ""
    Write-Host "WARNING: no video file was found in Phase$Phase\video." -ForegroundColor Yellow
    Write-Host "         Record the video, save it there (for example Phase${Phase}_Video.mp4) and run this again." -ForegroundColor Yellow
    Write-Host "         The archive is NOT complete without the video." -ForegroundColor Yellow
}
else {
    Write-Host ""
    Write-Host "The archive contains the video, the report, the code and the contribution statement."
}
