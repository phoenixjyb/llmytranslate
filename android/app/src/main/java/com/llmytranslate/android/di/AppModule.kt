package com.llmytranslate.android.di

import android.content.Context
import com.llmytranslate.android.services.STTService
import com.llmytranslate.android.services.TTSService
import com.llmytranslate.android.services.WebSocketService
import com.squareup.moshi.Moshi
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import java.util.concurrent.TimeUnit
import javax.inject.Singleton

/**
 * Hilt dependency injection module for the Android app.
 */
@Module
@InstallIn(SingletonComponent::class)
object AppModule {
    
    @Provides
    @Singleton
    fun provideOkHttpClient(): OkHttpClient {
        val loggingInterceptor = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY // Enable debug logging
        }
        
        return OkHttpClient.Builder()
            .addInterceptor(loggingInterceptor)
            .connectTimeout(10, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .build()
    }
    
    @Provides
    @Singleton
    fun provideMoshi(): Moshi {
        return Moshi.Builder()
            .add(KotlinJsonAdapterFactory())
            .build()
    }
    
    @Provides
    @Singleton
    fun provideSTTService(@ApplicationContext context: Context): STTService {
        return STTService(context)
    }
    
    @Provides
    @Singleton
    fun provideTTSService(@ApplicationContext context: Context): TTSService {
        return TTSService(context)
    }
    
    @Provides
    @Singleton
    fun provideWebSocketService(@ApplicationContext context: Context, moshi: Moshi): WebSocketService {
        return WebSocketService().apply {
            // Initialize if needed
        }
    }
}
