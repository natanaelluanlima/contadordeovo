# Encerra os servicos do Egg pelas portas 8009, 9000, 9001 e 9002.
$ports = @(8009, 9000, 9001, 9002)

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

Write-Host "Pronto." -ForegroundColor Green
