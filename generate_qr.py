import qrcode
import os

# Create a folder to store QR codes
output_folder = "generated_qrcodes"
os.makedirs(output_folder, exist_ok=True)

# Define items and how many QR codes to create
items = {
    "HDMI": 10,
    "REM": 10
}

# Generate QR codes
for prefix, count in items.items():
    for i in range(1, count + 1):
        code_text = f"{prefix}{i:03}"  # e.g., HDMI001, REM001
        img = qrcode.make(code_text)
        img_path = os.path.join(output_folder, f"{code_text}.png")
        img.save(img_path)
        print(f"✅ Generated: {img_path}")

print("\nAll QR codes generated successfully and saved in the 'generated_qrcodes' folder!")
