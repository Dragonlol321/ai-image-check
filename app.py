import os
import sys
import uuid
from pathlib import Path

from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from PIL import Image, UnidentifiedImageError

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 15 * 1024 * 1024  # 15 MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

_detector = None
_model_error = None

def get_detector():
    """Load the model once, on the first analysis request."""
    global _detector, _model_error
    if _detector is not None:
        return _detector
    if _model_error:
        raise RuntimeError(_model_error)
    try:
        from huggingface_hub import snapshot_download
        model_path = snapshot_download("abacusai/Smaug-AI-Image-Detector")
        sys.path.insert(0, model_path)
        from smaug_image_detect import SmaugImageDetect
        _detector = SmaugImageDetect.from_pretrained(model_path)
        return _detector
    except Exception as exc:
        _model_error = (
            "Не удалось загрузить модель. Проверь подключение к интернету, "
            "свободное место на диске и установку зависимостей. Подробности: "
            + str(exc)
        )
        raise RuntimeError(_model_error)

@app.get("/")
def home():
    return render_template("index.html")

@app.post("/api/check")
def check_image():
    if "image" not in request.files:
        return jsonify(error="Выбери изображение."), 400
    file = request.files["image"]
    if not file or not file.filename:
        return jsonify(error="Файл не выбран."), 400

    suffix = Path(secure_filename(file.filename)).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        return jsonify(error="Поддерживаются JPG, PNG и WEBP."), 400

    temp_path = UPLOAD_DIR / f"{uuid.uuid4().hex}{suffix}"
    try:
        file.save(temp_path)
        # Verify actual image content rather than trusting only the extension.
        with Image.open(temp_path) as im:
            im.verify()
        with Image.open(temp_path) as im:
            width, height = im.size
            if width < 64 or height < 64:
                return jsonify(error="Изображение слишком маленькое (минимум 64×64)."), 400

        detector = get_detector()
        score = float(detector(str(temp_path)))
        score = max(0.0, min(1.0, score))
        percent = round(score * 100, 1)

        if score >= 0.5:
            verdict = "Похоже на изображение, созданное ИИ"
            level = "ai"
        else:
            verdict = "Похоже на изображение, созданное человеком"
            level = "human"

        return jsonify(
            score=percent,
            verdict=verdict,
            level=level,
            width=width,
            height=height,
            model="Smaug-AI-Image-Detector"
        )
    except UnidentifiedImageError:
        return jsonify(error="Файл не удалось распознать как изображение."), 400
    except RuntimeError as exc:
        return jsonify(error=str(exc)), 503
    except Exception as exc:
        app.logger.exception("Image analysis failed")
        return jsonify(error="Ошибка анализа: " + str(exc)), 500
    finally:
        try:
            temp_path.unlink(missing_ok=True)
        except Exception:
            pass

@app.errorhandler(413)
def too_large(_):
    return jsonify(error="Файл слишком большой. Максимум — 15 МБ."), 413

if __name__ == "__main__":
    print("AI Image Check запущен: http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
