// VoiceRecorder.tsx - Voice recording component with microphone button

import React, { useState, useRef, useEffect } from 'react';
import { MicrophoneIcon } from './Icons';

interface VoiceRecorderProps {
  onTranscriptionComplete: (text: string) => void;
  isDisabled?: boolean;
}

type RecordingState = 'idle' | 'recording' | 'processing';

const VoiceRecorder: React.FC<VoiceRecorderProps> = ({ onTranscriptionComplete, isDisabled = false }) => {
  const [recordingState, setRecordingState] = useState<RecordingState>('idle');
  const [recordingTime, setRecordingTime] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const MAX_RECORDING_TIME = 600; // 10 minutes in seconds

  useEffect(() => {
    // Cleanup on unmount
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.stop();
      }
    };
  }, []);

  const startRecording = async () => {
    try {
      setError(null);

      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      // Create MediaRecorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/ogg',
      });

      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      // Handle data available
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      // Handle recording stop
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });

        // Stop all tracks to release microphone
        stream.getTracks().forEach(track => track.stop());

        // Send for transcription
        await transcribeAudio(audioBlob);
      };

      // Start recording
      mediaRecorder.start();
      setRecordingState('recording');
      setRecordingTime(0);

      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => {
          const newTime = prev + 1;

          // Auto-stop at max time
          if (newTime >= MAX_RECORDING_TIME) {
            stopRecording();
          }

          return newTime;
        });
      }, 1000);

    } catch (err) {
      console.error('Error starting recording:', err);

      if (err instanceof DOMException && err.name === 'NotAllowedError') {
        setError('Microphone access denied. Please enable microphone permissions.');
      } else if (err instanceof DOMException && err.name === 'NotFoundError') {
        setError('No microphone found. Please connect a microphone.');
      } else {
        setError('Failed to start recording. Please try again.');
      }
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();

      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  };

  const cancelRecording = () => {
    if (mediaRecorderRef.current) {
      // Stop recording without processing
      const mediaRecorder = mediaRecorderRef.current;

      mediaRecorder.onstop = () => {
        // Clear the stream
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
      };

      if (mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
      }
    }

    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }

    audioChunksRef.current = [];
    setRecordingState('idle');
    setRecordingTime(0);
    setError(null);
  };

  const transcribeAudio = async (audioBlob: Blob) => {
    setRecordingState('processing');

    try {
      // Create FormData
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.webm');

      // Send to backend
      const response = await fetch('http://localhost:5000/api/transcribe-audio', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Transcription failed: ${response.statusText}`);
      }

      const data = await response.json();

      if (data.success && data.transcription) {
        // Pass transcription to parent
        onTranscriptionComplete(data.transcription);
        setRecordingState('idle');
        setRecordingTime(0);
      } else {
        throw new Error(data.message || 'Transcription failed');
      }
    } catch (err) {
      console.error('Transcription error:', err);
      setError(err instanceof Error ? err.message : 'Failed to transcribe audio');
      setRecordingState('idle');
      setRecordingTime(0);
    }
  };

  const handleClick = () => {
    if (recordingState === 'idle') {
      startRecording();
    } else if (recordingState === 'recording') {
      stopRecording();
    }
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Check if browser supports MediaRecorder
  const isSupported = typeof navigator !== 'undefined' &&
                      navigator.mediaDevices &&
                      navigator.mediaDevices.getUserMedia;

  if (!isSupported) {
    return null; // Don't show button if not supported
  }

  return (
    <div className="flex items-center gap-2">
      {recordingState === 'recording' && (
        <>
          <button
            type="button"
            onClick={cancelRecording}
            className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800 border border-gray-300 rounded-md"
          >
            Cancel
          </button>
          <span className="text-sm text-gray-600 font-mono">
            {formatTime(recordingTime)}
          </span>
        </>
      )}

      {recordingState === 'processing' && (
        <span className="text-sm text-gray-600">Transcribing...</span>
      )}

      <button
        type="button"
        onClick={handleClick}
        disabled={isDisabled || recordingState === 'processing'}
        className={`p-2 rounded-full transition-colors ${
          recordingState === 'idle'
            ? 'text-gray-600 hover:text-gray-800 hover:bg-gray-100'
            : recordingState === 'recording'
            ? 'text-red-600 bg-red-50 animate-pulse'
            : 'text-gray-400 cursor-not-allowed'
        }`}
        title={
          recordingState === 'idle'
            ? 'Start voice recording'
            : recordingState === 'recording'
            ? 'Stop recording'
            : 'Processing...'
        }
      >
        <MicrophoneIcon
          className={`h-5 w-5 ${
            recordingState === 'recording' ? 'fill-red-600' : ''
          }`}
        />
      </button>

      {error && (
        <div className="absolute bottom-full mb-2 right-0 bg-red-50 border border-red-200 text-red-700 px-4 py-2 rounded-lg text-sm max-w-xs">
          {error}
        </div>
      )}
    </div>
  );
};

export default VoiceRecorder;
