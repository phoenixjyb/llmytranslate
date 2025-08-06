#!/bin/bash
# Quick Android Build Test Script

echo "🔧 Phase 2A Build Test Starting..."

# Set Java path for Android Studio
export JAVA_HOME="D:\Program Files\Android\Android Studio\jbr"
export PATH="$JAVA_HOME\bin:$PATH"

echo "☕ Java version:"
java -version

echo "🔨 Building Android app..."
./gradlew assembleDebug --console=plain

if [ $? -eq 0 ]; then
    echo "✅ Build successful! APK created:"
    ls -la app/build/outputs/apk/debug/
    echo "📱 Phase 2A implementation ready for testing!"
else
    echo "❌ Build failed. Checking logs..."
    echo "🔍 Recent build logs:"
    find . -name "*.log" -newer app/build.gradle.kts | head -5
fi

echo "🏁 Build test complete."
