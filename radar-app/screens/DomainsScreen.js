import React, { useState, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TextInput,
  TouchableOpacity,
} from 'react-native';

const PHOSPHOR = '#00ff41';
const BG = '#0a0e1a';
const CARD_BG = '#0d1224';
const BORDER = '#1a2340';

const CATEGORY_COLORS = {
  Analytics: { bg: '#1a0a2a', border: '#6a3aaa', text: '#c080ff' },
  Advertising: { bg: '#1a0a00', border: '#aa5a00', text: '#ffaa40' },
  CDN: { bg: '#0a1a1a', border: '#1a6a6a', text: '#40d0d0' },
  Social: { bg: '#0a0e2a', border: '#1a3aaa', text: '#6080ff' },
  Tracking: { bg: '#1a0a0a', border: '#aa1a1a', text: '#ff6060' },
  'A/B Testing': { bg: '#1a1a0a', border: '#7a7a1a', text: '#d0d040' },
  Telemetry: { bg: '#0a1a0a', border: '#2a6a2a', text: '#60c060' },
  Maps: { bg: '#0a1a1a', border: '#1a6a5a', text: '#40c0a0' },
};

const DOMAINS = [
  { id: '1',  domain: 'google-analytics.com',     company: 'Google',     category: 'Analytics' },
  { id: '2',  domain: 'doubleclick.net',           company: 'Google',     category: 'Advertising' },
  { id: '3',  domain: 'googlesyndication.com',     company: 'Google',     category: 'Advertising' },
  { id: '4',  domain: 'googletagmanager.com',      company: 'Google',     category: 'Analytics' },
  { id: '5',  domain: 'connect.facebook.net',      company: 'Meta',       category: 'Social' },
  { id: '6',  domain: 'graph.facebook.com',        company: 'Meta',       category: 'Social' },
  { id: '7',  domain: 'scorecardresearch.com',     company: 'Comscore',   category: 'Analytics' },
  { id: '8',  domain: 'omtrdc.net',                company: 'Adobe',      category: 'Analytics' },
  { id: '9',  domain: 'demdex.net',                company: 'Adobe',      category: 'Advertising' },
  { id: '10', domain: 'amazon-adsystem.com',       company: 'Amazon',     category: 'Advertising' },
  { id: '11', domain: 'cloudfront.net',            company: 'Amazon',     category: 'CDN' },
  { id: '12', domain: 'fastly.net',                company: 'Fastly',     category: 'CDN' },
  { id: '13', domain: 'cloudflareinsights.com',    company: 'Cloudflare', category: 'Analytics' },
  { id: '14', domain: 'hotjar.com',                company: 'Hotjar',     category: 'Analytics' },
  { id: '15', domain: 'mixpanel.com',              company: 'Mixpanel',   category: 'Analytics' },
  { id: '16', domain: 'segment.io',                company: 'Segment',    category: 'Analytics' },
  { id: '17', domain: 'optimizely.com',            company: 'Optimizely', category: 'A/B Testing' },
  { id: '18', domain: 'twitter.com',               company: 'X Corp',     category: 'Social' },
  { id: '19', domain: 'ads.twitter.com',           company: 'X Corp',     category: 'Advertising' },
  { id: '20', domain: 'linkedin.com',              company: 'Microsoft',  category: 'Social' },
  { id: '21', domain: 'snap.com',                  company: 'Snap',       category: 'Social' },
  { id: '22', domain: 'sentry.io',                 company: 'Sentry',     category: 'Telemetry' },
  { id: '23', domain: 'newrelic.com',              company: 'New Relic',  category: 'Telemetry' },
  { id: '24', domain: 'datadog-browser-agent.com', company: 'Datadog',    category: 'Telemetry' },
  { id: '25', domain: 'maps.googleapis.com',       company: 'Google',     category: 'Maps' },
  { id: '26', domain: 'criteo.com',                company: 'Criteo',     category: 'Advertising' },
  { id: '27', domain: 'quantserve.com',            company: 'Quantcast',  category: 'Analytics' },
  { id: '28', domain: 'chartbeat.com',             company: 'Chartbeat',  category: 'Analytics' },
  { id: '29', domain: 'taboola.com',               company: 'Taboola',    category: 'Advertising' },
  { id: '30', domain: 'outbrain.com',              company: 'Outbrain',   category: 'Advertising' },
];

const ALL_CATEGORIES = ['All', ...Object.keys(CATEGORY_COLORS)];

export default function DomainsScreen() {
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');

  const filtered = useMemo(() => {
    const q = search.toLowerCase().trim();
    return DOMAINS.filter((d) => {
      const matchSearch =
        !q ||
        d.domain.toLowerCase().includes(q) ||
        d.company.toLowerCase().includes(q) ||
        d.category.toLowerCase().includes(q);
      const matchCat =
        selectedCategory === 'All' || d.category === selectedCategory;
      return matchSearch && matchCat;
    });
  }, [search, selectedCategory]);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={styles.searchBox}>
          <Text style={styles.searchIcon}>🔍</Text>
          <TextInput
            style={styles.searchInput}
            placeholder="Search domains, companies..."
            placeholderTextColor="#3a5a4a"
            value={search}
            onChangeText={setSearch}
            autoCapitalize="none"
            autoCorrect={false}
          />
          {search.length > 0 && (
            <TouchableOpacity onPress={() => setSearch('')}>
              <Text style={styles.clearBtn}>✕</Text>
            </TouchableOpacity>
          )}
        </View>

        <FlatList
          horizontal
          data={ALL_CATEGORIES}
          keyExtractor={(item) => item}
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.categoryList}
          renderItem={({ item }) => {
            const active = item === selectedCategory;
            const colors = CATEGORY_COLORS[item];
            return (
              <TouchableOpacity
                style={[
                  styles.categoryChip,
                  active && { backgroundColor: colors?.bg ?? '#001a08', borderColor: colors?.border ?? PHOSPHOR },
                ]}
                onPress={() => setSelectedCategory(item)}
              >
                <Text
                  style={[
                    styles.categoryChipText,
                    active && { color: colors?.text ?? PHOSPHOR },
                  ]}
                >
                  {item}
                </Text>
              </TouchableOpacity>
            );
          }}
        />

        <View style={styles.statsRow}>
          <Text style={styles.statsText}>
            <Text style={styles.statsCount}>{filtered.length}</Text>
            {' '}domains protected
          </Text>
          <View style={styles.shieldBadge}>
            <Text style={styles.shieldText}>🛡️ ALL MASKED</Text>
          </View>
        </View>
      </View>

      <FlatList
        data={filtered}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.list}
        showsVerticalScrollIndicator={false}
        renderItem={({ item }) => <DomainCard domain={item} />}
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Text style={styles.emptyIcon}>🔒</Text>
            <Text style={styles.emptyText}>No domains match your search</Text>
          </View>
        }
      />
    </View>
  );
}

function DomainCard({ domain }) {
  const colors = CATEGORY_COLORS[domain.category] ?? {
    bg: '#0a1a0a',
    border: '#1a4a1a',
    text: PHOSPHOR,
  };

  return (
    <View style={styles.card}>
      <View style={styles.cardLeft}>
        <View style={styles.domainIconWrap}>
          <Text style={styles.domainInitial}>
            {domain.company.charAt(0).toUpperCase()}
          </Text>
        </View>
        <View style={styles.cardInfo}>
          <Text style={styles.domainName} selectable>{domain.domain}</Text>
          <Text style={styles.companyName}>{domain.company}</Text>
        </View>
      </View>
      <View style={styles.cardRight}>
        <View style={[styles.catBadge, { backgroundColor: colors.bg, borderColor: colors.border }]}>
          <Text style={[styles.catText, { color: colors.text }]}>{domain.category}</Text>
        </View>
        <View style={styles.protectedBadge}>
          <Text style={styles.protectedText}>✓ MASKED</Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: BG },
  header: {
    backgroundColor: CARD_BG,
    borderBottomWidth: 1,
    borderBottomColor: BORDER,
    paddingTop: 12,
    paddingHorizontal: 12,
  },
  searchBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#060d18',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: BORDER,
    paddingHorizontal: 10,
    marginBottom: 10,
    gap: 8,
  },
  searchIcon: { fontSize: 14 },
  searchInput: {
    flex: 1,
    color: '#c0d8c8',
    fontSize: 14,
    paddingVertical: 10,
  },
  clearBtn: { color: '#4a6a5a', fontSize: 14, paddingHorizontal: 4 },
  categoryList: { paddingBottom: 10, gap: 6 },
  categoryChip: {
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: BORDER,
    backgroundColor: 'transparent',
  },
  categoryChipText: {
    color: '#4a6a5a',
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.5,
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
    borderTopWidth: 1,
    borderTopColor: BORDER,
    marginTop: 2,
  },
  statsText: { color: '#4a6a5a', fontSize: 12 },
  statsCount: { color: PHOSPHOR, fontWeight: '700' },
  shieldBadge: {
    backgroundColor: '#001a08',
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderWidth: 1,
    borderColor: '#1a4a1a',
  },
  shieldText: { color: PHOSPHOR, fontSize: 10, fontWeight: '700', letterSpacing: 1 },
  list: { padding: 12, gap: 8 },
  card: {
    backgroundColor: CARD_BG,
    borderRadius: 12,
    padding: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderWidth: 1,
    borderColor: BORDER,
  },
  cardLeft: { flexDirection: 'row', alignItems: 'center', flex: 1, gap: 10 },
  domainIconWrap: {
    width: 36,
    height: 36,
    borderRadius: 8,
    backgroundColor: '#1a2a3a',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: '#2a3a4a',
  },
  domainInitial: { color: '#80a0c0', fontSize: 16, fontWeight: '700' },
  cardInfo: { flex: 1 },
  domainName: { color: '#c0d8c8', fontSize: 13, fontWeight: '600' },
  companyName: { color: '#4a6a7a', fontSize: 11, marginTop: 2 },
  cardRight: { alignItems: 'flex-end', gap: 5 },
  catBadge: {
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderWidth: 1,
  },
  catText: { fontSize: 10, fontWeight: '700', letterSpacing: 0.5 },
  protectedBadge: {
    backgroundColor: '#001a08',
    borderRadius: 6,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderWidth: 1,
    borderColor: '#1a4a1a',
  },
  protectedText: {
    color: PHOSPHOR,
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  emptyState: { alignItems: 'center', paddingTop: 60, gap: 12 },
  emptyIcon: { fontSize: 40 },
  emptyText: { color: '#3a5a4a', fontSize: 14 },
});
