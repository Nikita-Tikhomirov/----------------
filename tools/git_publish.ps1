param(
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

# Use the valid GitHub CLI keyring session instead of the expired process token.
Remove-Item Env:GITHUB_TOKEN -ErrorAction SilentlyContinue
$token = (& gh auth token).Trim()
if ($LASTEXITCODE -ne 0 -or -not $token) {
    throw 'GitHub CLI did not provide an authenticated token.'
}

$branch = (& git branch --show-current).Trim()
if ($LASTEXITCODE -ne 0 -or -not $branch) {
    throw 'Cannot determine the current Git branch.'
}

$authBytes = [Text.Encoding]::ASCII.GetBytes("x-access-token:$token")
$authorization = [Convert]::ToBase64String($authBytes)
$gitArgs = @(
    '-c', 'credential.helper=',
    '-c', "http.https://github.com/.extraheader=AUTHORIZATION: basic $authorization",
    'push'
)
if ($DryRun) {
    $gitArgs += '--dry-run'
}
$gitArgs += @('origin', $branch)

& git @gitArgs
exit $LASTEXITCODE
