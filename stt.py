from ellma.modules.tts import TextToSpeech

# Inicjalizacja TTS
tts = TextToSpeech()

# Przykładowy tekst do zamiany na mowę
text = "Witaj, to jest przykład działania syntezy mowy."

# Wygenerowanie mowy i zapis do pliku
output_file = "output.wav"
tts.speak(text, output_file)

# Odtworzenie wygenerowanej mowy
tts.play_audio(output_file)


from ellma.modules.stt import SpeechToText

# Inicjalizacja STT
stt = SpeechToText()

# Nagranie dźwięku z mikrofonu (domyślnie 5 sekund)
print("Mów teraz...")
audio_data = stt.record_audio()

# Alternatywnie: wczytanie pliku audio
# audio_data = stt.load_audio("sciezka/do/pliku.wav")

# Rozpoznanie mowy
text = stt.recognize(audio_data)
print("Rozpoznany tekst:", text)