# Test the deployed pitch-shifter endpoint
Write-Host "Testing deployed service at https://pitch-shifter.ai-builders.space/"

# Create a simple test audio file (1 second of silence as WAV)
$wavHeader = [byte[]](
    0x52, 0x49, 0x46, 0x46, # "RIFF"
    0x24, 0x00, 0x00, 0x00, # File size - 8
    0x57, 0x41, 0x56, 0x45, # "WAVE"
    0x66, 0x6D, 0x74, 0x20, # "fmt "
    0x10, 0x00, 0x00, 0x00, # Subchunk1Size (16 for PCM)
    0x01, 0x00,             # AudioFormat (1 for PCM)
    0x01, 0x00,             # NumChannels (1 = mono)
    0x80, 0x3E, 0x00, 0x00, # SampleRate (16000 Hz)
    0x00, 0x7D, 0x00, 0x00, # ByteRate (SampleRate * NumChannels * BitsPerSample/8)
    0x02, 0x00,             # BlockAlign (NumChannels * BitsPerSample/8)
    0x10, 0x00,             # BitsPerSample (16)
    0x64, 0x61, 0x74, 0x61, # "data"
    0x00, 0x00, 0x00, 0x00  # Subchunk2Size (0 for now, minimal data)
)

$testFile = "c:\RTI work folder\pitch change\test_audio.wav"
[System.IO.File]::WriteAllBytes($testFile, $wavHeader)

Write-Host "Created test audio file: $testFile"

# Test the endpoint
try {
    Write-Host "`nSending request to deployed service..."
    $boundary = [System.Guid]::NewGuid().ToString()
    $LF = "`r`n"
    
    $bodyLines = (
        "--$boundary",
        "Content-Disposition: form-data; name=`"audio`"; filename=`"test.wav`"",
        "Content-Type: audio/wav$LF",
        [System.IO.File]::ReadAllText($testFile),
        "--$boundary",
        "Content-Disposition: form-data; name=`"semitones`"$LF",
        "-3",
        "--$boundary--$LF"
    ) -join $LF
    
    $response = Invoke-WebRequest -Uri "https://pitch-shifter.ai-builders.space/process" `
        -Method POST `
        -ContentType "multipart/form-data; boundary=$boundary" `
        -Body $bodyLines `
        -TimeoutSec 60 `
        -UseBasicParsing
    
    Write-Host "Response Status: $($response.StatusCode)"
    Write-Host "Response Content-Type: $($response.Headers['Content-Type'])"
    Write-Host "Response Size: $($response.Content.Length) bytes"
    
    if ($response.StatusCode -eq 200) {
        Write-Host "`n✅ SUCCESS! Service is working correctly."
    } else {
        Write-Host "`n⚠️ Unexpected status code: $($response.StatusCode)"
    }
    
} catch {
    Write-Host "`n❌ ERROR: $_"
    if ($_.Exception.Response) {
        $reader = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "Error response: $responseBody"
    }
}

# Clean up
Remove-Item $testFile -ErrorAction SilentlyContinue
