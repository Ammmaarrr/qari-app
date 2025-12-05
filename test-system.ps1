# Quick Test Script for Qari App
# Tests all major endpoints

Write-Host "`n=== Qari App System Test ===" -ForegroundColor Green
Write-Host "Testing backend services...`n" -ForegroundColor Yellow

$baseUrl = "http://localhost:8000"
$passed = 0
$failed = 0

# Test 1: Health Check
Write-Host "[1/5] Testing health endpoint..." -NoNewline
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/health" -Method GET -TimeoutSec 5
    if ($response.status -eq "healthy") {
        Write-Host " ✓ PASSED" -ForegroundColor Green
        $passed++
    } else {
        Write-Host " ✗ FAILED" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host " ✗ FAILED (Not responding)" -ForegroundColor Red
    $failed++
}

# Test 2: Ready Check
Write-Host "[2/5] Testing readiness endpoint..." -NoNewline
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/ready" -Method GET -TimeoutSec 5
    Write-Host " ✓ PASSED" -ForegroundColor Green
    $passed++
} catch {
    Write-Host " ✗ FAILED" -ForegroundColor Red
    $failed++
}

# Test 3: API Docs
Write-Host "[3/5] Testing API documentation..." -NoNewline
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/docs" -Method GET -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host " ✓ PASSED" -ForegroundColor Green
        $passed++
    } else {
        Write-Host " ✗ FAILED" -ForegroundColor Red
        $failed++
    }
} catch {
    Write-Host " ✗ FAILED" -ForegroundColor Red
    $failed++
}

# Test 4: Correction List
Write-Host "[4/5] Testing correction list endpoint..." -NoNewline
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/v1/correction/list" -Method GET -TimeoutSec 5
    Write-Host " ✓ PASSED" -ForegroundColor Green
    $passed++
} catch {
    Write-Host " ✗ FAILED" -ForegroundColor Red
    $failed++
}

# Test 5: Feedback Queue
Write-Host "[5/5] Testing feedback queue endpoint..." -NoNewline
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/v1/feedback/queue?reviewer_id=test&limit=10" -Method GET -TimeoutSec 5
    Write-Host " ✓ PASSED" -ForegroundColor Green
    $passed++
} catch {
    Write-Host " ✗ FAILED" -ForegroundColor Red
    $failed++
}

# Summary
Write-Host "`n=== Test Summary ===" -ForegroundColor Cyan
Write-Host "Passed: $passed/5" -ForegroundColor Green
Write-Host "Failed: $failed/5" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Green" })

if ($passed -eq 5) {
    Write-Host "`n✓ All tests passed! Backend is operational." -ForegroundColor Green
    Write-Host "API Documentation: $baseUrl/docs" -ForegroundColor Cyan
} else {
    Write -Host "`n✗ Some tests failed. Check if backend is running:" -ForegroundColor Red
    Write-Host "  Run: .\start-backend.ps1" -ForegroundColor Yellow
}
