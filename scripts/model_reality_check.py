#!/usr/bin/env python3
"""
TRUTH CHECK: Verify if our TensorFlow Lite models are real or just stubs.
This script will analyze the models to determine their actual capabilities.
"""

import tensorflow as tf
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModelRealityCheck:
    def __init__(self):
        self.models_dir = Path("./models/")
    
    def analyze_model_weights(self, model_path: Path):
        """Analyze if model has meaningful weights or just random initialization."""
        logger.info(f"\n🔍 ANALYZING: {model_path.name}")
        
        try:
            interpreter = tf.lite.Interpreter(model_path=str(model_path))
            interpreter.allocate_tensors()
            
            # Get tensor details
            tensor_details = interpreter.get_tensor_details()
            
            logger.info(f"   📊 Total tensors: {len(tensor_details)}")
            
            # Analyze weights
            weight_tensors = [t for t in tensor_details if 'weight' in t['name'].lower() or 'kernel' in t['name'].lower()]
            
            if not weight_tensors:
                logger.warning(f"   ⚠️ No clear weight tensors found")
                return "UNKNOWN"
            
            # Check if weights look trained or random
            total_params = 0
            random_like_count = 0
            
            for tensor in weight_tensors[:5]:  # Check first 5 weight tensors
                try:
                    weights = interpreter.get_tensor(tensor['index'])
                    if weights.size > 0:
                        total_params += weights.size
                        
                        # Check if weights look random (close to normal distribution around 0)
                        mean = np.mean(weights)
                        std = np.std(weights)
                        
                        logger.info(f"   📈 {tensor['name']}: shape={weights.shape}, mean={mean:.6f}, std={std:.6f}")
                        
                        # Random weights typically have mean close to 0 and std around 0.1-1.0
                        if abs(mean) < 0.01 and 0.01 < std < 1.0:
                            random_like_count += 1
                            
                except Exception as e:
                    logger.warning(f"   ⚠️ Could not analyze tensor {tensor['name']}: {e}")
            
            logger.info(f"   🎯 Total parameters: {total_params:,}")
            
            # Determine if model is real or stub
            if random_like_count >= len(weight_tensors) * 0.7:  # 70% of weights look random
                return "STUB"
            else:
                return "REAL"
                
        except Exception as e:
            logger.error(f"   ❌ Analysis failed: {e}")
            return "ERROR"
    
    def test_model_behavior(self, model_path: Path):
        """Test if model produces meaningful outputs or just noise."""
        logger.info(f"\n🧪 BEHAVIOR TEST: {model_path.name}")
        
        try:
            interpreter = tf.lite.Interpreter(model_path=str(model_path))
            interpreter.allocate_tensors()
            
            input_details = interpreter.get_input_details()
            output_details = interpreter.get_output_details()
            
            # Test with multiple different inputs
            test_results = []
            
            for i in range(3):
                # Create different test inputs
                if input_details[0]['dtype'] == np.int32:
                    test_input = np.random.randint(0, 100, size=input_details[0]['shape'], dtype=np.int32)
                else:
                    test_input = np.random.randn(*input_details[0]['shape']).astype(input_details[0]['dtype'])
                
                interpreter.set_tensor(input_details[0]['index'], test_input)
                interpreter.invoke()
                output = interpreter.get_tensor(output_details[0]['index'])
                
                test_results.append(output.copy())
            
            # Check if outputs are meaningfully different for different inputs
            output_differences = []
            for i in range(len(test_results)-1):
                diff = np.mean(np.abs(test_results[i] - test_results[i+1]))
                output_differences.append(diff)
            
            avg_diff = np.mean(output_differences)
            logger.info(f"   📊 Average output difference: {avg_diff:.6f}")
            
            # Check output characteristics
            sample_output = test_results[0]
            output_mean = np.mean(sample_output)
            output_std = np.std(sample_output)
            output_range = np.max(sample_output) - np.min(sample_output)
            
            logger.info(f"   📈 Output stats: mean={output_mean:.6f}, std={output_std:.6f}, range={output_range:.6f}")
            
            # For real models, outputs should vary significantly with different inputs
            if avg_diff < 1e-6:
                return "STATIC_OUTPUT"  # Same output regardless of input
            elif avg_diff < 1e-3:
                return "LOW_VARIATION"  # Very little variation
            else:
                return "NORMAL_VARIATION"  # Outputs change with inputs
                
        except Exception as e:
            logger.error(f"   ❌ Behavior test failed: {e}")
            return "ERROR"
    
    def check_deepspeech_authenticity(self):
        """Check if DeepSpeech is real or fake."""
        deepspeech_path = self.models_dir / "deepspeech_lite.tflite"
        
        if not deepspeech_path.exists():
            return "NOT_FOUND"
        
        logger.info(f"\n🕵️ DEEPSPEECH AUTHENTICITY CHECK")
        
        # Check file size - real DeepSpeech models are typically 40-50MB
        size_mb = deepspeech_path.stat().st_size / (1024 * 1024)
        logger.info(f"   📏 File size: {size_mb:.1f}MB")
        
        if size_mb > 40:
            logger.info(f"   ✅ Size suggests real model (DeepSpeech models are typically 40-50MB)")
            
            # Try to load and check architecture
            try:
                interpreter = tf.lite.Interpreter(model_path=str(deepspeech_path))
                interpreter.allocate_tensors()
                
                input_details = interpreter.get_input_details()
                output_details = interpreter.get_output_details()
                
                logger.info(f"   🏗️ Architecture:")
                logger.info(f"      Inputs: {len(input_details)}")
                logger.info(f"      Outputs: {len(output_details)}")
                
                # Real DeepSpeech has specific input/output patterns
                if len(input_details) >= 3 and len(output_details) >= 3:
                    logger.info(f"   ✅ Input/output pattern matches DeepSpeech architecture")
                    return "LIKELY_REAL"
                else:
                    logger.info(f"   ⚠️ Architecture doesn't match typical DeepSpeech")
                    return "LIKELY_FAKE"
                    
            except Exception as e:
                logger.error(f"   ❌ Could not analyze architecture: {e}")
                return "UNKNOWN"
        else:
            logger.info(f"   ❌ Too small for real DeepSpeech model")
            return "FAKE"
    
    def comprehensive_reality_check(self):
        """Run comprehensive reality check on all models."""
        logger.info("🔍 COMPREHENSIVE MODEL REALITY CHECK")
        logger.info("="*60)
        
        results = {}
        
        model_files = list(self.models_dir.glob("*.tflite"))
        
        for model_path in model_files:
            model_name = model_path.name
            
            # Skip DeepSpeech for now - handle separately
            if 'deepspeech' in model_name.lower():
                results[model_name] = {
                    'authenticity': self.check_deepspeech_authenticity(),
                    'type': 'Downloaded',
                    'analysis': 'Special case - downloaded model'
                }
                continue
            
            # Analyze created models
            weight_analysis = self.analyze_model_weights(model_path)
            behavior_analysis = self.test_model_behavior(model_path)
            
            results[model_name] = {
                'weight_analysis': weight_analysis,
                'behavior_analysis': behavior_analysis,
                'type': 'Created'
            }
        
        # Generate report
        logger.info(f"\n" + "="*60)
        logger.info("REALITY CHECK REPORT")
        logger.info("="*60)
        
        real_models = 0
        stub_models = 0
        
        for model_name, analysis in results.items():
            logger.info(f"\n📱 {model_name}")
            
            if analysis['type'] == 'Downloaded':
                auth = analysis['authenticity']
                if auth in ['LIKELY_REAL']:
                    logger.info(f"   ✅ LIKELY REAL - Downloaded from Mozilla DeepSpeech")
                    real_models += 1
                else:
                    logger.info(f"   ❌ QUESTIONABLE - {auth}")
                    stub_models += 1
            else:
                weight = analysis['weight_analysis']
                behavior = analysis['behavior_analysis']
                
                if weight == 'STUB' or behavior in ['STATIC_OUTPUT', 'LOW_VARIATION']:
                    logger.info(f"   ❌ STUB/PLACEHOLDER MODEL")
                    logger.info(f"      Weight analysis: {weight}")
                    logger.info(f"      Behavior analysis: {behavior}")
                    logger.info(f"      🔍 This is a randomly initialized model, not trained!")
                    stub_models += 1
                else:
                    logger.info(f"   ✅ APPEARS REAL")
                    logger.info(f"      Weight analysis: {weight}")
                    logger.info(f"      Behavior analysis: {behavior}")
                    real_models += 1
        
        # Final verdict
        logger.info(f"\n" + "="*60)
        logger.info("FINAL VERDICT")
        logger.info("="*60)
        
        total_models = len(results)
        logger.info(f"📊 Total models analyzed: {total_models}")
        logger.info(f"✅ Real/likely real models: {real_models}")
        logger.info(f"❌ Stub/placeholder models: {stub_models}")
        
        if stub_models > real_models:
            logger.info(f"\n🚨 WARNING: Most models appear to be STUBS/PLACEHOLDERS!")
            logger.info(f"📝 These models will not provide meaningful AI functionality.")
            logger.info(f"🔧 You need to download real, pre-trained models for production use.")
        elif real_models == 0:
            logger.info(f"\n🚨 CRITICAL: NO REAL MODELS FOUND!")
            logger.info(f"📝 All models appear to be placeholders.")
        else:
            logger.info(f"\n✅ Good news: Some real models found!")
            logger.info(f"📝 Focus on using the real models for production.")
        
        return results

def main():
    """Run reality check on all models."""
    checker = ModelRealityCheck()
    results = checker.comprehensive_reality_check()

if __name__ == "__main__":
    main()
