import React, { useState, useRef, useEffect } from 'react';
import {
  MicrophoneIcon,
  StopIcon,
  SpeakerWaveIcon,
  ClockIcon,
  SignalIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { apiClient } from '../utils/api';
import { VoiceRecording, WebSocketMessage } from '../types';
import toast from 'react-hot-toast';
import classNames from 'classnames';

export default function VoiceDemo() {
  const [isRecording, setIsRecording] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [response, setResponse] = useState('');
  const [audioLevel, setAudioLevel] = useState(0);
  const [recordingTime, setRecordingTime] = useState(0);
  const [lastResponseTime, setLastResponseTime] = useState<number | null>(null);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const recordingTimerRef = useRef<NodeJS.Timeout | null>(null);

  const demoPrompts = [
    "Comment puis-je réinitialiser mon mot de passe ?",
    "Quels sont vos horaires d'ouverture ?",
    "Je souhaite connaître le statut de ma commande",
    "Comment puis-je contacter le support ?",
    "Y a-t-il des frais de livraison ?"
  ];

  useEffect(() => {
    return () => {
      // Cleanup
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 16000
        } 
      });
      
      streamRef.current = stream;

      // Setup audio level monitoring
      audioContextRef.current = new AudioContext();
      analyserRef.current = audioContextRef.current.createAnalyser();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      source.connect(analyserRef.current);
      
      analyserRef.current.fftSize = 256;
      const bufferLength = analyserRef.current.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);

      const updateAudioLevel = () => {
        if (analyserRef.current && isRecording) {
          analyserRef.current.getByteFrequencyData(dataArray);
          const average = dataArray.reduce((a, b) => a + b) / bufferLength;
          setAudioLevel(average / 255);
          requestAnimationFrame(updateAudioLevel);
        }
      };

      mediaRecorderRef.current = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });

      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        await processVoiceMessage(audioBlob);
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      setRecordingTime(0);
      
      // Start recording timer
      recordingTimerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 0.1);
      }, 100);

      updateAudioLevel();
      toast.success('Enregistrement démarré');

    } catch (error) {
      console.error('Error accessing microphone:', error);
      toast.error('Impossible d\'accéder au microphone');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setAudioLevel(0);
      
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
      }
      
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }

      toast.success('Enregistrement terminé');
    }
  };

  const processVoiceMessage = async (audioBlob: Blob) => {
    setIsProcessing(true);
    const startTime = Date.now();

    try {
      // Convert blob to file
      const audioFile = new File([audioBlob], 'recording.webm', { type: 'audio/webm' });
      
      // Simulate transcript (in real implementation, this would come from Deepgram STT)
      setTranscript("Traitement de l'audio en cours...");
      
      // Upload to backend
      const responseBlob = await apiClient.uploadVoiceMessage(audioFile);
      
      const endTime = Date.now();
      const responseTime = endTime - startTime;
      setLastResponseTime(responseTime);

      // Simulate transcript and response
      const mockTranscript = "Comment puis-je réinitialiser mon mot de passe ?";
      const mockResponse = "Pour réinitialiser votre mot de passe, cliquez sur 'Mot de passe oublié' sur la page de connexion, puis suivez les instructions envoyées par email.";
      
      setTranscript(mockTranscript);
      setResponse(mockResponse);

      // Play response audio
      await playAudioResponse(responseBlob);

    } catch (error) {
      console.error('Error processing voice message:', error);
      toast.error('Erreur lors du traitement vocal');
      
      // Fallback to text response
      setTranscript("Erreur de transcription");
      setResponse("Désolé, je n'ai pas pu traiter votre message vocal. Veuillez réessayer.");
    } finally {
      setIsProcessing(false);
    }
  };

  const playAudioResponse = async (audioBlob: Blob) => {
    try {
      setIsPlaying(true);
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      
      audio.onended = () => {
        setIsPlaying(false);
        URL.revokeObjectURL(audioUrl);
      };
      
      await audio.play();
    } catch (error) {
      console.error('Error playing audio:', error);
      setIsPlaying(false);
      toast.error('Erreur lors de la lecture audio');
    }
  };

  const simulateVoiceQuery = async (text: string) => {
    setTranscript(text);
    setIsProcessing(true);
    
    const startTime = Date.now();
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      const responses = {
        "Comment puis-je réinitialiser mon mot de passe ?": "Pour réinitialiser votre mot de passe, rendez-vous sur la page de connexion et cliquez sur 'Mot de passe oublié'. Vous recevrez un email avec les instructions.",
        "Quels sont vos horaires d'ouverture ?": "Notre support est disponible du lundi au vendredi de 9h à 18h, et le samedi de 10h à 16h. En dehors de ces horaires, vous pouvez nous contacter via le chat.",
        "Je souhaite connaître le statut de ma commande": "Pour vérifier le statut de votre commande, connectez-vous à votre compte et accédez à la section 'Mes commandes'. Vous y trouverez toutes les informations de suivi.",
        "Comment puis-je contacter le support ?": "Vous pouvez nous contacter via ce chat, par email à support@company.com, ou par téléphone au 01 23 45 67 89 pendant nos heures d'ouverture.",
        "Y a-t-il des frais de livraison ?": "La livraison est gratuite pour les commandes supérieures à 50€. En dessous, des frais de 4,90€ s'appliquent. La livraison express est disponible moyennant un supplément."
      };
      
      const responseText = responses[text as keyof typeof responses] || "Je n'ai pas compris votre question. Pourriez-vous la reformuler ?";
      setResponse(responseText);
      
      const endTime = Date.now();
      setLastResponseTime(endTime - startTime);
      
      // Simulate TTS playback
      setIsPlaying(true);
      setTimeout(() => setIsPlaying(false), 3000);
      
    } catch (error) {
      toast.error('Erreur lors de la simulation');
    } finally {
      setIsProcessing(false);
    }
  };

  const clearConversation = () => {
    setTranscript('');
    setResponse('');
    setLastResponseTime(null);
    toast.success('Conversation effacée');
  };

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="mb-8 flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Voice Demo</h1>
          <p className="text-gray-600">
            Interaction vocale avec IA - STT + TTS &lt; 1s latence
          </p>
        </div>
        
        <button
          onClick={clearConversation}
          className="btn btn-secondary btn-sm"
        >
          Effacer
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Recording Interface */}
        <div className="lg:col-span-2">
          <div className="card p-8 text-center">
            {/* Recording Button */}
            <div className="mb-8">
              <button
                onClick={isRecording ? stopRecording : startRecording}
                disabled={isProcessing}
                className={classNames(
                  'w-32 h-32 rounded-full flex items-center justify-center transition-all duration-300 transform',
                  isRecording
                    ? 'bg-danger-500 hover:bg-danger-600 text-white scale-110'
                    : 'bg-primary-500 hover:bg-primary-600 text-white hover:scale-105',
                  isProcessing && 'opacity-50 cursor-not-allowed'
                )}
              >
                {isRecording ? (
                  <StopIcon className="h-12 w-12" />
                ) : (
                  <MicrophoneIcon className="h-12 w-12" />
                )}
              </button>
            </div>

            {/* Audio Level Indicator */}
            {isRecording && (
              <div className="mb-6">
                <div className="flex justify-center items-center space-x-1 mb-2">
                  {[...Array(20)].map((_, i) => (
                    <div
                      key={i}
                      className={classNames(
                        'w-1 bg-primary-500 rounded-full transition-all duration-75',
                        i < audioLevel * 20 ? 'h-8' : 'h-2'
                      )}
                    />
                  ))}
                </div>
                <p className="text-sm text-gray-600">
                  Enregistrement: {recordingTime.toFixed(1)}s
                </p>
              </div>
            )}

            {/* Status */}
            <div className="mb-6">
              {isRecording && (
                <div className="flex items-center justify-center text-danger-600">
                  <SignalIcon className="h-5 w-5 mr-2 animate-pulse" />
                  <span className="font-medium">Enregistrement en cours...</span>
                </div>
              )}

              {isProcessing && (
                <div className="flex items-center justify-center text-warning-600">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-warning-600 mr-2"></div>
                  <span className="font-medium">Traitement vocal...</span>
                </div>
              )}

              {isPlaying && (
                <div className="flex items-center justify-center text-success-600">
                  <SpeakerWaveIcon className="h-5 w-5 mr-2 animate-pulse" />
                  <span className="font-medium">Lecture de la réponse...</span>
                </div>
              )}

              {!isRecording && !isProcessing && !isPlaying && (
                <p className="text-gray-600">
                  Cliquez sur le microphone pour commencer
                </p>
              )}
            </div>

            {/* Instructions */}
            <div className="text-sm text-gray-500">
              <p>• Maintenez le bouton pour enregistrer</p>
              <p>• Relâchez pour envoyer</p>
              <p>• La réponse sera automatiquement vocalisée</p>
            </div>
          </div>

          {/* Conversation */}
          {(transcript || response) && (
            <div className="mt-6 card p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Conversation</h3>
              
              {transcript && (
                <div className="mb-4 p-4 bg-primary-50 rounded-lg">
                  <div className="flex items-start">
                    <MicrophoneIcon className="h-5 w-5 text-primary-600 mt-0.5 mr-3" />
                    <div>
                      <p className="text-sm font-medium text-primary-900">Vous avez dit:</p>
                      <p className="text-primary-800">{transcript}</p>
                    </div>
                  </div>
                </div>
              )}

              {response && (
                <div className="p-4 bg-success-50 rounded-lg">
                  <div className="flex items-start">
                    <SpeakerWaveIcon className="h-5 w-5 text-success-600 mt-0.5 mr-3" />
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <p className="text-sm font-medium text-success-900">Réponse IA:</p>
                        {lastResponseTime && (
                          <div className="flex items-center text-xs text-success-700">
                            <ClockIcon className="h-3 w-3 mr-1" />
                            {lastResponseTime}ms
                          </div>
                        )}
                      </div>
                      <p className="text-success-800">{response}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Demo Prompts */}
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Questions Demo</h3>
          <p className="text-sm text-gray-600 mb-4">
            Cliquez pour simuler une question vocale:
          </p>
          
          <div className="space-y-3">
            {demoPrompts.map((prompt, index) => (
              <button
                key={index}
                onClick={() => simulateVoiceQuery(prompt)}
                disabled={isRecording || isProcessing}
                className="w-full text-left p-3 text-sm bg-gray-50 hover:bg-gray-100 rounded-lg border hover:border-primary-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {prompt}
              </button>
            ))}
          </div>

          {/* Technical Specs */}
          <div className="mt-8 pt-6 border-t border-gray-200">
            <h4 className="text-sm font-semibold text-gray-900 mb-3">Spécifications Techniques</h4>
            <div className="space-y-2 text-xs text-gray-600">
              <div className="flex justify-between">
                <span>STT:</span>
                <span>Deepgram Nova</span>
              </div>
              <div className="flex justify-between">
                <span>TTS:</span>
                <span>Deepgram Aura</span>
              </div>
              <div className="flex justify-between">
                <span>Latence cible:</span>
                <span>&lt; 1000ms</span>
              </div>
              <div className="flex justify-between">
                <span>Format:</span>
                <span>WebM Opus 16kHz</span>
              </div>
              <div className="flex justify-between">
                <span>WER cible:</span>
                <span>&lt; 15%</span>
              </div>
            </div>
          </div>

          {/* Performance Metrics */}
          {lastResponseTime && (
            <div className="mt-6 pt-4 border-t border-gray-200">
              <h4 className="text-sm font-semibold text-gray-900 mb-3">Performance</h4>
              <div className="space-y-2">
                <div className={classNames(
                  'p-2 rounded text-xs',
                  lastResponseTime < 1000 
                    ? 'bg-success-50 text-success-800'
                    : lastResponseTime < 2000
                    ? 'bg-warning-50 text-warning-800'
                    : 'bg-danger-50 text-danger-800'
                )}>
                  <div className="flex items-center justify-between">
                    <span>Temps de réponse:</span>
                    <span className="font-medium">{lastResponseTime}ms</span>
                  </div>
                  <div className="text-xs opacity-75 mt-1">
                    {lastResponseTime < 1000 ? '✅ Excellent' : 
                     lastResponseTime < 2000 ? '⚠️ Acceptable' : '❌ Trop lent'}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Browser Compatibility Warning */}
      {!navigator.mediaDevices && (
        <div className="mt-8">
          <div className="card p-4 border-l-4 border-warning-400 bg-warning-50">
            <div className="flex">
              <ExclamationTriangleIcon className="h-5 w-5 text-warning-400" />
              <div className="ml-3">
                <p className="text-sm text-warning-800">
                  Votre navigateur ne supporte pas l'enregistrement audio. 
                  Utilisez Chrome, Firefox ou Safari pour une expérience complète.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 