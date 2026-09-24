# Codeteam skills installer (portable)
# Copies skills/ into ~/.claude/skills/ and rewrites the hardcoded root path.
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path.Replace('\', '/')
$src = Join-Path $root 'skills'
$dst = Join-Path $env:USERPROFILE '.claude\skills'

Write-Host "Codeteam root: $root"
Write-Host "Install target: $dst"
if (-not (Test-Path $dst)) { New-Item -ItemType Directory -Path $dst | Out-Null }

Get-ChildItem $src -Directory | Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') } | ForEach-Object {
    $target = Join-Path $dst $_.Name
    if (Test-Path $target) { Remove-Item $target -Recurse -Force }
    Copy-Item $_.FullName $target -Recurse
    $skill = Join-Path $target 'SKILL.md'
    $content = Get-Content $skill -Raw -Encoding UTF8
    $content = $content -replace 'E:/code/codeteam', $root -replace 'E:\\code\\codeteam', ($root.Replace('/', '\'))
    [IO.File]::WriteAllText($skill, $content, (New-Object System.Text.UTF8Encoding($false)))
    Write-Host "  installed: $($_.Name)"
}
Write-Host ''
Write-Host 'Done. Skills are in ~/.claude/skills - restart your Claude session to use them.'
