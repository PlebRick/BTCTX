import subprocess

try:
    subprocess.run(["pdftk", "--version"], check=True)
    print("✅ pdftk is installed and available!")
except subprocess.CalledProcessError as e:
    print("❌ pdftk failed to run:", e)
except FileNotFoundError:
    print("❌ pdftk not found in PATH.")
