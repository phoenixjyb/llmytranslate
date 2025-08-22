plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.serialization")
    id("com.google.devtools.ksp")
    id("dagger.hilt.android.plugin")
}

android {
    namespace = "com.llmytranslate.android"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.llmytranslate.android"
        minSdk = 26
        targetSdk = 34
        versionCode = 2
        versionName = "2.0.0-streaming-tts"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        vectorDrawables {
            useSupportLibrary = true
        }
        
        // TensorFlow Lite requires ARM64 for optimal GPU performance
        ndk {
            abiFilters += listOf("arm64-v8a")
        }
        
        // TensorFlow Lite specific cmake arguments
        externalNativeBuild {
            cmake {
                cppFlags += listOf("-std=c++17", "-frtti", "-fexceptions")
                val extraCmakeArgs = (project.findProperty("cmakeArgs") as String?)
                    ?.split(" ")?.filter { it.isNotBlank() } ?: emptyList()
                arguments += listOf(
                    "-DANDROID_STL=c++_shared",
                    "-DTFLITE_GPU_AVAILABLE=ON",
                    "-DONNX_MOBILE_AVAILABLE=ON"
                    // , "-DREAL_TFLITE_AVAILABLE=ON"  // enable when libtensorflowlite.so is available
                )
                arguments += extraCmakeArgs
            }
        }
    }
    
    // Enable native builds for TensorFlow Lite Mobile AI
    externalNativeBuild {
        cmake {
            path = file("src/main/cpp/CMakeLists.txt")
            version = "3.22.1"
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
        debug {
            isMinifyEnabled = false
            isDebuggable = true
        }
    }
    
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_1_8
        targetCompatibility = JavaVersion.VERSION_1_8
        isCoreLibraryDesugaringEnabled = true
    }
    
    kotlinOptions {
        jvmTarget = "1.8"
    }
    
    buildFeatures {
        compose = true
    }
    
    composeOptions {
        kotlinCompilerExtensionVersion = "1.5.4"
    }
    
    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
}

dependencies {
    // Core Android
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.7.0")
    implementation("androidx.activity:activity-compose:1.8.2")
    
    // Jetpack Compose - Stable BOM
    implementation(platform("androidx.compose:compose-bom:2024.02.00"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-graphics")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.material:material-icons-extended")
    
    // Navigation
    implementation("androidx.navigation:navigation-compose:2.7.6")
    
    // ViewModel
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.7.0")
    
    // Networking
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("com.squareup.okhttp3:logging-interceptor:4.12.0")
    implementation("org.java-websocket:Java-WebSocket:1.5.4")
    
    // Audio processing for STT
    implementation("androidx.media3:media3-common:1.2.1")
    
    // TensorFlow Lite for mobile AI acceleration
    implementation("org.tensorflow:tensorflow-lite:2.14.0")
    implementation("org.tensorflow:tensorflow-lite-gpu:2.14.0")
    implementation("org.tensorflow:tensorflow-lite-support:0.4.4")
    
    // ONNX Runtime for fallback mobile AI
    implementation("com.microsoft.onnxruntime:onnxruntime-android:1.16.3")
    
    // JSON Serialization
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.6.0")
    implementation("com.squareup.moshi:moshi:1.15.0")
    implementation("com.squareup.moshi:moshi-kotlin:1.15.0")
    implementation("com.squareup.moshi:moshi-adapters:1.15.0")
    ksp("com.squareup.moshi:moshi-kotlin-codegen:1.15.0")
    
    // Dependency Injection (Dagger Hilt)
    implementation("com.google.dagger:hilt-android:2.48.1")
    ksp("com.google.dagger:hilt-compiler:2.48.1")
    
    // Retrofit for REST API calls
    implementation("com.squareup.retrofit2:retrofit:2.11.0")
    implementation("com.squareup.retrofit2:converter-moshi:2.11.0")
    
    // Room Database (simplified without KAPT)
    implementation("androidx.room:room-runtime:2.6.1")
    implementation("androidx.room:room-ktx:2.6.1")
    
    // Preferences
    implementation("androidx.datastore:datastore-preferences:1.1.1")
    
    // Permissions
    implementation("com.google.accompanist:accompanist-permissions:0.34.0")
    
    // Coroutines
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3")
    
    // Core Library Desugaring
    coreLibraryDesugaring("com.android.tools:desugar_jdk_libs:2.0.4")
    
    // Testing
    testImplementation("junit:junit:4.13.2")
    testImplementation("org.mockito:mockito-core:5.7.0")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.7.3")
    
    androidTestImplementation("androidx.test.ext:junit:1.1.5")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.5.1")
    androidTestImplementation(platform("androidx.compose:compose-bom:2024.02.00"))
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")
    
    debugImplementation("androidx.compose.ui:ui-tooling")
    debugImplementation("androidx.compose.ui:ui-test-manifest")
}

// --- TensorFlow Lite native convenience tasks ---
tasks.register("tfliteCopyLibs") {
    group = "tflite"
    description = "Copy TFLite native .so from AARs into third_party/tflite/libs/arm64-v8a"
    doLast {
        val dest = file("src/main/cpp/third_party/tflite/libs/arm64-v8a")
        dest.mkdirs()
        val deps = listOf(
            "org.tensorflow:tensorflow-lite:2.14.0",
            "org.tensorflow:tensorflow-lite-gpu:2.14.0"
        )
        deps.forEach { coord ->
            val cfg = configurations.detachedConfiguration(dependencies.create(coord))
            cfg.isTransitive = false
            cfg.resolve().forEach { aar ->
                copy {
                    from(zipTree(aar))
                    include("jni/arm64-v8a/*.so")
                    into(dest)
                }
            }
        }
        println("Copied TFLite .so files to: ${dest}")
    }
}

tasks.register<Exec>("tfliteFetchHeaders") {
    group = "tflite"
    description = "Fetch TFLite C++ headers into third_party/tflite/include via helper script"
    commandLine("bash", "${project.rootDir}/scripts/android/fetch_tflite_headers.sh")
}

// --- Always bundle real TinyLlama TFLite model from repo's models/ folder ---
// We include only the LLM (real_tinyllama.tflite) for now; SpeechT5 is postponed.
val generatedRealModelsDir = layout.buildDirectory.dir("generated/assets/realModels")

val prepareRealLLMAssets = tasks.register<Copy>("prepareRealLLMAssets") {
    val src = rootProject.file("models")
    from(src) { include("real_tinyllama.tflite") }
    into(generatedRealModelsDir.map { it.dir("models") })
    doFirst {
        println("Including LLM model from ${src} → ${generatedRealModelsDir.get().asFile}/models")
    }
}

android.sourceSets.named("main").configure {
    assets.srcDir(generatedRealModelsDir)
}

// Ensure the copy runs before merging assets for both debug and release
listOf("mergeDebugAssets", "mergeReleaseAssets").forEach { target ->
    tasks.matching { it.name == target }.configureEach {
        dependsOn(prepareRealLLMAssets)
    }
}
