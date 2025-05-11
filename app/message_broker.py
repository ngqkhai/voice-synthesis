import os
import json
import asyncio
import logging
import aio_pika
from aio_pika.abc import AbstractConnection, AbstractChannel, AbstractQueue
from dotenv import load_dotenv
import httpx

# Import request model and synthesis function from main
# from main import VoiceRequest, synthesize_voice

# Load environment variables
load_dotenv()

# RabbitMQ configuration
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqps://xugpluia:XsNjsZwBkRwz2StOuqE7FxBzy1u4n_mi@fuji.lmq.cloudamqp.com/xugpluia")
SCRIPT_VOICE_QUEUE = os.getenv("SCRIPT_VOICE_QUEUE", "script_voice")
VOICE_RESULTS_EXCHANGE = os.getenv("VOICE_RESULTS_EXCHANGE", "voice_results")
VOICE_RESULTS_QUEUE = os.getenv("VOICE_RESULTS_QUEUE", "voice_results")
VOICE_RESULTS_ROUTING_KEY = os.getenv("VOICE_RESULTS_ROUTING_KEY", "voice.generated")
# URL for calling the local synthesize API endpoint
VOICE_SERVICE_URL = os.getenv("VOICE_SERVICE_URL", "http://localhost:8000")

# Logger setup
logger = logging.getLogger("voice-synthesis.message_broker")

class VoiceMessageBroker:
    def __init__(self):
        self.connection: AbstractConnection = None
        self.channel: AbstractChannel = None
        self.script_queue: AbstractQueue = None
        self.voice_queue: AbstractQueue = None
        self.exchange: aio_pika.Exchange = None

    async def connect(self):
        # Connect to RabbitMQ
        self.connection = await aio_pika.connect_robust(RABBITMQ_URL)
        self.channel = await self.connection.channel()
        # Declare the task queue for scripts
        self.script_queue = await self.channel.declare_queue(
            SCRIPT_VOICE_QUEUE,
            durable=True
        )
        # Declare the queue for voice results
        self.voice_queue = await self.channel.declare_queue(
            VOICE_RESULTS_QUEUE,
            durable=True
        )
        # Declare the exchange for voice results
        self.exchange = await self.channel.declare_exchange(
            VOICE_RESULTS_EXCHANGE,
            aio_pika.ExchangeType.TOPIC,
            durable=True
        )
        await self.voice_queue.bind(self.exchange, routing_key=VOICE_RESULTS_ROUTING_KEY)
        logger.info(f"Connected to RabbitMQ: queue={SCRIPT_VOICE_QUEUE}, exchange={VOICE_RESULTS_EXCHANGE}")

    async def consume_messages(self):
        # Debug log to confirm consume_messages was called
        logger.info("🔔 consume_messages() called")
        # Start consuming messages from the script_voice queue
        async with self.script_queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        body = message.body.decode()
                        try:
                            data = json.loads(body)
                        except json.JSONDecodeError:
                            import ast
                            data = ast.literal_eval(body)
                        await self.handle_message(data)
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")

    async def handle_message(self, data):
        # Debug log to confirm handle_message is processing data
        logger.info(f"🔧 handle_message() called with data: {data}")
        # data contains keys: script, script_id, collection_id, etc.
        script = data.get("script", {})
        script_id = data.get("script_id")
        collection_id = data.get("collection_id")
        # Synthesize each scene with voiceover and collect results
        scenes = script.get("scenes", [])
        voice_name = script.get("voice", "Neural2-A")
        language = script.get("language", "en-US")
        voice_id = language + "-" + voice_name
        speed = float(os.getenv("DEFAULT_SPEED", "1"))
        scene_results = []
        async with httpx.AsyncClient() as client:
            for scene in scenes:
                if not scene.get("voiceover", True):
                    continue
                scene_id = scene.get("scene_id")
                scene_text = scene.get("script", "").strip()
                if not scene_text:
                    logger.warning(f"Scene {scene_id} has empty script, skipping")
                    continue
                # Call the local synthesize API for this scene with retry/backoff
                resp_json = None
                timeout = httpx.Timeout(10.0, read=10.0)
                max_retries = 3
                for attempt in range(1, max_retries + 1):
                    try:
                        logger.info(f"Attempt {attempt}: POST {VOICE_SERVICE_URL}/api/v1/voice/synthesize for scene {scene_id}")
                        res = await client.post(
                            f"{VOICE_SERVICE_URL}/api/v1/voice/synthesize",
                            json={
                                "text": scene_text,
                                "voice_id": voice_id,
                                "language": language,
                                "speed": speed
                            },
                            timeout=timeout
                        )
                        res.raise_for_status()
                        resp_json = res.json()
                        break
                    except httpx.HTTPStatusError as status_err:
                        # Don't retry on 4xx errors
                        logger.error(
                            f"HTTP status {status_err.response.status_code} error for scene {scene_id}: {status_err.response.text}"
                        )
                        break
                    except (httpx.RequestError, httpx.TimeoutException) as req_err:
                        logger.warning(
                            f"Request error on attempt {attempt} for scene {scene_id}: {repr(req_err)}"
                        )
                        if attempt < max_retries:
                            backoff = 2 ** attempt
                            logger.info(f"Waiting {backoff}s before retry...")
                            await asyncio.sleep(backoff)
                            continue
                        else:
                            logger.error(f"Max retries reached for scene {scene_id}. Skipping.")
                            break
                    except Exception:
                        logger.exception(f"Unexpected error synthesizing scene {scene_id}")
                        break
                if not resp_json:
                    continue  # Skip if all attempts failed
                # Collect result for this scene in order
                scene_results.append({
                    "scene_id": scene_id,
                    "voice_id": resp_json.get("voice_id"),
                    "audio_url": resp_json.get("audio_url"),
                    "cloudinary_url": resp_json.get("cloudinary_url"),
                    "duration": resp_json.get("duration")
                })
        # After processing all scenes, publish aggregated results to preserve order
        try:
            aggregated_payload = {
                "script_id": script_id,
                "collection_id": collection_id,
                "scene_voiceovers": scene_results
            }
            outgoing = aio_pika.Message(
                body=json.dumps(aggregated_payload).encode("utf-8"),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )
            logger.info(f"Publishing aggregated voice results for script_id: {script_id}")
            await self.exchange.publish(
                outgoing,
                routing_key=VOICE_RESULTS_ROUTING_KEY
            )
            logger.info(f"Published aggregated voice results for script_id: {script_id}")
        except Exception as e:
            logger.error(f"Error publishing aggregated voice results: {e}")

    async def close(self):
        # Close the RabbitMQ connection
        if self.connection:
            await self.connection.close()
            logger.info("RabbitMQ connection closed")
