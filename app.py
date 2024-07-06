import os
import asyncio
import json
from aiohttp import web
from websockets import serve
import aiohttp_cors

# Directory containing the videos
VIDEO_DIR = "Videos"

# Get the list of videos in the VIDEO_DIR
def get_video_list():
    return [f for f in os.listdir(VIDEO_DIR) if f.endswith('.mp4')]

async def get_videos(request):
    videos = get_video_list()
    response_data = json.dumps(videos)
    print(f"Sending response: {response_data}")
    return web.Response(text=response_data, content_type='application/json')

# WebSocket handler
async def video_stream(websocket, path):
    async for message in websocket:
        if message.startswith("SELECT "):
            video_name = message.split(" ", 1)[1]
            video_path = os.path.join(VIDEO_DIR, video_name)
            if os.path.exists(video_path):
                with open(video_path, "rb") as video_file:
                    while True:
                        chunk = video_file.read(1024*1024)  # Read 1MB at a time
                        if not chunk:
                            break
                        await websocket.send(chunk)
            else:
                await websocket.send(f"Error: Video '{video_name}' not found")

# Set up the HTTP server
app = web.Application()

# Setup CORS
cors = aiohttp_cors.setup(app, defaults={
    "*": aiohttp_cors.ResourceOptions(
        allow_credentials=True,
        expose_headers="*",
        allow_headers="*",
    )
})

# Add routes
cors.add(app.router.add_get('/videos', get_videos))

# Set up the WebSocket server
async def start_websocket_server():
    await serve(video_stream, "localhost", 8765)

# Run both servers
async def run_servers():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8081)
    await site.start()
    print(f"HTTP server started at http://localhost:8081")
    
    await start_websocket_server()
    print(f"WebSocket server started at ws://localhost:8765")
    
    while True:
        await asyncio.sleep(3600)  # Keep the server running

if __name__ == "__main__":
    asyncio.run(run_servers())
