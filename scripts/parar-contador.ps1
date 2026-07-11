# Encerra os servicos do Egg pelas portas 8009, 9000, 9001 e 9002.
$ports = @(8009, 9000, 9001, 9002, 5005, 5006)

foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    foreach ($connection in $connections) {
        $processId = $connection.OwningProcess
        if ($processId -and $processId -gt 0) {
            $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
            if ($process) {
                Write-Host "Encerrando $($process.ProcessName) (PID $processId) na porta $port"
                Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
            }
        }
    }
}

# Encerra wrappers Maven/Quarkus orfaos que possam segurar o JDWP
Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object {
        $_.Name -match '^(java|javaw)\.exe$' -and
        $_.CommandLine -match 'quarkus:dev|cortex-bff|cortex-gateway|egg-bff|egg-gateway'
    } |
    ForEach-Object {
        Write-Host "Encerrando processo Java orfao (PID $($_.ProcessId))"
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    }

Write-Host "Pronto." -ForegroundColor Green
