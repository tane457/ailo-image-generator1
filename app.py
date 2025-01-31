from flask import Flask, render_template, request, jsonify, redirect
from flask_cors import CORS
import requests
import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# Gemini API yapılandırması
genai.configure(api_key='AIzaSyBWNLTksgP_URKODwc4EL68R9nAM5tAgGg')
model = genai.GenerativeModel('gemini-pro')

def generate_image(prompt):
    api_url = "https://prompt.glitchy.workers.dev/gen"
    params = {
        "key": prompt,
        "t": 0.2,
        "f": "dalle3",
        "demo": "true",
        "count": 1
    }

    try:
        response = requests.get(api_url, params=params)
        data = response.json()

        if data["status"] == 1 and "images" in data:
            return {
                "success": True,
                "image_url": data["images"][0]["imagedemo1"][0]
            }
        return {"success": False}

    except Exception as e:
        print(f"Hata: {str(e)}")
        return {"success": False}

@app.route('/')
@cache.cached(timeout=3600)
def home():
    return render_template('home.html', 
        meta_title="Turuncu.online | Yapay Zeka Asistanı",
        meta_description="Turuncu.online ile yapay zeka destekli içerik üretimi, resim oluşturma ve sosyal medya optimizasyonu yapın.",
        meta_keywords="yapay zeka, AI, içerik üretimi, resim oluşturma, sosyal medya, turuncu.online"
    )

@app.route('/image-generator')
@cache.cached(timeout=3600)
def image_generator():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
@limiter.limit("10 per minute")
def generate():
    prompt = request.json.get('prompt')
    result = generate_image(prompt)
    return jsonify(result)

@app.route('/chat')
@cache.cached(timeout=3600)
def chat():
    return render_template('chat.html')

@app.route('/chat', methods=['POST'])
@limiter.limit("20 per minute")
def chat_response():
    message = request.json.get('message')
    
    try:
        response = model.generate_content(message)
        return jsonify({
            "success": True,
            "response": response.text
        })
    except Exception as e:
        print(f"Gemini API Hatası: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Bir hata oluştu"
        })

@app.route('/music')
@cache.cached(timeout=3600)
def music():
    return render_template('music.html')

@app.route('/search-music')
@limiter.limit("30 per minute")
def search_music():
    query = request.args.get('query', '')
    try:
        response = requests.get(f'https://jiosaavn-api-codyandersan.vercel.app/search/all?query={query}&page=1&limit=6')
        data = response.json()
        
        # API yanıtını düzenleme
        songs = data.get('data', {}).get('songs', {}).get('results', [])
        formatted_songs = []
        
        for song in songs:
            formatted_songs.append({
                'name': song.get('title', ''),
                'primaryArtists': song.get('primaryArtists', ''),
                'image': song.get('image', [{}])[2].get('link', ''),  # 500x500 resim
                'url': song.get('url', ''),
                'album': song.get('album', '')
            })
            
        return jsonify({
            'success': True,
            'results': formatted_songs
        })
    except Exception as e:
        print(f"Müzik API Hatası: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Bir hata oluştu'
        })

@app.route('/video')
@cache.cached(timeout=3600)
def video():
    return render_template('video.html')

@app.route('/get-video-info', methods=['POST'])
@limiter.limit("10 per minute")
def get_video_info():
    url = request.json.get('url')
    try:
        api_url = f"https://aiovd.hideme.eu.org/?url={url}"
        response = requests.get(api_url)
        data = response.json()
        
        if data["status"] == "success":
            return jsonify({
                "success": True,
                "metadata": data
            })
        return jsonify({
            "success": False,
            "error": "Video bilgileri alınamadı"
        })
    except Exception as e:
        print(f"Video API Hatası: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Bir hata oluştu"
        })

@app.route('/social')
@cache.cached(timeout=3600)
def social():
    return render_template('social.html')

@app.route('/improve-post', methods=['POST'])
@limiter.limit("20 per minute")
def improve_post():
    data = request.json
    platform = data.get('platform')
    topic = data.get('topic')
    content = data.get('content')
    
    prompt = f"""Platform: {platform}
    Konu: {topic}
    İçerik: {content}
    
    1. İçeriği iyileştir
    2. Güncel ve trend 5 hashtag öner
    3. 3 farklı içerik önerisi sun
    """
    
    try:
        response = model.generate_content(prompt)
        # Yanıtı işle ve formatla
        
        return jsonify({
            "success": True,
            "improved_content": "İyileştirilmiş içerik...",
            "hashtags": ["#trend2024", "#digital", "#ai", "#tech", "#innovation"],
            "trend_suggestions": [
                "Trend öneri 1...",
                "Trend öneri 2...",
                "Trend öneri 3..."
            ]
        })
    except Exception as e:
        print(f"Hata: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Bir hata oluştu"
        })

@app.before_request
def redirect_to_domain():
    if request.headers.get('X-Forwarded-Proto') == 'http':
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)
        
    if request.headers.get('Host') != 'turuncu.online':
        url = 'https://turuncu.online' + request.path
        return redirect(url, code=301)

@app.before_request
def redirect_www():
    if request.headers.get('Host').startswith('www.'):
        url = request.url.replace('www.', '', 1)
        return redirect(url, code=301)

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    