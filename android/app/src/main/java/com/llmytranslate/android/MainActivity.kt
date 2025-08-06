package com.llmytranslate.android

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.navigation.compose.rememberNavController
import com.llmytranslate.android.ui.navigation.AppNavigation
import com.llmytranslate.android.ui.theme.LLMyTranslateTheme

/**
 * Main Activity for LLMyTranslate Android app.
 * Uses Jetpack Compose for modern UI with Material Design 3.
 */
class MainActivity : ComponentActivity() {
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        setContent {
            LLMyTranslateTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    LLMyTranslateApp()
                }
            }
        }
    }
}

@Composable
fun LLMyTranslateApp() {
    val navController = rememberNavController()
    AppNavigation(navController = navController)
}

@Preview(showBackground = true)
@Composable
fun LLMyTranslateAppPreview() {
    LLMyTranslateTheme {
        LLMyTranslateApp()
    }
}
