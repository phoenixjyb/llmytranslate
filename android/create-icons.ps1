# Create Android App Icons Script
# This script creates placeholder icons for the Android app
# For production, replace these with proper icons using Android Studio's Asset Studio

Write-Host "=== Android Icon Generator ===" -ForegroundColor Cyan
Write-Host "Creating placeholder icons for LLMyTranslate Android app..."

$iconSizes = @{
    "mipmap-mdpi" = 48
    "mipmap-hdpi" = 72
    "mipmap-xhdpi" = 96
    "mipmap-xxhdpi" = 144
    "mipmap-xxxhdpi" = 192
}

$basePath = "C:\Users\yanbo\wSpace\llmytranslate\android\app\src\main\res"

Write-Host "`n📋 Icon sizes needed:" -ForegroundColor Yellow
foreach ($folder in $iconSizes.Keys) {
    $size = $iconSizes[$folder]
    Write-Host "  • $folder : ${size}x${size} px" -ForegroundColor Gray
}

Write-Host "`n💡 To create proper icons:" -ForegroundColor Green
Write-Host "1. Use Android Studio's Image Asset Studio:"
Write-Host "   - Right-click app > New > Image Asset"
Write-Host "   - Choose 'Launcher Icons (Adaptive and Legacy)'"
Write-Host "   - Upload your logo/icon image"
Write-Host ""
Write-Host "2. Or use online tools like:"
Write-Host "   - https://romannurik.github.io/AndroidAssetStudio/"
Write-Host "   - https://icon.kitchen/"
Write-Host ""
Write-Host "3. For now, creating minimal placeholder icons..."

# Create basic XML drawable as placeholder
$xmlIcon = @"
<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp"
    android:height="24dp"
    android:viewportWidth="24"
    android:viewportHeight="24"
    android:tint="?attr/colorOnPrimary">
  <path
      android:fillColor="@android:color/white"
      android:pathData="M12,2C6.48,2 2,6.48 2,12s4.48,10 10,10 10,-4.48 10,-10S17.52,2 12,2zM13,17h-2v-6h2v6zM13,9h-2L11,7h2v2z"/>
</vector>
"@

# Create drawable directory
$drawableDir = Join-Path $basePath "drawable"
if (!(Test-Path $drawableDir)) {
    New-Item -ItemType Directory -Path $drawableDir -Force
    Write-Host "✅ Created drawable directory" -ForegroundColor Green
}

# Create placeholder icon
$iconPath = Join-Path $drawableDir "ic_launcher_foreground.xml"
$xmlIcon | Out-File -FilePath $iconPath -Encoding UTF8
Write-Host "✅ Created placeholder vector icon" -ForegroundColor Green

Write-Host "`n🔄 You can now build the app with placeholder icons" -ForegroundColor Cyan
Write-Host "⚠️  Remember to replace with proper icons before production release" -ForegroundColor Yellow
