<#
Phase U13 — verified local Windows payload extraction (no phone).
PowerShell usage:
powershell -ExecutionPolicy Bypass -File .\scripts\u13_windows_local_extract.ps1 -PayloadFile "C:\ROM\payload.bin" -PayloadProperties "C:\ROM\payload_properties.txt" -DumperExe "C:\Tools\payload-dumper-go.exe"
Alternatively use -PayloadFile with the exact official full ZIP.

Does not touch Android devices, partitions, ADB, fastboot or phone images.
Creates a LOCAL folder with selected extracted images and a small JSON report.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$PayloadFile,
    [Parameter(Mandatory=$true)][string]$DumperExe,
    [string]$PayloadProperties = "",
    [string]$OutputDirectory = ""
)
$ErrorActionPreference = "Stop"
$OfficialZipName = "EvolutionX-16.0-20260915-shiba-11.11-Official.zip"
$OfficialZipBytes = [int64]3033648565
$OfficialZipSha256 = "41fd43bb5ec5c457906f4e8861aff0442b8670c2164069afbc6015ec31b5f5e0"
$OfficialPayloadBytes = [int64]3033640593
$ExpectedPayloadHash = "kZO/l+sj+c97aUxtyKJUd/LhIqtTuT063uwfWZJwKQ0="
$Parts = @("boot","init_boot","dtbo","vendor_boot","vendor_kernel_boot","vendor_dlkm","system_dlkm")

$PayloadFile = (Resolve-Path -LiteralPath $PayloadFile).Path
$DumperExe = (Resolve-Path -LiteralPath $DumperExe).Path
$InputItem = Get-Item -LiteralPath $PayloadFile
if ([string]::IsNullOrWhiteSpace($OutputDirectory)) {
    $OutputDirectory = Join-Path $InputItem.DirectoryName "U13_shiba_OFFLINE_ONLY"
}
if (!(Test-Path -LiteralPath $OutputDirectory)) {
    New-Item -ItemType Directory -Path $OutputDirectory | Out-Null
}
$OutputDirectory = (Resolve-Path -LiteralPath $OutputDirectory).Path
$InputSha256 = (Get-FileHash -LiteralPath $PayloadFile -Algorithm SHA256).Hash.ToLowerInvariant()
$InputKind = "unknown"

if ($InputItem.Extension -ieq ".zip") {
    if ($InputItem.Name -cne $OfficialZipName) {
        throw "Not the exact official 20260915 shiba ZIP filename."
    }
    if ($InputItem.Length -ne $OfficialZipBytes -or $InputSha256 -ne $OfficialZipSha256) {
        throw "Official OTA ZIP length/SHA256 mismatch. Aborting without extraction."
    }
    $InputKind = "official_sha256_verified_zip"
} elseif ($InputItem.Extension -ieq ".bin") {
    if ($InputItem.Name -ine "payload.bin") { throw "Expected payload.bin input." }
    if ($InputItem.Length -ne $OfficialPayloadBytes) { throw "payload.bin size mismatch." }
    if ([string]::IsNullOrWhiteSpace($PayloadProperties)) {
        throw "Raw payload.bin must include -PayloadProperties path for SHA256 verification."
    }
    $PayloadProperties = (Resolve-Path -LiteralPath $PayloadProperties).Path
    $Properties = @{}
    foreach ($line in (Get-Content -LiteralPath $PayloadProperties)) {
        if ($line -match '^([^=]+)=(.+)$') {
            $Properties[$Matches[1]] = $Matches[2].Trim()
        }
    }
    if ([int64]$Properties["FILE_SIZE"] -ne $OfficialPayloadBytes) {
        throw "FILE_SIZE from payload_properties.txt does not match."
    }
    if ($Properties["FILE_HASH"] -cne $ExpectedPayloadHash) {
        throw "FILE_HASH from payload_properties.txt differs from known input."
    }
    $hashBytes = New-Object byte[] 32
    for ($i=0; $i -lt 32; $i++) {
        $hashBytes[$i] = [Convert]::ToByte($InputSha256.Substring($i*2,2),16)
    }
    $actualPayloadB64 = [Convert]::ToBase64String($hashBytes)
    if ($actualPayloadB64 -cne $ExpectedPayloadHash) {
        throw "Actual payload.bin SHA256 does not match properties FILE_HASH."
    }
    $InputKind = "payload_sha256_and_properties_verified"
} else {
    throw "Only the exact official ZIP or payload.bin is supported."
}

Write-Host "Verified $InputKind"
Write-Host "Input SHA256: $InputSha256"
$PartsCsv = $Parts -join ","
& $DumperExe -p $PartsCsv -o $OutputDirectory $PayloadFile
if ($LASTEXITCODE -ne 0) {
    throw "payload-dumper-go failed. Check its output above."
}

$records = @()
foreach ($part in $Parts) {
    $file = Join-Path $OutputDirectory ($part + ".img")
    if (!(Test-Path -LiteralPath $file -PathType Leaf)) {
        throw "Missing expected partition output: $part"
    }
    $info = Get-Item -LiteralPath $file
    $h = (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant()
    $records += [pscustomobject]@{
        partition = $part
        image_file = $info.Name
        size_bytes = $info.Length
        sha256 = $h
    }
}
$report = [pscustomobject]@{
    phase = "U13_LOCAL_WINDOWS"
    source = $InputKind
    exact_official_rom_filename = $OfficialZipName
    expected_official_zip_sha256 = $OfficialZipSha256
    local_input_sha256 = $InputSha256
    partitions = $records
    kernel_kmi_verified = $false
    pixel8_ubuntu_bootable = $false
    flashable = $false
    phone_accessed = $false
}
$reportPath = Join-Path $OutputDirectory "U13_PARTITION_SHA256_REPORT.json"
$report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $reportPath -Encoding UTF8
Write-Host ""
Write-Host "SUCCESS. Send ONLY this small JSON file (not the huge payload):"
Write-Host $reportPath
Write-Host "Images remain local and must NOT be flashed."
