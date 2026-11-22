# Converts .docx files to PDF with Microsoft Word (updates tables of contents first)
# and .pptx files to PDF with PowerPoint. Usage: export_pdf.ps1 file1.docx file2.pptx ...
# A named mutex makes concurrent callers take turns (PowerPoint is a single shared process).
param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Files)

$mutex = New-Object System.Threading.Mutex($false, "CSAI301_OfficeExport")
[void]$mutex.WaitOne()
$word = $null
$ppt = $null
$pptWasBusy = $false
try {
    foreach ($file in $Files) {
        $full = (Resolve-Path $file).Path
        $pdf = [System.IO.Path]::ChangeExtension($full, ".pdf")
        if ($full.ToLower().EndsWith(".docx")) {
            if ($null -eq $word) { $word = New-Object -ComObject Word.Application; $word.Visible = $false; $word.DisplayAlerts = 0 }
            $doc = $word.Documents.Open($full, $false, $false)
            foreach ($toc in $doc.TablesOfContents) { $toc.Update() }
            $doc.Fields.Update() | Out-Null
            $doc.Save()
            $doc.ExportAsFixedFormat($pdf, 17)          # 17 = wdExportFormatPDF
            $pages = $doc.ComputeStatistics(2)          # 2 = wdStatisticPages
            $doc.Close($false)
            "{0}  ->  {1}  ({2} pages)" -f (Split-Path $full -Leaf), (Split-Path $pdf -Leaf), $pages
        }
        elseif ($full.ToLower().EndsWith(".pptx")) {
            if ($null -eq $ppt) {
                $ppt = New-Object -ComObject PowerPoint.Application
                $pptWasBusy = $ppt.Presentations.Count -gt 0    # someone else's presentations are open
            }
            $deck = $ppt.Presentations.Open($full, $true, $false, $false)   # read-only, no window
            $deck.SaveAs($pdf, 32)                      # 32 = ppSaveAsPDF
            $slides = $deck.Slides.Count
            $deck.Close()
            "{0}  ->  {1}  ({2} slides)" -f (Split-Path $full -Leaf), (Split-Path $pdf -Leaf), $slides
        }
    }
}
finally {
    if ($null -ne $word) { $word.Quit(); [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null }
    if ($null -ne $ppt) {
        if (-not $pptWasBusy) { $ppt.Quit() }           # never close a PowerPoint that was already in use
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($ppt) | Out-Null
    }
    $mutex.ReleaseMutex()
}
