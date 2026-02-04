# E.V3 - Setup Python 3.13 venv with llama-cpp-python
# This uses portable Python (no system installation required)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "E.V3 - LLM Environment Setup (Python 3.13)" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Download portable Python 3.13
$portableDir = ".python313_portable"
$pythonZip = "$portableDir\python-3.13.1-embed-amd64.zip"
$pythonUrl = "https://www.python.org/ftp/python/3.13.1/python-3.13.1-embed-amd64.zip"

if (-not (Test-Path "$portableDir\python.exe")) {
    Write-Host "Downloading portable Python 3.13.1..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path $portableDir | Out-Null
    
    try {
        Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonZip -UseBasicParsing
        Write-Host "Extracting Python 3.13..." -ForegroundColor Yellow
        Expand-Archive -Path $pythonZip -DestinationPath $portableDir -Force
        Write-Host "Portable Python 3.13 ready" -ForegroundColor Green
    } catch {
        Write-Host "Failed to download Python 3.13" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Portable Python 3.13 already exists" -ForegroundColor Green
}

Write-Host ""

# Step 2: Enable pip in embedded Python
$pthFile = Get-ChildItem -Path $portableDir -Filter "python*._pth" | Select-Object -First 1
if ($pthFile) {
    $pthContent = Get-Content $pthFile.FullName
    if ($pthContent -notcontains "import site") {
        Write-Host "Enabling pip in portable Python..." -ForegroundColor Yellow
        $pthContent = $pthContent -replace "^#import site", "import site"
        if ($pthContent -notcontains "import site") {
            $pthContent += "import site"
        }
        Set-Content -Path $pthFile.FullName -Value $pthContent
        Write-Host "pip enabled" -ForegroundColor Green
    }
}

# Step 3: Install pip
$getPipUrl = "https://bootstrap.pypa.io/get-pip.py"
$getPipPath = "$portableDir\get-pip.py"

if (-not (Test-Path "$portableDir\Scripts\pip.exe")) {
    Write-Host "Installing pip..." -ForegroundColor Yellow
    try {
        Invoke-WebRequest -Uri $getPipUrl -OutFile $getPipPath -UseBasicParsing
        & "$portableDir\python.exe" $getPipPath
        Write-Host "pip installed" -ForegroundColor Green
    } catch {
        Write-Host "Failed to install pip" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "pip already installed" -ForegroundColor Green
}

Write-Host ""

# Step 4: Create venv
$venvDir = ".venv_llama"
if (-not (Test-Path "$venvDir\Scripts\python.exe")) {
    Write-Host "Creating Python 3.13 virtual environment..." -ForegroundColor Yellow
    try {
        & "$portableDir\python.exe" -m venv $venvDir
        Write-Host "Virtual environment created: $venvDir" -ForegroundColor Green
    } catch {
        Write-Host "Failed to create venv" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Virtual environment already exists: $venvDir" -ForegroundColor Green
}

Write-Host ""

# Step 5: Install llama-cpp-python
Write-Host "Installing llama-cpp-python..." -ForegroundColor Yellow
Write-Host "(This may take several minutes)" -ForegroundColor Gray
Write-Host ""

try {
    & "$venvDir\Scripts\pip.exe" install --upgrade pip | Out-Null
    & "$venvDir\Scripts\pip.exe" install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
    
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "SUCCESS! Environment ready" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Portable Python 3.13: $portableDir" -ForegroundColor Green
    Write-Host "Virtual environment: $venvDir" -ForegroundColor Green
    Write-Host "llama-cpp-python installed" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next: Run start_ev3.bat to launch E.V3 with LLM!" -ForegroundColor Cyan
    Write-Host ""
    
} catch {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Red
    Write-Host "WARNING: Installation completed with issues" -ForegroundColor Yellow
    Write-Host "============================================" -ForegroundColor Red
    Write-Host ""
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "You may need Visual Studio Build Tools." -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
