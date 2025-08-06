package com.llmytranslate.android.ui.navigation

import androidx.compose.runtime.Composable
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import com.llmytranslate.android.ui.chat.EnhancedChatScreen
import com.llmytranslate.android.ui.voice.VoiceCallScreen
import com.llmytranslate.android.ui.settings.SettingsScreen

/**
 * Main navigation component for the app.
 */
@Composable
fun AppNavigation(
    navController: NavHostController
) {
    NavHost(
        navController = navController,
        startDestination = "enhanced_chat"
    ) {
        composable("enhanced_chat") {
            EnhancedChatScreen(
                onNavigateToVoice = {
                    navController.navigate("voice")
                },
                onNavigateToSettings = {
                    navController.navigate("settings")
                }
            )
        }
        
        composable("voice") {
            VoiceCallScreen(
                onNavigateBack = {
                    navController.popBackStack()
                },
                onNavigateToSettings = {
                    navController.navigate("settings")
                }
            )
        }
        
        composable("settings") {
            SettingsScreen(
                onNavigateBack = {
                    navController.popBackStack()
                }
            )
        }
    }
}
