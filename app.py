from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

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
def home():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    prompt = request.json.get('prompt')
    result = generate_image(prompt)
    return jsonify(result)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)