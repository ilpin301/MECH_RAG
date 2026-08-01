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

# Detached ingest for MECH_RAG (server port 9623). Shared venv under F:\____IL_AI\RAG.
$root = "F:\____IL_AI\MECH_RAG\lightrag"
$venv = "F:\____IL_AI\RAG\lightrag\.venv-rag"
$log  = "$root\LOG\ingest_run.log"

Set-Location $root
New-Item -ItemType Directory -Force "$root\LOG" | Out-Null
$env:Path = "$venv\Scripts;$env:Path"   # raganything needs mineru on PATH
$env:NO_PROXY = '*'
$env:PYTHONIOENCODING = 'utf-8'
$env:MINERU_DEVICE_MODE = 'cuda'
$env:PYTHONINTMAXSTRDIGITS = '0'
# without this tiktoken downloads o200k_base from Azure CDN and times out on the SOCKS proxy machine
$env:TIKTOKEN_CACHE_DIR = 'C:\Users\il720506\AppData\Local\Temp\data-gym-cache'
# rag_ingest.py requires ZAI_API_KEY; this project stores the z.ai key as LLM_BINDING_API_KEY
$env:ZAI_API_KEY = (Get-Content "$root\.env" | Select-String '^LLM_BINDING_API_KEY=').Line.Split('=',2)[1].Trim()

& "$venv\Scripts\python.exe" rag_ingest.py @Files *>> $log
$ec = $LASTEXITCODE
# An ingest can exit 0 while writing NaN vectors (corrupt embedding model);
# check_vectors.py turns that silent failure into a non-zero EXITCODE.
if ($ec -eq 0) {
  & "$venv\Scripts\python.exe" check_vectors.py *>> $log
  if ($LASTEXITCODE -ne 0) { $ec = $LASTEXITCODE }
}
"EXITCODE=$ec" | Add-Content $log
docker compose start
