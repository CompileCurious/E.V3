#!/usr/bin/env pwsh
# Check build status for E.V3 C++ Kernel

Write-Host "`nE.V3 Build Status Check" -ForegroundColor Cyan
Write-Host "========================`n"

# Check Shell
$shell = "dist\Shell\Shell.exe"
if (Test-Path $shell) {
    $shellInfo = Get-Item $shell
    Write-Host "✓ Shell.exe" -ForegroundColor Green
    Write-Host "  Size: $([math]::Round($shellInfo.Length / 1MB, 1)) MB"
    Write-Host "  Modified: $($shellInfo.LastWriteTime)"
} else {
    Write-Host "✗ Shell.exe not found" -ForegroundColor Red
}

Write-Host ""

# Check Kernel
$kernel = "dist\Kernel\EV3Kernel.exe"
if (Test-Path $kernel) {
    $kernelInfo = Get-Item $kernel
    Write-Host "✓ C++ Kernel.exe" -ForegroundColor Green
    Write-Host "  Size: $([math]::Round($kernelInfo.Length / 1MB, 1)) MB"
    Write-Host "  Modified: $($kernelInfo.LastWriteTime)"
    Write-Host "`n✓✓✓ BUILD COMPLETE - BOTH COMPONENTS READY ✓✓✓" -ForegroundColor Green
} else {
    Write-Host "⏳ C++ Kernel.exe - Building..." -ForegroundColor Yellow
    
    # Check if build is running
    $msbuild = Get-Process -Name MSBuild -ErrorAction SilentlyContinue
    if ($msbuild) {
        Write-Host "  MSBuild processes: $($msbuild.Count)"
        Write-Host "  Status: Compiling llama.cpp (500+ files)"
        Write-Host "  Estimated: 10-15 minutes total"
        
        $buildDir = "kernel_cpp\build"
        if (Test-Path $buildDir) {
            $objFiles = (Get-ChildItem $buildDir -Recurse -Filter "*.obj" -ErrorAction SilentlyContinue).Count
            Write-Host "  Progress: ~$objFiles object files compiled"
        }
    } else {
        Write-Host "  Status: Build not running" -ForegroundColor Red
        Write-Host "  To start build: cd kernel_cpp\build; python -m cmake --build . --config Release"
    }
}

Write-Host ""
