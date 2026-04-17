import { useState, useRef, useCallback } from 'react';
import { useStore } from '../store/useStore';

export const useVideoRecorder = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const startRecording = useCallback((videoBitsPerSecond: number = 8_000_000) => {
    const { mapRef } = useStore.getState();
    if (!mapRef) return;

    const mapCanvas = mapRef.getCanvas();
    if (!mapCanvas) return;

    const stream = (mapCanvas as any).captureStream(60);

    let recorder: MediaRecorder;
    try {
      recorder = new MediaRecorder(stream, { mimeType: 'video/webm; codecs=vp9', videoBitsPerSecond });
    } catch (e) {
      console.warn('VP9 not supported, falling back.');
      recorder = new MediaRecorder(stream, { mimeType: 'video/webm', videoBitsPerSecond });
    }

    chunksRef.current = [];

    recorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) chunksRef.current.push(e.data);
    };

    recorder.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: 'video/webm' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `SiteANA_Animation_${new Date().getTime()}.webm`;
      a.click();
      URL.revokeObjectURL(url);
    };

    recorder.start(100);
    mediaRecorderRef.current = recorder;
    setIsRecording(true);
    setRecordingSeconds(0);
    timerRef.current = setInterval(() => setRecordingSeconds(prev => prev + 1), 1000);


  }, []);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      if (timerRef.current) clearInterval(timerRef.current);
    }
  }, []);

  return {
    isRecording,
    recordingSeconds,
    startRecording,
    stopRecording
  };
};
