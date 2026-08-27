# QR Link Opener

English | [繁體中文](README.md)

An offline Windows utility for opening QR-code links from your screen. Press `Ctrl + Shift + Q`, select one QR code, review the result, then open its link or copy its contents.

## Features

- QR capture and decoding happen locally; screenshots and QR content are never uploaded.
- A URL is opened only after explicit confirmation.
- Supports `http`, `https`, and `line://` links. Windows and any installed LINE app decide which application receives a LINE link.
- Plain text, Wi-Fi configurations, and other non-URL payloads can only be copied; they are never executed.
- System-tray operation, global shortcut, multi-monitor selection, and configurable auto-start.

## Install and use

Download from the project's **Releases** page:

- `QR-Link-Opener-Setup-x.y.z.exe` — installer for most users.
- `QR-Link-Opener-x.y.z-portable.exe` — portable single-file edition.

After installation or launch, find the QR icon in the Windows notification area. Press `Ctrl + Shift + Q`, drag around one QR code, and choose **Open link** or **Copy**. Press `Esc` to cancel. If the shortcut is unavailable, start a scan from the tray menu.

## Security and SmartScreen

The first release is not code-signed, so Windows SmartScreen may show a warning. Download only from the official GitHub Releases page and verify the included `SHA256SUMS.txt` file:

```powershell
Get-FileHash .\QR-Link-Opener-1.0.0-portable.exe -Algorithm SHA256
```

## Build from source

Requires Windows and Python 3.12 or later.

```powershell
python -m venv build-venv
.\build-venv\Scripts\python.exe -m pip install -r requirements.txt
.\build-venv\Scripts\python.exe -m unittest discover -s tests -v
.\build.ps1
```

## Contributing and license

See [CONTRIBUTING.md](CONTRIBUTING.md). This project is released under the [MIT License](LICENSE).
