package com.llmytranslate.android.ui.navigation

import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import com.llmytranslate.android.ui.chat.EnhancedChatScreen
import com.llmytranslate.android.ui.voice.VoiceCallScreen
import com.llmytranslate.android.ui.settings.SettingsScreen
import com.llmytranslate.android.ui.testing.MobileAITestScreen
import androidx.compose.ui.platform.LocalContext
import com.llmytranslate.android.services.MobileAIService

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
                },
                onNavigateToTesting = {
                    navController.navigate("mobile_ai_test")
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
                onNavigateBack = { navController.popBackStack() },
                onNavigateToTesting = { navController.navigate("mobile_ai_test") }
            )
        }

        composable("mobile_ai_test") {
            val context = LocalContext.current
            val service = remember(context) { MobileAIService(context) }
            MobileAITestScreen(mobileAIService = service)
        }
    }
}
