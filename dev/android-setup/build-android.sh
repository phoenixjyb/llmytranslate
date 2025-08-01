#!/bin/bash
# LLMyTranslate Android Build Script for Mac/Linux
# Bash script for building and deploying the Android app

ACTION="build"
INSTALL=false
CLEAN=false
RELEASE=false
DEBUG=true

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        build|install|test|clean|sync|devices|logs)
            ACTION="$1"
            shift
            ;;
        --install)
            INSTALL=true
            shift
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        --release)
            RELEASE=true
            DEBUG=false
            shift
            ;;
        --debug)
            DEBUG=true
            RELEASE=false
            shift
            ;;
        -h|--help)
            ACTION="help"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            ACTION="help"
            shift
            ;;
    esac
done

BUILD_TYPE="Debug"
if [ "$RELEASE" = true ]; then
    BUILD_TYPE="Release"
fi

ANDROID_DIR="$(dirname "$0")/android"

echo -e "${CYAN}=== LLMyTranslate Android Builder ===${NC}"
echo -e "${YELLOW}Build Type: $BUILD_TYPE${NC}"
echo -e "${GRAY}Android Directory: $ANDROID_DIR${NC}"

# Check if Android directory exists
if [ ! -d "$ANDROID_DIR" ]; then
    echo -e "${RED}❌ Android directory not found: $ANDROID_DIR${NC}"
    exit 1
fi

# Check Java installation
echo -e "${YELLOW}Checking Java installation...${NC}"
if command -v java &> /dev/null; then
    JAVA_VERSION=$(java -version 2>&1 | head -n 1)
    echo -e "${GREEN}✅ Java found: $JAVA_VERSION${NC}"
else
    echo -e "${RED}❌ Java not found or not in PATH${NC}"
    echo -e "${YELLOW}Please install OpenJDK 11 or 17:${NC}"
    echo -e "${CYAN}  1. macOS: brew install openjdk@17${NC}"
    echo -e "${CYAN}  2. Linux: sudo apt install openjdk-17-jdk${NC}"
    echo -e "${CYAN}  3. Or download from: https://adoptium.net/temurin/releases/${NC}"
    echo -e "${CYAN}  4. Set JAVA_HOME and update PATH${NC}"
    exit 1
fi

# Check Android SDK (optional but recommended)
if [ -n "$ANDROID_HOME" ]; then
    echo -e "${GREEN}✅ ANDROID_HOME set: $ANDROID_HOME${NC}"
else
    echo -e "${YELLOW}⚠️  ANDROID_HOME not set (optional for building)${NC}"
    echo -e "${GRAY}   For device installation, install Android SDK Command Line Tools${NC}"
fi

# Navigate to Android directory
cd "$ANDROID_DIR" || exit 1

case $ACTION in
    "build")
        echo "🔨 Building Android APK..."
        
        if [ "$CLEAN" = true ]; then
            echo "🧹 Cleaning previous builds..."
            ./gradlew clean
        fi
        
        if [ "$RELEASE" = true ]; then
            BUILD_TASK="assembleRelease"
        else
            BUILD_TASK="assembleDebug"
        fi
        
        ./gradlew $BUILD_TASK
        
        if [ $? -eq 0 ]; then
            echo "✅ Build successful!"
            
            if [ "$RELEASE" = true ]; then
                APK_PATH="app/build/outputs/apk/release/app-release.apk"
            else
                APK_PATH="app/build/outputs/apk/debug/app-debug.apk"
            fi
            
            if [ -f "$APK_PATH" ]; then
                echo "📱 APK created: $APK_PATH"
                
                if [ "$INSTALL" = true ]; then
                    echo "📲 Installing APK on connected device..."
                    if [ "$RELEASE" = true ]; then
                        INSTALL_TASK="installRelease"
                    else
                        INSTALL_TASK="installDebug"
                    fi
                    
                    ./gradlew $INSTALL_TASK
                    
                    if [ $? -eq 0 ]; then
                        echo "✅ App installed successfully!"
                    else
                        echo "❌ Installation failed!"
                    fi
                fi
            fi
        else
            echo "❌ Build failed!"
        fi
        ;;
    
    "install")
        echo "📲 Installing app on connected device..."
        if [ "$RELEASE" = true ]; then
            INSTALL_TASK="installRelease"
        else
            INSTALL_TASK="installDebug"
        fi
        ./gradlew $INSTALL_TASK
        ;;
    
    "test")
        echo "🧪 Running tests..."
        ./gradlew test
        ;;
    
    "clean")
        echo "🧹 Cleaning build artifacts..."
        ./gradlew clean
        ;;
    
    "sync")
        echo "🔄 Syncing Gradle dependencies..."
        ./gradlew --refresh-dependencies
        ;;
    
    "devices")
        echo "📱 Checking connected devices..."
        adb devices
        ;;
    
    "logs")
        echo "📋 Showing app logs (press Ctrl+C to stop)..."
        adb logcat | grep "LLMyTranslate"
        ;;
    
    "help"|*)
        echo "Usage: ./build-android.sh [action] [options]"
        echo ""
        echo "Actions:"
        echo "  build    - Build the APK (default)"
        echo "  install  - Install APK on connected device"
        echo "  test     - Run unit tests"
        echo "  clean    - Clean build artifacts"
        echo "  sync     - Sync Gradle dependencies"
        echo "  devices  - List connected devices"
        echo "  logs     - Show app logs"
        echo ""
        echo "Options:"
        echo "  --install   - Install after building"
        echo "  --clean     - Clean before building"
        echo "  --release   - Build release version"
        echo "  --debug     - Build debug version (default)"
        echo ""
        echo "Examples:"
        echo "  ./build-android.sh build --install --clean"
        echo "  ./build-android.sh build --release"
        echo "  ./build-android.sh devices"
        echo "  ./build-android.sh logs"
        ;;
esac

echo ""
echo "=== Build Script Complete ==="
