# Agora Video Call Setup for Doctor Webinars

## Installation

Run the following command to install Agora RTC SDK:

```bash
npm install agora-rtc-sdk-ng
```

## Environment Variables

Add these to your `.env` file:

```env
VITE_AGORA_APP_ID=your_agora_app_id_here
```

## Steps to Get Agora App ID:

1. Go to https://console.agora.io/
2. Sign up or login
3. Create a new project
4. Get your App ID from the project settings
5. Add it to your `.env` file

## Features Implemented:

- ✅ Host video stream
- ✅ Multiple participant view
- ✅ Screen sharing
- ✅ Mute/Unmute audio
- ✅ Camera on/off
- ✅ Leave call functionality
- ✅ Participant list
- ✅ Chat integration
- ✅ Recording controls (for host)

## Usage:

When a doctor clicks "Start" or "Join Stream" on a webinar, the Agora video room will be initialized using the `agora_channel_name` and `agora_token` from the webinar details.

