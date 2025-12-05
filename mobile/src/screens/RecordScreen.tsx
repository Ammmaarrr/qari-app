/**
 * Record Screen
 * Audio recording with visual feedback
 */
import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Animated,
  Alert,
  ActivityIndicator,
  SafeAreaView,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import AudioRecorderPlayer from 'react-native-audio-recorder-player';
import RNFS from 'react-native-fs';
import { uploadRecording } from '../services/api';

const audioRecorderPlayer = new AudioRecorderPlayer();

interface RecordScreenProps {
  navigation: any;
  route: any;
}

const RecordScreen: React.FC<RecordScreenProps> = ({ navigation, route }) => {
  const { surah, ayah } = route.params || {};
  
  const [isRecording, setIsRecording] = useState(false);
  const [recordTime, setRecordTime] = useState('00:00');
  const [recordPath, setRecordPath] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  
  // Animation for recording indicator
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    if (isRecording) {
      // Pulse animation while recording
      Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.2,
            duration: 500,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 500,
            useNativeDriver: true,
          }),
        ]),
      ).start();
    } else {
      pulseAnim.setValue(1);
    }
  }, [isRecording, pulseAnim]);

  const startRecording = async () => {
    try {
      const path = `${RNFS.CachesDirectoryPath}/recitation_${Date.now()}.wav`;
      
      const result = await audioRecorderPlayer.startRecorder(path, {
        SampleRate: 16000,
        Channels: 1,
        AudioEncoding: 'lpcm',
      });
      
      audioRecorderPlayer.addRecordBackListener((e) => {
        setRecordTime(audioRecorderPlayer.mmssss(Math.floor(e.currentPosition)));
      });
      
      setRecordPath(result);
      setIsRecording(true);
    } catch (error) {
      console.error('Recording error:', error);
      Alert.alert('Error', 'Failed to start recording. Please check microphone permissions.');
    }
  };

  const stopRecording = async () => {
    try {
      const result = await audioRecorderPlayer.stopRecorder();
      audioRecorderPlayer.removeRecordBackListener();
      setIsRecording(false);
      setRecordPath(result);
      
      // Ask user to analyze or re-record
      Alert.alert(
        'Recording Complete',
        'Would you like to analyze your recitation?',
        [
          { text: 'Re-record', onPress: () => setRecordPath(null) },
          { text: 'Analyze', onPress: () => analyzeRecording(result) },
        ],
      );
    } catch (error) {
      console.error('Stop recording error:', error);
    }
  };

  const analyzeRecording = async (audioPath: string) => {
    setIsAnalyzing(true);
    
    try {
      // Get user ID from storage (simplified - use actual auth in production)
      const userId = 'user-' + Date.now();
      
      const result = await uploadRecording(audioPath, userId, surah, ayah);
      
      setIsAnalyzing(false);
      
      // Navigate to results screen
      navigation.navigate('Results', {
        analysisResult: result,
        surah,
        ayah,
        audioPath,
      });
    } catch (error) {
      setIsAnalyzing(false);
      console.error('Analysis error:', error);
      Alert.alert(
        'Analysis Failed',
        'Could not analyze your recording. Please try again.',
        [{ text: 'OK' }],
      );
    }
  };

  const handleRecordPress = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  if (isAnalyzing) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.analyzingContainer}>
          <ActivityIndicator size="large" color="#2E7D32" />
          <Text style={styles.analyzingText}>Analyzing your recitation...</Text>
          <Text style={styles.analyzingSubtext}>This may take a few seconds</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {/* Header Info */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>
          {surah ? `Surah ${surah}` : 'Free Recording'}
        </Text>
        {ayah && <Text style={styles.headerSubtitle}>Ayah {ayah}</Text>}
      </View>

      {/* Recording Area */}
      <View style={styles.recordingArea}>
        {/* Timer */}
        <Text style={styles.timer}>{recordTime}</Text>
        
        {/* Recording Status */}
        <Text style={styles.status}>
          {isRecording ? 'Recording...' : 'Tap to start'}
        </Text>

        {/* Record Button */}
        <Animated.View style={{ transform: [{ scale: pulseAnim }] }}>
          <TouchableOpacity
            style={[
              styles.recordButton,
              isRecording && styles.recordButtonActive,
            ]}
            onPress={handleRecordPress}
          >
            <Icon
              name={isRecording ? 'stop' : 'microphone'}
              size={48}
              color="#fff"
            />
          </TouchableOpacity>
        </Animated.View>

        {/* Instructions */}
        <View style={styles.instructions}>
          <Text style={styles.instructionText}>
            {isRecording
              ? 'Recite clearly and tap to stop when done'
              : 'Tap the microphone to begin recording'}
          </Text>
        </View>
      </View>

      {/* Tips */}
      <View style={styles.tipsBox}>
        <Icon name="lightbulb-outline" size={20} color="#FFA000" />
        <Text style={styles.tipText}>
          Tip: Record in a quiet place for better accuracy
        </Text>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#2E7D32',
    padding: 20,
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#fff',
  },
  headerSubtitle: {
    fontSize: 16,
    color: '#C8E6C9',
    marginTop: 4,
  },
  recordingArea: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  timer: {
    fontSize: 48,
    fontWeight: '200',
    color: '#333',
    marginBottom: 8,
  },
  status: {
    fontSize: 16,
    color: '#666',
    marginBottom: 40,
  },
  recordButton: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: '#2E7D32',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  recordButtonActive: {
    backgroundColor: '#D32F2F',
  },
  instructions: {
    marginTop: 40,
    paddingHorizontal: 40,
  },
  instructionText: {
    textAlign: 'center',
    fontSize: 16,
    color: '#666',
    lineHeight: 24,
  },
  tipsBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFF8E1',
    padding: 16,
    margin: 16,
    borderRadius: 12,
  },
  tipText: {
    marginLeft: 12,
    fontSize: 14,
    color: '#5D4037',
    flex: 1,
  },
  analyzingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  analyzingText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginTop: 20,
  },
  analyzingSubtext: {
    fontSize: 14,
    color: '#666',
    marginTop: 8,
  },
});

export default RecordScreen;
