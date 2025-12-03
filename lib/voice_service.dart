import 'package:speech_to_text/speech_to_text.dart' as stt;

class VoiceService {
  // המשתנה שמחזיק את המנוע של גוגל
  late stt.SpeechToText _speech;
  bool _isListening = false;

  // פונקציה 1: אתחול (בודקת שיש מיקרופון ואישור)
  Future<bool> initialize() async {
    _speech = stt.SpeechToText();
    // מנסה להתחבר לשירות
    bool available = await _speech.initialize(
      onError: (val) => print('Error: $val'),
      onStatus: (val) => print('Status: $val'),
    );
    return available;
  }

  // פונקציה 2: הקשבה (מתחילה להקליט)
  void listen(Function(String) onResult) {
    if (!_isListening) {
      _isListening = true;
      _speech.listen(
        onResult: (val) {
          onResult(val.recognizedWords);
        },
        localeId: 'he_IL', // <--- קריטי: מכריח עברית
        cancelOnError: true,
        listenMode: stt.ListenMode.confirmation,
      );
    }
  }

  // פונקציה 3: עצירה
  void stop() {
    _speech.stop();
    _isListening = false;
  }
}
