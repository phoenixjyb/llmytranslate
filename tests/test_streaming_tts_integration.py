"""
Test Script for Streaming TTS Integration

This script tests the streaming TTS WebSocket handler to ensure proper integration
with the phone call system and validates real-time audio streaming functionality.
"""

import asyncio
import json
import time
import logging
from typing import List, Dict, Any
import websockets
from unittest.mock import Mock, AsyncMock

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import our streaming TTS components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from services.streaming_tts_service import StreamingTTSService
from services.streaming_tts_websocket import StreamingTTSWebSocketHandler, LLMStreamingSimulator

class MockWebSocket:
    """Mock WebSocket for testing"""
    
    def __init__(self):
        self.messages = []
        self.is_closed = False
    
    async def send_text(self, message: str):
        """Mock send_text method"""
        if not self.is_closed:
            self.messages.append(json.loads(message))
            logger.debug(f"📤 WebSocket sent: {json.loads(message)['type']}")
    
    def get_messages_by_type(self, message_type: str) -> List[Dict[str, Any]]:
        """Get all messages of a specific type"""
        return [msg for msg in self.messages if msg.get('type') == message_type]
    
    def close(self):
        """Mock close method"""
        self.is_closed = True

class StreamingTTSIntegrationTest:
    """Test suite for streaming TTS integration"""
    
    def __init__(self):
        self.streaming_tts = StreamingTTSService()
        self.websocket_handler = StreamingTTSWebSocketHandler(self.streaming_tts)
        self.test_results = {}
    
    async def test_basic_streaming_flow(self) -> Dict[str, Any]:
        """Test basic streaming TTS flow with WebSocket communication"""
        logger.info("🧪 Testing basic streaming TTS flow...")
        
        # Create mock WebSocket
        mock_websocket = MockWebSocket()
        session_id = "test_session_001"
        
        # Create LLM stream simulation
        llm_stream = LLMStreamingSimulator.create_llm_stream("Tell me about streaming TTS")
        
        start_time = time.time()
        
        try:
            # Run streaming TTS
            await self.websocket_handler.handle_llm_response_with_streaming_tts(
                mock_websocket,
                session_id,
                llm_stream,
                language="en",
                voice="default",
                speed=1.0,
                tts_mode="fast"
            )
            
            duration = time.time() - start_time
            
            # Analyze results
            all_messages = mock_websocket.messages
            audio_chunks = mock_websocket.get_messages_by_type("audio_chunk")
            start_message = mock_websocket.get_messages_by_type("tts_streaming_started")
            first_chunk_message = mock_websocket.get_messages_by_type("first_audio_chunk")
            completion_message = mock_websocket.get_messages_by_type("tts_streaming_completed")
            
            result = {
                "success": True,
                "total_duration": round(duration, 2),
                "message_counts": {
                    "total_messages": len(all_messages),
                    "audio_chunks": len(audio_chunks),
                    "start_messages": len(start_message),
                    "first_chunk_messages": len(first_chunk_message),
                    "completion_messages": len(completion_message)
                },
                "audio_analysis": {
                    "total_chunks": len(audio_chunks),
                    "total_audio_size": sum(len(chunk.get("audio_chunk", "")) for chunk in audio_chunks),
                    "chunk_size_consistency": self._analyze_chunk_sizes(audio_chunks)
                },
                "timing_analysis": {
                    "first_chunk_latency": first_chunk_message[0]["latency_ms"] if first_chunk_message else None,
                    "completion_summary": completion_message[0]["summary"] if completion_message else None
                }
            }
            
            logger.info(f"✅ Basic streaming test passed: {len(audio_chunks)} chunks in {duration:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"❌ Basic streaming test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time
            }
    
    async def test_concurrent_sessions(self) -> Dict[str, Any]:
        """Test multiple concurrent streaming sessions"""
        logger.info("🧪 Testing concurrent streaming sessions...")
        
        num_sessions = 3
        sessions = []
        
        start_time = time.time()
        
        try:
            # Create multiple concurrent sessions
            tasks = []
            for i in range(num_sessions):
                mock_websocket = MockWebSocket()
                session_id = f"concurrent_session_{i:03d}"
                llm_stream = LLMStreamingSimulator.create_llm_stream(f"Session {i} response")
                
                task = self.websocket_handler.handle_llm_response_with_streaming_tts(
                    mock_websocket, session_id, llm_stream
                )
                tasks.append((task, mock_websocket, session_id))
            
            # Run all sessions concurrently
            results = await asyncio.gather(*[task for task, _, _ in tasks], return_exceptions=True)
            
            duration = time.time() - start_time
            
            # Analyze results
            successful_sessions = 0
            total_chunks = 0
            
            for i, (result, (_, websocket, session_id)) in enumerate(zip(results, tasks)):
                if not isinstance(result, Exception):
                    successful_sessions += 1
                    audio_chunks = websocket.get_messages_by_type("audio_chunk")
                    total_chunks += len(audio_chunks)
                    logger.info(f"📊 Session {session_id}: {len(audio_chunks)} chunks")
                else:
                    logger.error(f"❌ Session {session_id} failed: {result}")
            
            result = {
                "success": successful_sessions == num_sessions,
                "total_duration": round(duration, 2),
                "sessions_tested": num_sessions,
                "successful_sessions": successful_sessions,
                "total_audio_chunks": total_chunks,
                "average_chunks_per_session": round(total_chunks / num_sessions, 1) if num_sessions > 0 else 0,
                "concurrency_efficiency": round(successful_sessions / num_sessions, 2)
            }
            
            logger.info(f"✅ Concurrent test: {successful_sessions}/{num_sessions} sessions successful")
            return result
            
        except Exception as e:
            logger.error(f"❌ Concurrent streaming test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time
            }
    
    async def test_error_handling(self) -> Dict[str, Any]:
        """Test error handling in streaming TTS"""
        logger.info("🧪 Testing error handling...")
        
        mock_websocket = MockWebSocket()
        session_id = "error_test_session"
        
        start_time = time.time()
        
        try:
            # Create a failing LLM stream
            async def failing_llm_stream():
                yield "This will work fine"
                await asyncio.sleep(0.1)
                yield "This too"
                await asyncio.sleep(0.1)
                raise Exception("Simulated LLM failure")
            
            # Run streaming TTS with failing stream
            await self.websocket_handler.handle_llm_response_with_streaming_tts(
                mock_websocket, session_id, failing_llm_stream()
            )
            
            duration = time.time() - start_time
            
            # Analyze error handling
            error_messages = mock_websocket.get_messages_by_type("tts_streaming_error")
            audio_chunks = mock_websocket.get_messages_by_type("audio_chunk")
            
            result = {
                "success": len(error_messages) > 0,  # Should have error messages
                "duration": round(duration, 2),
                "error_messages": len(error_messages),
                "chunks_before_error": len(audio_chunks),
                "error_details": error_messages[0] if error_messages else None
            }
            
            logger.info(f"✅ Error handling test: {len(error_messages)} error messages, {len(audio_chunks)} chunks processed")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error handling test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time
            }
    
    async def test_stream_status_tracking(self) -> Dict[str, Any]:
        """Test stream status tracking functionality"""
        logger.info("🧪 Testing stream status tracking...")
        
        mock_websocket = MockWebSocket()
        session_id = "status_test_session"
        
        start_time = time.time()
        
        try:
            # Check initial status (should not exist)
            initial_status = self.websocket_handler.get_stream_status(session_id)
            
            # Start streaming in background
            llm_stream = LLMStreamingSimulator.create_llm_stream("Status tracking test")
            streaming_task = asyncio.create_task(
                self.websocket_handler.handle_llm_response_with_streaming_tts(
                    mock_websocket, session_id, llm_stream
                )
            )
            
            # Wait a bit and check active status
            await asyncio.sleep(0.5)
            active_status = self.websocket_handler.get_stream_status(session_id)
            
            # Complete streaming
            await streaming_task
            
            # Check final status
            final_status = self.websocket_handler.get_stream_status(session_id)
            
            duration = time.time() - start_time
            
            result = {
                "success": True,
                "duration": round(duration, 2),
                "status_progression": {
                    "initial_status": initial_status["status"],
                    "active_status": active_status["status"] if "status" in active_status else "unknown",
                    "final_status": final_status["status"]
                },
                "active_session_data": {
                    "chunks_during_active": active_status.get("chunks_sent", 0),
                    "audio_kb_during_active": active_status.get("total_audio_kb", 0),
                    "processing_rate": active_status.get("processing_rate", 0)
                }
            }
            
            logger.info(f"✅ Status tracking test: {initial_status['status']} → {active_status.get('status', 'unknown')} → {final_status['status']}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Status tracking test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time
            }
    
    def _analyze_chunk_sizes(self, audio_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze audio chunk size consistency"""
        if not audio_chunks:
            return {"consistent": False, "reason": "no_chunks"}
        
        chunk_sizes = [len(chunk.get("audio_chunk", "")) for chunk in audio_chunks]
        avg_size = sum(chunk_sizes) / len(chunk_sizes)
        size_variance = sum((size - avg_size) ** 2 for size in chunk_sizes) / len(chunk_sizes)
        
        return {
            "consistent": size_variance < avg_size * 0.5,  # Less than 50% variance
            "average_size": round(avg_size, 1),
            "size_variance": round(size_variance, 1),
            "min_size": min(chunk_sizes),
            "max_size": max(chunk_sizes),
            "total_chunks": len(chunk_sizes)
        }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests"""
        logger.info("🚀 Starting streaming TTS integration tests...")
        
        test_suite_start = time.time()
        
        # Run all tests
        tests = [
            ("basic_streaming", self.test_basic_streaming_flow),
            ("concurrent_sessions", self.test_concurrent_sessions),
            ("error_handling", self.test_error_handling),
            ("status_tracking", self.test_stream_status_tracking)
        ]
        
        results = {}
        successful_tests = 0
        
        for test_name, test_func in tests:
            logger.info(f"\n--- Running {test_name} test ---")
            try:
                test_result = await test_func()
                results[test_name] = test_result
                if test_result.get("success", False):
                    successful_tests += 1
                    logger.info(f"✅ {test_name}: PASSED")
                else:
                    logger.error(f"❌ {test_name}: FAILED")
            except Exception as e:
                logger.error(f"❌ {test_name}: EXCEPTION - {e}")
                results[test_name] = {"success": False, "error": str(e)}
        
        total_duration = time.time() - test_suite_start
        
        # Create comprehensive summary
        summary = {
            "test_suite_summary": {
                "total_tests": len(tests),
                "successful_tests": successful_tests,
                "failed_tests": len(tests) - successful_tests,
                "success_rate": round(successful_tests / len(tests), 2),
                "total_duration": round(total_duration, 2)
            },
            "individual_test_results": results,
            "overall_success": successful_tests == len(tests)
        }
        
        logger.info(f"\n🏁 Test Suite Complete: {successful_tests}/{len(tests)} tests passed in {total_duration:.2f}s")
        
        return summary

# Standalone test runner
async def main():
    """Main test runner function"""
    logger.info("🎬 Starting Streaming TTS Integration Test Suite")
    
    # Create and run test suite
    test_suite = StreamingTTSIntegrationTest()
    results = await test_suite.run_all_tests()
    
    # Print detailed results
    print("\n" + "="*80)
    print("STREAMING TTS INTEGRATION TEST RESULTS")
    print("="*80)
    
    summary = results["test_suite_summary"]
    print(f"Overall Success: {'✅ PASS' if results['overall_success'] else '❌ FAIL'}")
    print(f"Tests Passed: {summary['successful_tests']}/{summary['total_tests']}")
    print(f"Success Rate: {summary['success_rate']*100:.1f}%")
    print(f"Total Duration: {summary['total_duration']:.2f} seconds")
    
    print(f"\nIndividual Test Results:")
    for test_name, test_result in results["individual_test_results"].items():
        status = "✅ PASS" if test_result.get("success", False) else "❌ FAIL"
        duration = test_result.get("duration", 0)
        print(f"  {test_name}: {status} ({duration:.2f}s)")
        
        if not test_result.get("success", False) and "error" in test_result:
            print(f"    Error: {test_result['error']}")
    
    print("\n" + "="*80)
    
    # Return exit code based on success
    return 0 if results["overall_success"] else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
