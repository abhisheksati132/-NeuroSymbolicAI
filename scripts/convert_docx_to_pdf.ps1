param (
    [Parameter(Mandatory=$true)]
    [string]$DocxPath,
    [Parameter(Mandatory=$true)]
    [string]$PdfPath
)

$resolvedDocx = (Resolve-Path $DocxPath).Path
$resolvedPdf = [System.IO.Path]::GetFullPath($PdfPath)

Write-Host "Converting $resolvedDocx to $resolvedPdf using Word COM..."

$word = $null
$doc = $null

try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $doc = $word.Documents.Open($resolvedDocx, $false, $true)
    $wdFormatPDF = 17
    $doc.SaveAs([ref]$resolvedPdf, [ref]$wdFormatPDF)
    Write-Host "Success: Exported to PDF successfully!"
} catch {
    Write-Error "Error during Word export: $_"
} finally {
    if ($doc -ne $null) {
        $doc.Close([ref]0)
    }
    if ($word -ne $null) {
        $word.Quit()
        [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
    }
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
}
