/**
 * Progress Screen
 * Track user's learning progress over time
 */
import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  SafeAreaView,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

interface ProgressScreenProps {
  navigation: any;
}

// Mock progress data
const MOCK_STATS = {
  totalSessions: 45,
  totalMinutes: 180,
  averageScore: 0.78,
  streak: 7,
  improvement: 0.12,
};

const MOCK_RECENT_SESSIONS = [
  { date: '2024-01-15', surah: 1, score: 0.85, duration: 5 },
  { date: '2024-01-14', surah: 112, score: 0.72, duration: 3 },
  { date: '2024-01-13', surah: 1, score: 0.78, duration: 4 },
  { date: '2024-01-12', surah: 114, score: 0.90, duration: 4 },
];

const MOCK_ERROR_BREAKDOWN = [
  { type: 'Madd', count: 12, color: '#7B1FA2' },
  { type: 'Letter Substitution', count: 8, color: '#D32F2F' },
  { type: 'Ghunnah', count: 5, color: '#0288D1' },
  { type: 'Qalqalah', count: 3, color: '#388E3C' },
];

const ProgressScreen: React.FC<ProgressScreenProps> = () => {
  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Your Progress</Text>
      </View>

      <ScrollView style={styles.content}>
        {/* Stats Grid */}
        <View style={styles.statsGrid}>
          <View style={styles.statCard}>
            <Icon name="fire" size={32} color="#FF5722" />
            <Text style={styles.statValue}>{MOCK_STATS.streak}</Text>
            <Text style={styles.statLabel}>Day Streak</Text>
          </View>
          
          <View style={styles.statCard}>
            <Icon name="microphone" size={32} color="#2E7D32" />
            <Text style={styles.statValue}>{MOCK_STATS.totalSessions}</Text>
            <Text style={styles.statLabel}>Sessions</Text>
          </View>
          
          <View style={styles.statCard}>
            <Icon name="clock-outline" size={32} color="#1976D2" />
            <Text style={styles.statValue}>{MOCK_STATS.totalMinutes}</Text>
            <Text style={styles.statLabel}>Minutes</Text>
          </View>
          
          <View style={styles.statCard}>
            <Icon name="trending-up" size={32} color="#4CAF50" />
            <Text style={styles.statValue}>+{Math.round(MOCK_STATS.improvement * 100)}%</Text>
            <Text style={styles.statLabel}>Improved</Text>
          </View>
        </View>

        {/* Average Score */}
        <View style={styles.scoreSection}>
          <Text style={styles.sectionTitle}>Average Score</Text>
          <View style={styles.scoreBar}>
            <View 
              style={[
                styles.scoreBarFill, 
                { width: `${MOCK_STATS.averageScore * 100}%` }
              ]} 
            />
          </View>
          <Text style={styles.scorePercentage}>
            {Math.round(MOCK_STATS.averageScore * 100)}%
          </Text>
        </View>

        {/* Error Breakdown */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Common Areas to Improve</Text>
          {MOCK_ERROR_BREAKDOWN.map((error, index) => (
            <View key={index} style={styles.errorRow}>
              <View style={styles.errorInfo}>
                <View style={[styles.errorDot, { backgroundColor: error.color }]} />
                <Text style={styles.errorType}>{error.type}</Text>
              </View>
              <Text style={styles.errorCount}>{error.count} times</Text>
            </View>
          ))}
        </View>

        {/* Recent Sessions */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Recent Sessions</Text>
          {MOCK_RECENT_SESSIONS.map((session, index) => (
            <View key={index} style={styles.sessionCard}>
              <View style={styles.sessionInfo}>
                <Text style={styles.sessionDate}>{session.date}</Text>
                <Text style={styles.sessionSurah}>Surah {session.surah}</Text>
              </View>
              <View style={styles.sessionStats}>
                <Text style={styles.sessionScore}>
                  {Math.round(session.score * 100)}%
                </Text>
                <Text style={styles.sessionDuration}>{session.duration} min</Text>
              </View>
            </View>
          ))}
        </View>

        {/* Motivational Message */}
        <View style={styles.motivationCard}>
          <Icon name="star" size={24} color="#FFC107" />
          <Text style={styles.motivationText}>
            Keep up the great work! You're making excellent progress in your tajweed journey.
          </Text>
        </View>
      </ScrollView>
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
  content: {
    flex: 1,
    padding: 16,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  statCard: {
    width: '48%',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  statValue: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 8,
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  scoreSection: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
  },
  scoreBar: {
    height: 12,
    backgroundColor: '#E0E0E0',
    borderRadius: 6,
    overflow: 'hidden',
  },
  scoreBarFill: {
    height: '100%',
    backgroundColor: '#4CAF50',
    borderRadius: 6,
  },
  scorePercentage: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#4CAF50',
    textAlign: 'center',
    marginTop: 8,
  },
  section: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  errorRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  errorInfo: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  errorDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 12,
  },
  errorType: {
    fontSize: 14,
    color: '#333',
  },
  errorCount: {
    fontSize: 14,
    color: '#666',
  },
  sessionCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  sessionInfo: {},
  sessionDate: {
    fontSize: 14,
    fontWeight: '500',
    color: '#333',
  },
  sessionSurah: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  sessionStats: {
    alignItems: 'flex-end',
  },
  sessionScore: {
    fontSize: 16,
    fontWeight: '600',
    color: '#4CAF50',
  },
  sessionDuration: {
    fontSize: 12,
    color: '#999',
    marginTop: 2,
  },
  motivationCard: {
    backgroundColor: '#FFF8E1',
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 32,
  },
  motivationText: {
    flex: 1,
    marginLeft: 12,
    fontSize: 14,
    color: '#5D4037',
    lineHeight: 20,
  },
});

export default ProgressScreen;
