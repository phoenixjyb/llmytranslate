#!/bin/bash
# ================================================================================================
# LLM Translation Service - Stop Launcher (Unix/Linux/macOS)
# This script redirects to the actual stop script in the scripts/ folder
# ================================================================================================

echo -e "\033[0;31m🛑 LLM Translation Service Stop Launcher\033[0m"
echo -e "\033[1;33mRedirecting to main stop script...\033[0m"
echo ""

# Pass all parameters to the main script
exec "./scripts/stop-service.sh" "$@"
