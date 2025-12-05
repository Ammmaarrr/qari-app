/**
 * Results Screen
 * Display analysis results with error details
 */
import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import Sound from 'react-native-sound';

// Configure Sound
Sound.setCategory('Playback');

interface TajweedError {
  type: string;
  letter: string | null;
  expected: string | null;
  detected: string | null;
  start_time: number;
  end_time: number;
  confidence: number;
  suggestion: string;
  correction_audio_url: string;
  severity: string;
}

interface AnalysisResult {
  matched_ayah: {
    surah: number;
    ayah: number;
    confidence: number;
    text: string;
  };
  errors: TajweedError[];
  overall_score: number;
  recommendation: string;
}

interface ResultsScreenProps {
  navigation: any;
  route: any;
}

// Error type display info
const ERROR_TYPE_INFO: Record<string, { icon: string; color: string; label: string }> = {
  substituted_letter: { icon: 'alphabetical', color: '#D32F2F', label: 'Letter Substitution' },
  missing_word: { icon: 'text-box-remove', color: '#F57C00', label: 'Missing Word' },
  madd_short: { icon: 'timer-sand', color: '#7B1FA2', label: 'Madd Too Short' },
  madd_long: { icon: 'timer-sand-full', color: '#7B1FA2', label: 'Madd Too Long' },
  ghunnah_missing: { icon: 'music-note', color: '#0288D1', label: 'Missing Ghunnah' },
  qalqalah_missing: { icon: 'waveform', color: '#388E3C', label: 'Missing Qalqalah' },
};

const ResultsScreen: React.FC<ResultsScreenProps> = ({ navigation, route }) => {
  const { analysisResult, surah, ayah, audioPath } = route.params || {};
  const result: AnalysisResult = analysisResult;
  
  const [playingAudio, setPlayingAudio] = useState<string | null>(null);

  const getScoreColor = (score: number): string => {
    if (score >= 0.85) return '#4CAF50';
    if (score >= 0.7) return '#FFC107';
    if (score >= 0.5) return '#FF9800';
    return '#F44336';
  };

  const playCorrection = (audioUrl: string) => {
    // In production, use actual audio URL
    // For now, show feedback
    setPlayingAudio(audioUrl);
    
    // Simulate audio playback
    setTimeout(() => {
      setPlayingAudio(null);
    }, 2000);
  };

  const handleTryAgain = (error: TajweedError) => {
    // Navigate to focused practice for this specific error
    navigation.navigate('Record', {
      surah: result.matched_ayah.surah,
      ayah: result.matched_ayah.ayah,
      focusWord: error.letter,
      startTime: error.start_time,
      endTime: error.end_time,
    });
  };

  const handleRecordAgain = () => {
    navigation.navigate('Record', { surah, ayah });
  };

  const getErrorInfo = (type: string) => {
    return ERROR_TYPE_INFO[type] || { 
      icon: 'alert-circle', 
      color: '#9E9E9E', 
      label: type 
    };
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView>
        {/* Score Card */}
        <View style={styles.scoreCard}>
          <View style={styles.scoreCircle}>
            <Text style={[styles.scoreText, { color: getScoreColor(result.overall_score) }]}>
              {Math.round(result.overall_score * 100)}%
            </Text>
          </View>
          <Text style={styles.scoreLabel}>Overall Score</Text>
          <Text style={styles.matchedAyah}>
            Surah {result.matched_ayah.surah}, Ayah {result.matched_ayah.ayah}
          </Text>
          <Text style={styles.arabicText}>{result.matched_ayah.text}</Text>
        </View>

        {/* Recommendation */}
        <View style={styles.recommendationCard}>
          <Icon name="lightbulb-outline" size={24} color="#FFA000" />
          <Text style={styles.recommendationText}>{result.recommendation}</Text>
        </View>

        {/* Errors List */}
        <View style={styles.errorsSection}>
          <Text style={styles.sectionTitle}>
            {result.errors.length > 0 ? 'Areas to Improve' : 'Great Job!'}
          </Text>
          
          {result.errors.length === 0 ? (
            <View style={styles.noErrorsCard}>
              <Icon name="check-circle" size={48} color="#4CAF50" />
              <Text style={styles.noErrorsText}>
                No errors detected! Excellent recitation.
              </Text>
            </View>
          ) : (
            result.errors.map((error, index) => {
              const errorInfo = getErrorInfo(error.type);
              
              return (
                <View key={index} style={styles.errorCard}>
                  {/* Error Header */}
                  <View style={styles.errorHeader}>
                    <View style={[styles.errorIcon, { backgroundColor: errorInfo.color + '20' }]}>
                      <Icon name={errorInfo.icon} size={24} color={errorInfo.color} />
                    </View>
                    <View style={styles.errorHeaderText}>
                      <Text style={styles.errorType}>{errorInfo.label}</Text>
                      <Text style={styles.errorConfidence}>
                        Confidence: {Math.round(error.confidence * 100)}%
                      </Text>
                    </View>
                    <View style={[styles.severityBadge, { 
                      backgroundColor: error.severity === 'high' ? '#FFEBEE' : '#FFF8E1' 
                    }]}>
                      <Text style={[styles.severityText, {
                        color: error.severity === 'high' ? '#D32F2F' : '#F57C00'
                      }]}>
                        {error.severity}
                      </Text>
                    </View>
                  </View>

                  {/* Letter Info */}
                  {error.letter && (
                    <View style={styles.letterInfo}>
                      <Text style={styles.letterLabel}>Letter:</Text>
                      <Text style={styles.letterArabic}>{error.expected}</Text>
                      {error.detected && (
                        <>
                          <Icon name="arrow-right" size={16} color="#999" />
                          <Text style={styles.letterArabic}>{error.detected}</Text>
                        </>
                      )}
                    </View>
                  )}

                  {/* Suggestion */}
                  <Text style={styles.suggestion}>{error.suggestion}</Text>

                  {/* Action Buttons */}
                  <View style={styles.errorActions}>
                    <TouchableOpacity
                      style={styles.actionButton}
                      onPress={() => playCorrection(error.correction_audio_url)}
                    >
                      <Icon 
                        name={playingAudio === error.correction_audio_url ? 'volume-high' : 'play-circle'} 
                        size={20} 
                        color="#2E7D32" 
                      />
                      <Text style={styles.actionButtonText}>
                        {playingAudio === error.correction_audio_url ? 'Playing...' : 'Play Correct'}
                      </Text>
                    </TouchableOpacity>
                    
                    <TouchableOpacity
                      style={[styles.actionButton, styles.tryAgainButton]}
                      onPress={() => handleTryAgain(error)}
                    >
                      <Icon name="refresh" size={20} color="#fff" />
                      <Text style={[styles.actionButtonText, { color: '#fff' }]}>
                        Try Again
                      </Text>
                    </TouchableOpacity>
                  </View>
                </View>
              );
            })
          )}
        </View>
      </ScrollView>

      {/* Bottom Actions */}
      <View style={styles.bottomActions}>
        <TouchableOpacity style={styles.recordAgainButton} onPress={handleRecordAgain}>
          <Icon name="microphone" size={20} color="#2E7D32" />
          <Text style={styles.recordAgainText}>Record Again</Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={styles.homeButton}
          onPress={() => navigation.navigate('Home')}
        >
          <Icon name="home" size={20} color="#fff" />
          <Text style={styles.homeButtonText}>Home</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  scoreCard: {
    backgroundColor: '#fff',
    margin: 16,
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  scoreCircle: {
    width: 100,
    height: 100,
    borderRadius: 50,
    borderWidth: 6,
    borderColor: '#E0E0E0',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  scoreText: {
    fontSize: 32,
    fontWeight: 'bold',
  },
  scoreLabel: {
    fontSize: 16,
    color: '#666',
    marginBottom: 8,
  },
  matchedAyah: {
    fontSize: 14,
    color: '#999',
    marginBottom: 8,
  },
  arabicText: {
    fontSize: 20,
    color: '#333',
    textAlign: 'center',
    lineHeight: 32,
  },
  recommendationCard: {
    backgroundColor: '#FFF8E1',
    marginHorizontal: 16,
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
  },
  recommendationText: {
    flex: 1,
    marginLeft: 12,
    fontSize: 14,
    color: '#5D4037',
    lineHeight: 20,
  },
  errorsSection: {
    padding: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
  },
  noErrorsCard: {
    backgroundColor: '#E8F5E9',
    borderRadius: 12,
    padding: 32,
    alignItems: 'center',
  },
  noErrorsText: {
    fontSize: 16,
    color: '#2E7D32',
    marginTop: 12,
    textAlign: 'center',
  },
  errorCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  errorHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  errorIcon: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorHeaderText: {
    flex: 1,
    marginLeft: 12,
  },
  errorType: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  errorConfidence: {
    fontSize: 12,
    color: '#999',
    marginTop: 2,
  },
  severityBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  severityText: {
    fontSize: 10,
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  letterInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F5F5F5',
    padding: 12,
    borderRadius: 8,
    marginBottom: 12,
  },
  letterLabel: {
    fontSize: 14,
    color: '#666',
    marginRight: 8,
  },
  letterArabic: {
    fontSize: 24,
    color: '#333',
    marginHorizontal: 8,
  },
  suggestion: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
    marginBottom: 12,
  },
  errorActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#E8F5E9',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    flex: 0.48,
    justifyContent: 'center',
  },
  tryAgainButton: {
    backgroundColor: '#2E7D32',
  },
  actionButtonText: {
    fontSize: 14,
    color: '#2E7D32',
    marginLeft: 6,
    fontWeight: '500',
  },
  bottomActions: {
    flexDirection: 'row',
    padding: 16,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#eee',
  },
  recordAgainButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#E8F5E9',
    paddingVertical: 14,
    borderRadius: 12,
    marginRight: 8,
  },
  recordAgainText: {
    fontSize: 16,
    color: '#2E7D32',
    fontWeight: '600',
    marginLeft: 8,
  },
  homeButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#2E7D32',
    paddingVertical: 14,
    borderRadius: 12,
    marginLeft: 8,
  },
  homeButtonText: {
    fontSize: 16,
    color: '#fff',
    fontWeight: '600',
    marginLeft: 8,
  },
});

export default ResultsScreen;
