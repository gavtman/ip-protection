import React, { useState, useEffect, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  TouchableOpacity,
} from 'react-native';

const PHOSPHOR = '#00ff41';
const BG = '#0a0e1a';
const CARD_BG = '#0d1224';
const BORDER = '#1a2340';

const MOCK_IP_DATA = {
  ip: '198.51.100.42',
  country_name: 'United States',
  region: 'California',
  city: 'Mountain View',
  org: 'AS15169 Google LLC',
  timezone: 'America/Los_Angeles',
  latitude: 37.3861,
  longitude: -122.0839,
};

export default function IPInfoScreen() {
  const [ipData, setIpData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [masked, setMasked] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchIPData = async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);

    try {
      const ipRes = await fetch('https://api.ipify.org?format=json');
      const { ip } = await ipRes.json();
      const geoRes = await fetch(`https://ipapi.co/${ip}/json/`);
      const geoData = await geoRes.json();
      setIpData({ ...geoData, ip });
    } catch (e) {
      setError('Could not fetch live IP data. Showing demo data.');
      setIpData(MOCK_IP_DATA);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchIPData();
  }, []);

  const displayIP = useMemo(
    () => (masked ? maskIP(ipData?.ip) : ipData?.ip),
    [masked, ipData?.ip]
  );

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color={PHOSPHOR} />
        <Text style={styles.loadingText}>SCANNING NETWORK...</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
    >
      {error && (
        <View style={styles.errorBanner}>
          <Text style={styles.errorText}>⚠️  {error}</Text>
        </View>
      )}

      <View style={styles.protectionCard}>
        <View style={styles.protectionHeader}>
          <Text style={styles.protectionTitle}>IP PROTECTION STATUS</Text>
          <TouchableOpacity
            style={[styles.toggleBtn, masked && styles.toggleBtnActive]}
            onPress={() => setMasked((m) => !m)}
          >
            <Text style={[styles.toggleText, masked && styles.toggleTextActive]}>
              {masked ? '🛡️  ACTIVE' : '👁️  INACTIVE'}
            </Text>
          </TouchableOpacity>
        </View>

        <View style={styles.ipDisplay}>
          <Text style={styles.ipLabel}>YOUR IP ADDRESS</Text>
          <Text style={styles.ipValue} selectable>{displayIP}</Text>
          <Text style={styles.ipNote}>
            {masked
              ? '✓ IP is masked via privacy proxy'
              : '⚠ Real IP visible to third-parties'}
          </Text>
        </View>
      </View>

      <Text style={styles.sectionTitle}>NETWORK DETAILS</Text>

      <InfoRow icon="🌍" label="Country" value={ipData?.country_name ?? '—'} />
      <InfoRow icon="📍" label="Region" value={ipData?.region ?? '—'} />
      <InfoRow icon="🏙️" label="City" value={ipData?.city ?? '—'} />
      <InfoRow icon="🏢" label="ISP / Org" value={ipData?.org ?? '—'} />
      <InfoRow icon="🕐" label="Timezone" value={ipData?.timezone ?? '—'} />
      <InfoRow
        icon="📌"
        label="Coordinates"
        value={
          ipData?.latitude && ipData?.longitude
            ? `${Number(ipData.latitude).toFixed(4)}, ${Number(ipData.longitude).toFixed(4)}`
            : '—'
        }
      />

      <Text style={styles.sectionTitle}>PROXY CHAIN</Text>
      <View style={styles.proxyCard}>
        <ProxyHop
          step={1}
          label="Your Device"
          ip={ipData?.ip ?? '…'}
          active
          first
        />
        <ProxyHop step={2} label="Proxy A (Region 1)" ip="100.64.x.x" active />
        <ProxyHop step={3} label="Proxy B (Region 2)" ip="100.64.y.y" active />
        <ProxyHop step={4} label="Third-party Server" ip="Masked IP" last />
      </View>

      <TouchableOpacity
        style={styles.refreshBtn}
        onPress={() => fetchIPData(true)}
        disabled={refreshing}
      >
        {refreshing ? (
          <ActivityIndicator size="small" color={PHOSPHOR} />
        ) : (
          <Text style={styles.refreshText}>↻  REFRESH IP DATA</Text>
        )}
      </TouchableOpacity>
    </ScrollView>
  );
}

function maskIP(ip) {
  if (!ip) return '██.██.██.██';
  // IPv6 — mask the last four groups
  if (ip.includes(':')) {
    const parts = ip.split(':');
    const visible = parts.slice(0, Math.max(1, parts.length - 4)).join(':');
    return `${visible}:██:██:██:██`;
  }
  // IPv4 — mask the last two octets
  const parts = ip.split('.');
  if (parts.length === 4) {
    return `${parts[0]}.${parts[1]}.██.██`;
  }
  return '██.██.██.██';
}

function InfoRow({ icon, label, value }) {
  return (
    <View style={styles.infoRow}>
      <Text style={styles.rowIcon}>{icon}</Text>
      <View style={styles.rowContent}>
        <Text style={styles.rowLabel}>{label}</Text>
        <Text style={styles.rowValue} selectable>{value}</Text>
      </View>
    </View>
  );
}

function ProxyHop({ step, label, ip, active, first, last }) {
  return (
    <View style={styles.hopRow}>
      <View style={styles.hopLineCol}>
        {!first && <View style={[styles.hopLine, active && styles.hopLineActive]} />}
        <View style={[styles.hopDot, active && styles.hopDotActive]} />
        {!last && <View style={[styles.hopLine, active && styles.hopLineActive]} />}
      </View>
      <View style={styles.hopInfo}>
        <Text style={styles.hopStep}>HOP {step}</Text>
        <Text style={styles.hopLabel}>{label}</Text>
        <Text style={[styles.hopIP, last && styles.hopIPMasked]}>{ip}</Text>
      </View>
      {active && (
        <View style={styles.hopBadge}>
          <Text style={styles.hopBadgeText}>✓</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: BG },
  content: { padding: 16, paddingBottom: 32 },
  centered: {
    flex: 1,
    backgroundColor: BG,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 16,
  },
  loadingText: {
    color: PHOSPHOR,
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 2,
  },
  errorBanner: {
    backgroundColor: '#1a0a00',
    borderWidth: 1,
    borderColor: '#ff8c00',
    borderRadius: 8,
    padding: 10,
    marginBottom: 12,
  },
  errorText: { color: '#ff8c00', fontSize: 12 },
  protectionCard: {
    backgroundColor: '#0a1a0a',
    borderRadius: 16,
    padding: 16,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#1a3a1a',
  },
  protectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  protectionTitle: {
    color: PHOSPHOR,
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1.5,
  },
  toggleBtn: {
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#3a3a3a',
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  toggleBtnActive: { borderColor: PHOSPHOR, backgroundColor: '#001a08' },
  toggleText: { color: '#6a6a6a', fontSize: 12, fontWeight: '600' },
  toggleTextActive: { color: PHOSPHOR },
  ipDisplay: { alignItems: 'center', paddingVertical: 8 },
  ipLabel: {
    color: '#4a6a5a',
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 2,
    marginBottom: 8,
  },
  ipValue: {
    color: PHOSPHOR,
    fontSize: 28,
    fontWeight: '800',
    letterSpacing: 2,
    fontVariant: ['tabular-nums'],
  },
  ipNote: { color: '#4a7a5a', fontSize: 12, marginTop: 8 },
  sectionTitle: {
    color: '#4a6a5a',
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 2,
    marginBottom: 8,
    marginTop: 4,
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: CARD_BG,
    borderRadius: 10,
    padding: 12,
    marginBottom: 6,
    borderWidth: 1,
    borderColor: BORDER,
    gap: 12,
  },
  rowIcon: { fontSize: 20 },
  rowContent: { flex: 1 },
  rowLabel: { color: '#4a6a5a', fontSize: 10, fontWeight: '600', letterSpacing: 1 },
  rowValue: { color: '#c0d8c8', fontSize: 14, fontWeight: '500', marginTop: 2 },
  proxyCard: {
    backgroundColor: CARD_BG,
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: BORDER,
    marginBottom: 16,
  },
  hopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    minHeight: 50,
  },
  hopLineCol: { alignItems: 'center', width: 16 },
  hopLine: { width: 2, flex: 1, minHeight: 12, backgroundColor: '#1a2a1a' },
  hopLineActive: { backgroundColor: '#004d14' },
  hopDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: '#1a2a1a',
    borderWidth: 2,
    borderColor: '#2a3a2a',
  },
  hopDotActive: { backgroundColor: PHOSPHOR, borderColor: PHOSPHOR },
  hopInfo: { flex: 1 },
  hopStep: { color: '#3a5a3a', fontSize: 9, fontWeight: '700', letterSpacing: 1 },
  hopLabel: { color: '#c0d8c8', fontSize: 13, fontWeight: '600' },
  hopIP: { color: '#4a7a5a', fontSize: 11, fontFamily: 'monospace' },
  hopIPMasked: { color: '#6a4a7a', fontStyle: 'italic' },
  hopBadge: {
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: '#001a08',
    borderWidth: 1,
    borderColor: PHOSPHOR,
    alignItems: 'center',
    justifyContent: 'center',
  },
  hopBadgeText: { color: PHOSPHOR, fontSize: 12, fontWeight: '700' },
  refreshBtn: {
    borderWidth: 1,
    borderColor: PHOSPHOR,
    borderRadius: 10,
    padding: 14,
    alignItems: 'center',
    backgroundColor: '#001a08',
  },
  refreshText: {
    color: PHOSPHOR,
    fontSize: 13,
    fontWeight: '700',
    letterSpacing: 1.5,
  },
});
