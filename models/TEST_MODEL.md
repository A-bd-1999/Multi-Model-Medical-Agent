# Testing the Bone Fracture Model

## Step 1: Install AI Dependencies

```bash
pip install -r requirements-ai.txt
```

This installs:
- TensorFlow (AI framework)
- OpenCV (image processing)
- NumPy (numerical operations)
- gdown (Google Drive downloader)

---

## Step 2: Test the Model Directly

```bash
cd models
python bone_model.py path/to/test_xray.jpg
```

**Expected Output:**
```
Downloading fracture model...
Model downloaded: models/fracture_model.keras
Loading bone model: models/fracture_model.keras
Bone model loaded OK

Finding    : Fracture Detected
Confidence : 87.3%
Model      : bone_fracture_v1.0
```

---

## Step 3: Test via Flask API

Start the server:
```bash
python flask_app.py
```

Upload an X-ray via the frontend at `http://localhost:5000`

---

## Step 4: Check Model Location

After first run, the model file will be saved at:
```
C:\Users\user\Desktop\Multi-Model-Medical-Agent\models\fracture_model.keras
```

Size: ~50-100 MB (depending on model architecture)

---

## Troubleshooting

### Error: "gdown not installed"
```bash
pip install gdown
```

### Error: "TensorFlow not installed"
```bash
pip install tensorflow
```

### Error: "Model download failed"
- Check your internet connection
- Make sure Google Drive link is accessible
- Try downloading manually and place in `models/fracture_model.keras`

### Error: "CUDA/GPU errors"
```bash
# Use CPU-only version instead:
pip uninstall tensorflow
pip install tensorflow-cpu
```

---

## Model Behavior

| Input | Output |
|---|---|
| X-ray with fracture | `"Fracture Detected"` + confidence > 0.5 |
| Normal X-ray | `"No Fracture Detected — Normal"` + confidence > 0.5 |
| Invalid image | Error with fallback stub result |

---

## Performance Notes

- **First prediction**: ~30-60 seconds (downloads + loads model)
- **Subsequent predictions**: ~2-5 seconds (model already in memory)
- **Model size**: ~50-100 MB on disk
- **Memory usage**: ~500 MB RAM when loaded
