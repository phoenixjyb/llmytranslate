#!/bin/bash
# ================================================================================================
# LLM Translation Service - Main Launcher (Unix/Linux/macOS)
# This script redirects to the actual startup script in the scripts/ folder
# ================================================================================================

echo -e "\033[0;36m🚀 LLM Translation Service Launcher\033[0m"
echo -e "\033[1;33mRedirecting to main startup script...\033[0m"
echo ""

# Pass all parameters to the main script
exec "./scripts/start-service.sh" "$@"
