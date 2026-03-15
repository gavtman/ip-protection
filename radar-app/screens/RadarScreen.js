import React, { useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  Dimensions,
  ScrollView,
} from 'react-native';
import Svg, {
  Circle,
  Line,
  G,
  Path,
  Defs,
  RadialGradient,
  Stop,
  Polygon,
} from 'react-native-svg';

const { width } = Dimensions.get('window');
const RADAR_SIZE = Math.min(width - 32, 320);
const CENTER = RADAR_SIZE / 2;
const RADIUS = CENTER - 10;

const PHOSPHOR = '#00ff41';
const DIM_PHOSPHOR = '#004d14';
const BG = '#0a0e1a';
const CARD_BG = '#0d1224';

function toRad(deg) {
  return (deg * Math.PI) / 180;
}

function polarToXY(angleDeg, r) {
  const rad = toRad(angleDeg - 90);
  return {
    x: CENTER + r * Math.cos(rad),
    y: CENTER + r * Math.sin(rad),
  };
}

const BLIP_LIFETIME = 4000;

function useBlips() {
  const [blips, setBlips] = useState([]);
  const sweepAngle = useRef(0);

  useEffect(() => {
    const interval = setInterval(() => {
      const angle = sweepAngle.current;
      const r = RADIUS * (0.2 + Math.random() * 0.75);
      const blipAngle = angle + (Math.random() * 10 - 5);
      const pos = polarToXY(blipAngle, r);
      const id = Date.now() + Math.random();
      setBlips((prev) => [
        ...prev.filter((b) => Date.now() - b.born < BLIP_LIFETIME),
        { id, x: pos.x, y: pos.y, born: Date.now() },
      ]);
    }, 600);
    return () => clearInterval(interval);
  }, []);

  return { blips, sweepAngle };
}

function RadarBlip({ blip }) {
  const opacity = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    Animated.timing(opacity, {
      toValue: 0,
      duration: BLIP_LIFETIME,
      useNativeDriver: true,
    }).start();
  }, []);

  return (
    <Animated.View
      style={[
        styles.blip,
        { left: blip.x - 4, top: blip.y - 4, opacity },
      ]}
    />
  );
}

const AnimatedG = Animated.createAnimatedComponent(G);

export default function RadarScreen() {
  const sweepAnim = useRef(new Animated.Value(0)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const { blips, sweepAngle } = useBlips();
  const [stats] = useState({
    protectedRequests: 2847,
    maskedIPs: 14,
    activeConnections: 3,
    threatLevel: 'LOW',
  });

  useEffect(() => {
    Animated.loop(
      Animated.timing(sweepAnim, {
        toValue: 360,
        duration: 3000,
        useNativeDriver: true,
      })
    ).start();

    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.08,
          duration: 1200,
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 1200,
          useNativeDriver: true,
        }),
      ])
    ).start();

    const listenerId = sweepAnim.addListener(({ value }) => {
      sweepAngle.current = value;
    });
    return () => sweepAnim.removeListener(listenerId);
  }, []);

  const sweepRotation = sweepAnim.interpolate({
    inputRange: [0, 360],
    outputRange: ['0deg', '360deg'],
  });

  const rings = [0.25, 0.5, 0.75, 1.0];
  const ringCount = rings.length;

  const sweepPath = (() => {
    const fanAngle = 30;
    const p1 = polarToXY(0, RADIUS);
    const p2 = polarToXY(-fanAngle, RADIUS);
    const largeArc = fanAngle > 180 ? 1 : 0;
    return `M ${CENTER} ${CENTER} L ${p1.x} ${p1.y} A ${RADIUS} ${RADIUS} 0 ${largeArc} 0 ${p2.x} ${p2.y} Z`;
  })();

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
    >
      <View style={styles.statusRow}>
        <View style={styles.statusBadge}>
          <View style={styles.statusDot} />
          <Text style={styles.statusText}>PROTECTED</Text>
        </View>
        <Text style={styles.threatText}>
          THREAT: <Text style={styles.threatLevel}>{stats.threatLevel}</Text>
        </Text>
      </View>

      <Animated.View style={[styles.radarWrapper, { transform: [{ scale: pulseAnim }] }]}>
        <View style={[styles.radarContainer, { width: RADAR_SIZE, height: RADAR_SIZE }]}>
          <Svg width={RADAR_SIZE} height={RADAR_SIZE}>
            <Defs>
              <RadialGradient id="radarGrad" cx="50%" cy="50%" r="50%">
                <Stop offset="0%" stopColor="#001a08" stopOpacity="1" />
                <Stop offset="100%" stopColor="#000d04" stopOpacity="1" />
              </RadialGradient>
            </Defs>

            <Circle cx={CENTER} cy={CENTER} r={RADIUS + 8} fill="#060e08" />
            <Circle cx={CENTER} cy={CENTER} r={RADIUS} fill="url(#radarGrad)" />

            {rings.map((ratio, i) => (
              <Circle
                key={i}
                cx={CENTER}
                cy={CENTER}
                r={RADIUS * ratio}
                stroke={PHOSPHOR}
                strokeWidth={i === ringCount - 1 ? 1.5 : 0.5}
                strokeOpacity={i === ringCount - 1 ? 0.8 : 0.25}
                fill="none"
              />
            ))}

            <Line x1={CENTER} y1={CENTER - RADIUS} x2={CENTER} y2={CENTER + RADIUS}
              stroke={PHOSPHOR} strokeWidth={0.5} strokeOpacity={0.25} />
            <Line x1={CENTER - RADIUS} y1={CENTER} x2={CENTER + RADIUS} y2={CENTER}
              stroke={PHOSPHOR} strokeWidth={0.5} strokeOpacity={0.25} />
            <Line
              x1={CENTER - RADIUS * Math.cos(toRad(45))}
              y1={CENTER - RADIUS * Math.sin(toRad(45))}
              x2={CENTER + RADIUS * Math.cos(toRad(45))}
              y2={CENTER + RADIUS * Math.sin(toRad(45))}
              stroke={PHOSPHOR} strokeWidth={0.5} strokeOpacity={0.15} />
            <Line
              x1={CENTER + RADIUS * Math.cos(toRad(45))}
              y1={CENTER - RADIUS * Math.sin(toRad(45))}
              x2={CENTER - RADIUS * Math.cos(toRad(45))}
              y2={CENTER + RADIUS * Math.sin(toRad(45))}
              stroke={PHOSPHOR} strokeWidth={0.5} strokeOpacity={0.15} />

            {[0, 45, 90, 135, 180, 225, 270, 315].map((deg) => {
              const inner = polarToXY(deg, RADIUS - 6);
              const outer = polarToXY(deg, RADIUS + 2);
              return (
                <Line key={deg}
                  x1={inner.x} y1={inner.y}
                  x2={outer.x} y2={outer.y}
                  stroke={PHOSPHOR} strokeWidth={1} strokeOpacity={0.6} />
              );
            })}
          </Svg>

          <Animated.View
            style={[
              styles.sweepContainer,
              { width: RADAR_SIZE, height: RADAR_SIZE },
              { transform: [{ rotate: sweepRotation }] },
            ]}
          >
            <Svg width={RADAR_SIZE} height={RADAR_SIZE}>
              <Defs>
                <RadialGradient id="sweepGrad" cx="50%" cy="50%" r="50%">
                  <Stop offset="0%" stopColor={PHOSPHOR} stopOpacity="0.5" />
                  <Stop offset="100%" stopColor={PHOSPHOR} stopOpacity="0" />
                </RadialGradient>
              </Defs>
              <Path d={sweepPath} fill={PHOSPHOR} opacity={0.15} />
              <Line
                x1={CENTER}
                y1={CENTER}
                x2={CENTER}
                y2={CENTER - RADIUS}
                stroke={PHOSPHOR}
                strokeWidth={2}
                strokeOpacity={0.9}
              />
            </Svg>
          </Animated.View>

          <View style={[styles.blipsLayer, { width: RADAR_SIZE, height: RADAR_SIZE }]}>
            {blips.map((blip) => (
              <RadarBlip key={blip.id} blip={blip} />
            ))}
          </View>

          <View style={styles.centerDot} />
        </View>
      </Animated.View>

      <View style={styles.statsGrid}>
        <StatCard label="Protected Requests" value={stats.protectedRequests.toLocaleString()} icon="🛡️" />
        <StatCard label="Masked IPs" value={stats.maskedIPs} icon="🎭" />
        <StatCard label="Active Connections" value={stats.activeConnections} icon="📡" />
        <StatCard label="Threat Level" value={stats.threatLevel} icon="⚠️" accent />
      </View>

      <View style={styles.infoCard}>
        <Text style={styles.infoTitle}>HOW IP PROTECTION WORKS</Text>
        <Text style={styles.infoText}>
          Chrome's IP Protection feature routes third-party traffic through privacy
          proxies in Incognito mode, masking your real IP address from trackers.
          The radar shows simulated network scanning activity.
        </Text>
      </View>
    </ScrollView>
  );
}

function StatCard({ label, value, icon, accent }) {
  return (
    <View style={[styles.statCard, accent && styles.statCardAccent]}>
      <Text style={styles.statIcon}>{icon}</Text>
      <Text style={[styles.statValue, accent && styles.statValueAccent]}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: BG,
  },
  content: {
    alignItems: 'center',
    paddingVertical: 16,
    paddingHorizontal: 16,
  },
  statusRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    width: '100%',
    marginBottom: 16,
    paddingHorizontal: 4,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#001a08',
    borderWidth: 1,
    borderColor: PHOSPHOR,
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 6,
    gap: 6,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: PHOSPHOR,
    shadowColor: PHOSPHOR,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 1,
    shadowRadius: 4,
  },
  statusText: {
    color: PHOSPHOR,
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 1.5,
  },
  threatText: {
    color: '#4a6a4a',
    fontSize: 12,
    fontWeight: '600',
    letterSpacing: 1,
  },
  threatLevel: {
    color: '#7fff7f',
    fontWeight: '700',
  },
  radarWrapper: {
    marginBottom: 24,
    shadowColor: PHOSPHOR,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.3,
    shadowRadius: 20,
    elevation: 10,
  },
  radarContainer: {
    position: 'relative',
    borderRadius: RADAR_SIZE / 2,
    overflow: 'hidden',
    borderWidth: 2,
    borderColor: '#1a3a1a',
  },
  sweepContainer: {
    position: 'absolute',
    top: 0,
    left: 0,
  },
  blipsLayer: {
    position: 'absolute',
    top: 0,
    left: 0,
  },
  centerDot: {
    position: 'absolute',
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: PHOSPHOR,
    top: CENTER - 4,
    left: CENTER - 4,
    shadowColor: PHOSPHOR,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 1,
    shadowRadius: 6,
  },
  blip: {
    position: 'absolute',
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: PHOSPHOR,
    shadowColor: PHOSPHOR,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 1,
    shadowRadius: 6,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
    width: '100%',
    marginBottom: 16,
  },
  statCard: {
    flex: 1,
    minWidth: '45%',
    backgroundColor: CARD_BG,
    borderRadius: 12,
    padding: 14,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#1a2340',
  },
  statCardAccent: {
    borderColor: DIM_PHOSPHOR,
    backgroundColor: '#0a1a0a',
  },
  statIcon: {
    fontSize: 22,
    marginBottom: 6,
  },
  statValue: {
    fontSize: 22,
    fontWeight: '800',
    color: PHOSPHOR,
    letterSpacing: 0.5,
  },
  statValueAccent: {
    color: '#7fff7f',
  },
  statLabel: {
    fontSize: 10,
    color: '#4a6a5a',
    marginTop: 4,
    textAlign: 'center',
    fontWeight: '600',
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },
  infoCard: {
    width: '100%',
    backgroundColor: CARD_BG,
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#1a2340',
    borderLeftWidth: 3,
    borderLeftColor: PHOSPHOR,
  },
  infoTitle: {
    color: PHOSPHOR,
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1.5,
    marginBottom: 8,
  },
  infoText: {
    color: '#6a8a7a',
    fontSize: 13,
    lineHeight: 20,
  },
});
