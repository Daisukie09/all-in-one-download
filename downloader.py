#!/usr/bin/env python3
"""
Universal Video Downloader using yt-dlp
Supports: YouTube, TikTok, Instagram, Twitter/X, Facebook, and many more platforms
"""

import os
import sys
import subprocess
import json
import argparse
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

class VideoDownloader:
    def __init__(self, download_path=None):
        self.download_path = download_path or os.path.join(os.path.expanduser("~"), "Downloads", "VideoDownloads")
        Path(self.download_path).mkdir(parents=True, exist_ok=True)
        self.check_dependencies()
    
    def check_dependencies(self):
        """Check if yt-dlp is installed"""
        try:
            subprocess.run(['yt-dlp', '--version'], capture_output=True, check=True, timeout=10)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Installing yt-dlp...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'yt-dlp'], check=True)
    
    def get_video_info(self, url):
        """Get video information"""
        try:
            cmd = ['yt-dlp', '--dump-json', '--no-playlist', url]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
            info = json.loads(result.stdout)
            
            return {
                'ok': True,
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'uploader': info.get('uploader', 'Unknown'),
                'thumbnail': info.get('thumbnail', ''),
                'platform': self.detect_platform(url)
            }
        except Exception as e:
            return {'ok': False, 'error': str(e)}
    
    def detect_platform(self, url):
        """Detect platform from URL"""
        url_lower = url.lower()
        if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return 'youtube'
        elif 'tiktok.com' in url_lower:
            return 'tiktok'
        elif 'instagram.com' in url_lower:
            return 'instagram'
        elif 'facebook.com' in url_lower or 'fb.watch' in url_lower:
            return 'facebook'
        elif 'twitter.com' in url_lower or 'x.com' in url_lower:
            return 'twitter'
        elif 'reddit.com' in url_lower:
            return 'reddit'
        else:
            return 'direct'
    
    def download(self, url, quality='best'):
        """Download video and return the file path"""
        # Get filename template
        filename_template = os.path.join(self.download_path, '%(title)s_%(id)s.%(ext)s')
        
        # Build yt-dlp command
        if quality == 'audio':
            cmd = [
                'yt-dlp',
                '-x', '--audio-format', 'mp3',
                '-o', filename_template,
                '--no-playlist',
                '--quiet',
                '--no-warnings',
                url
            ]
        else:
            # Quality format mapping
            quality_formats = {
                '720': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
                '1080': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
                '1440': 'bestvideo[height<=1440]+bestaudio/best[height<=1440]',
                '4k': 'bestvideo[height<=2160]+bestaudio/best[height<=2160]',
                'best': 'bestvideo+bestaudio/best',
            }
            format_str = quality_formats.get(quality, quality_formats['best'])
            
            cmd = [
                'yt-dlp',
                '-f', format_str,
                '-o', filename_template,
                '--no-playlist',
                '--quiet',
                '--no-warnings',
                url
            ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=300)
            
            # Find the downloaded file
            files = list(Path(self.download_path).glob('*'))
            if files:
                # Get most recently modified file
                latest_file = max(files, key=os.path.getmtime)
                return {
                    'ok': True,
                    'filepath': str(latest_file),
                    'filename': os.path.basename(latest_file)
                }
            return {'ok': False, 'error': 'No file found'}
        except subprocess.TimeoutExpired:
            return {'ok': False, 'error': 'Download timeout'}
        except subprocess.CalledProcessError as e:
            return {'ok': False, 'error': e.stderr or 'Download failed'}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

# Global downloader instance
downloader = VideoDownloader()

class RequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress logging
    
    def do_GET(self):
        parsed = urlparse(self.path)
        
        if parsed.path == '/api/check':
            # Get video info
            params = parse_qs(parsed.query)
            url = params.get('url', [''])[0]
            
            if not url:
                self.send_json(400, {'ok': False, 'error': 'Missing url parameter'})
                return
            
            info = downloader.get_video_info(url)
            self.send_json(200, {
                'ok': True,
                'platform': info.get('platform', 'unknown'),
                'url': url,
                'title': info.get('title', ''),
                'message': f"Detected platform: {info.get('platform', 'unknown')}"
            })
        
        elif parsed.path == '/api/download':
            # Download video
            params = parse_qs(parsed.query)
            url = params.get('url', [''])[0]
            quality = params.get('quality', ['best'])[0]
            
            if not url:
                self.send_json(400, {'ok': False, 'error': 'Missing url parameter'})
                return
            
            # Start download in background thread
            result = downloader.download(url, quality)
            
            if result['ok']:
                # Read and serve the file
                filepath = result['filepath']
                filename = result['filename']
                
                try:
                    with open(filepath, 'rb') as f:
                        data = f.read()
                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'video/mp4')
                    self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                    self.send_header('Content-Length', len(data))
                    self.end_headers()
                    self.wfile.write(data)
                    
                    # Clean up file after sending
                    try:
                        os.remove(filepath)
                    except:
                        pass
                    return
                except Exception as e:
                    self.send_json(500, {'ok': False, 'error': str(e)})
                    return
            else:
                self.send_json(500, {'ok': False, 'error': result.get('error', 'Download failed')})
        
        else:
            self.send_json(404, {'error': 'Not found'})
    
    def send_json(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

def run_server(port=3001):
    server = HTTPServer(('127.0.0.1', port), RequestHandler)
    print(f"Python downloader server running on http://127.0.0.1:{port}")
    server.serve_forever()

if __name__ == '__main__':
    run_server()
