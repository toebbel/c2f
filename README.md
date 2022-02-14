Call To The Future
=================

Make a phone call to the future: 🇸🇪 +46766860735 🇸🇪

> This is a highly experimental service. Don't tell any secrets on the phone. There are no safety measures that prevent attackers from stealing your recording.

This idea is heavily inspired by [https://www.futureme.org/](futureme.org)

## Additionally, required tools
- ffmpeg and ffprobe must be installed (docker container coming at some point)
- requirements.txt / venv is (maybe) not 100% correct.

## Ideas for the future:
- Limit number of recordings to n queued calls
- Give user option to schedule call via voice recognition or sending a SMS with a link for settings
- Allowing users to store a backup email address, in case their phone number changes
- Send sms with link to recording when recording can't be played back after X attempts
- Cropping of recording is based on hard-coded values
- Read the action logs from 46elks to verify authenticity of call inputs
- https
- a real database (aka not sqlite)
- logging and alerts on errors
- using blob storage (s3 or similar) for recordings, instead of sqlite database

## Why?
For fun and ~~profit~~ learning Python