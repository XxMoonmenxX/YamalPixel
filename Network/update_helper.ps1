param([Parameter(Mandatory=$true)][string]$ConfigPath)
$ErrorActionPreference = 'Stop'
$settings = Get-Content -LiteralPath $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
$current = [IO.Path]::GetFullPath($settings.current)
$staged = [IO.Path]::GetFullPath($settings.staged)
$backup = [IO.Path]::GetFullPath($settings.backup)
$directory = Split-Path -Parent $current
$log = $current + '.update.log'
$oldMoved = $false
$newMoved = $false
try {
    if ((Split-Path -Parent $staged) -ne $directory -or
        (Split-Path -Parent $backup) -ne $directory -or $staged -ne ($current + '.new')) {
        throw 'Invalid update paths'
    }
    $stream = [IO.File]::OpenRead($staged)
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try {
        $hash = [BitConverter]::ToString($algorithm.ComputeHash($stream)).Replace('-', '')
    } finally {
        $stream.Dispose()
        $algorithm.Dispose()
    }
    if ($hash -ne $settings.sha256) { throw 'Staged EXE checksum mismatch' }
    if ((Get-Item -LiteralPath $staged).Length -lt 1MB) { throw 'Staged EXE is too small' }
    # Nuitka's outer process and extracted child must both release the EXE.
    for ($attempt = 0; $attempt -lt 240; $attempt++) {
        try {
            $running = Get-Process -Id $settings.pid -ErrorAction SilentlyContinue
            if ($null -ne $running) {
                Start-Sleep -Milliseconds 500
                continue
            }
            if (Test-Path -LiteralPath $current) {
                Move-Item -LiteralPath $current -Destination $backup -ErrorAction Stop
                $oldMoved = $true
            }
            break
        } catch {
            if ($attempt -eq 239) { throw }
            Start-Sleep -Milliseconds 500
        }
    }
    if ((Test-Path -LiteralPath $current) -and -not $oldMoved) {
        throw 'Launcher did not exit or EXE is still locked'
    }
    Move-Item -LiteralPath $staged -Destination $current -ErrorAction Stop
    $newMoved = $true
    # The launcher is an interactive app and must reopen visibly.
    Start-Process -FilePath $current -WorkingDirectory $directory -ErrorAction Stop
    ('Updated and restarted: ' + (Get-Date -Format o) + '; backup: ' + $backup) |
        Set-Content -LiteralPath $log -Encoding UTF8
} catch {
    $failure = $_.Exception.Message
    try {
        if ($newMoved -and (Test-Path -LiteralPath $current)) {
            Move-Item -LiteralPath $current -Destination $staged -ErrorAction Stop
        }
        if ($oldMoved -and (Test-Path -LiteralPath $backup)) {
            Move-Item -LiteralPath $backup -Destination $current -ErrorAction Stop
        }
    } catch { $failure += '; rollback: ' + $_.Exception.Message }
    ('Update failed: ' + $failure) | Set-Content -LiteralPath $log -Encoding UTF8
    exit 1
} finally {
    # Delete only our two files and the empty helper directory.
    Remove-Item -LiteralPath $ConfigPath -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $PSCommandPath -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath (Split-Path -Parent $ConfigPath) -ErrorAction SilentlyContinue
}
