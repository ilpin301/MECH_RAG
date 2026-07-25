param(
  # UTF-8 file with one document path per line. Use this for non-ASCII names —
  # passing them as process args mangles them via the ANSI codepage.
  [string]$ListFile,
  [Parameter(ValueFromRemainingArguments=$true)][string[]]$Files
)

if ($ListFile) {
  $Files = Get-Content -LiteralPath $ListFile -Encoding UTF8 | Where-Object { $_.Trim() }
}
if (-not $Files) { throw "no input files: pass paths or -ListFile <utf8 list>" }

# Detached ingest for MECH_RAG (port 9621). Local venv.
$venv = "C:\____PETR_AI\MECH_RAG\lightrag\.venv-rag"
$log  = "C:\____PETR_AI\MECH_RAG\lightrag\ingest_run.log"

Set-Location C:\____PETR_AI\MECH_RAG\lightrag
$env:Path = "$venv\Scripts;$env:Path"   # raganything needs mineru on PATH
$env:NO_PROXY = '*'
$env:PYTHONIOENCODING = 'utf-8'
$env:MINERU_DEVICE_MODE = 'cuda'

& "$venv\Scripts\python.exe" rag_ingest.py @Files *>> $log
"EXITCODE=$LASTEXITCODE" | Add-Content $log
