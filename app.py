import os
import time
import urllib.parse
import requests
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

app = Flask(__name__)
client = Groq(api_key="your_api_key_here")  # Replace with your actual API key

UNSPLASH_KEY = "wscqaLAsM8hoZA572U4x90U3EVcFEBkZUMXBzxhfYlk"

FORMAT_INSTRUCTIONS = {
    "social": {
        "label": "Social Media Post",
        "instruction": "Write a social media post (Instagram/Twitter style). Include a hook, 2-3 short punchy lines, relevant emojis, and 5 hashtags.",
    },
    "banner": {
        "label": "Banner Ad",
        "instruction": "Write a banner ad with clearly labeled sections:\nHEADLINE: (max 8 words)\nSUBHEADLINE: (max 15 words)\nCTA BUTTON: (2-4 words)",
    },
    "email": {
        "label": "Email Campaign",
        "instruction": "Write an email with clearly labeled sections:\nSUBJECT LINE:\nPREVIEW TEXT:\nGREETING:\nBODY: (2-3 short paragraphs)\nCALL-TO-ACTION:",
    },
}

TONE_DESCRIPTIONS = {
    "fun":    "energetic, playful, and witty — use humor, casual language, and excitement",
    "formal": "professional, polished, and authoritative — use clean business language",
    "bold":   "confident, powerful, and direct — use strong verbs and commanding language",
}

PLATFORM_DESCRIPTIONS = {
    "instagram": "optimized for Instagram — visual, emoji-rich, hashtag-heavy",
    "facebook":  "optimized for Facebook — conversational, community-focused",
    "twitter":   "optimized for Twitter/X — punchy, under 280 chars, witty",
    "linkedin":  "optimized for LinkedIn — professional, achievement-focused",
    "youtube":   "optimized for YouTube — descriptive, engaging, call-to-action heavy",
}


def build_prompt(product_name, description, audience, ad_format, tone, platform):
    fmt   = FORMAT_INSTRUCTIONS[ad_format]
    tdesc = TONE_DESCRIPTIONS[tone]
    pdesc = PLATFORM_DESCRIPTIONS.get(platform, "")
    return f"""You are an expert advertising copywriter. Create high-converting ad copy.

PRODUCT NAME: {product_name}
PRODUCT DESCRIPTION: {description}
TARGET AUDIENCE: {audience}
AD FORMAT: {fmt['label']}
PLATFORM: {platform.upper()} — {pdesc}
TONE: {tone.upper()} — {tdesc}

TASK: {fmt['instruction']}

Tailor the copy specifically for {audience} on {platform.upper()}.
Be creative, compelling, and on-brand. Focus on benefits over features.
Return ONLY the ad copy — no explanations or extra commentary."""


def get_image_url(product_name, description):
    """Fetch relevant image from Unsplash — free, instant, 100% relevant."""
    keyword = (product_name + " " + description).strip()
    try:
        res = requests.get(
            "https://api.unsplash.com/photos/random",
            params={"query": keyword, "orientation": "landscape"},
            headers={"Authorization": f"Client-ID {UNSPLASH_KEY}"},
            timeout=10
        )
        data = res.json()
        return data["urls"]["regular"]
    except Exception:
        # fallback to loremflickr if unsplash fails
        kw = urllib.parse.quote(product_name)
        return f"https://loremflickr.com/800/600/{kw}?random={int(time.time())}"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    try:
        data         = request.get_json()
        product_name = data.get("product_name", "").strip()
        description  = data.get("description",  "").strip()
        audience     = data.get("audience",      "general audience").strip()
        ad_format    = data.get("format",        "social")
        tone         = data.get("tone",          "bold")
        platform     = data.get("platform",      "instagram")

        if not product_name or not description:
            return jsonify({"error": "Please enter a product name and description."}), 400

        prompt   = build_prompt(product_name, description, audience, ad_format, tone, platform)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
        )
        ad_copy   = response.choices[0].message.content.strip()
        image_url = get_image_url(product_name, description)

        return jsonify({
            "ad_copy":      ad_copy,
            "image_url":    image_url,
            "format_label": FORMAT_INSTRUCTIONS[ad_format]["label"],
            "tone":         tone,
            "platform":     platform,
        })

    except Exception as e:
        err = str(e)
        if "invalid_api_key" in err.lower() or "auth" in err.lower():
            return jsonify({"error": "❌ Invalid API key. Check your keys."}), 401
        if "rate_limit" in err.lower() or "429" in err:
            return jsonify({"error": "⏳ Rate limit hit. Wait a moment and retry."}), 429
        return jsonify({"error": f"Something went wrong: {err}"}), 500


if __name__ == "__main__":
    print("\n✅  AdForge AI is running!")
    print("🌐  Open in browser → http://127.0.0.1:5000\n")
    app.run(debug=True)