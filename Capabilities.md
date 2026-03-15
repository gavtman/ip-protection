Some Privacy Sandbox technologies are being phased out. Please see our
[Update on Plans for Privacy Sandbox Technologies](https://privacysandbox.com/news/update-on-plans-for-privacy-sandbox-technologies/).

[Privacy Sandbox feature status](https://privacysandbox.google.com/overview/status)
provides more information about the status of individual APIs and platform features.

This repository will be archived and no longer updated.

# IP Protection: Overview of Capabilities

This document provides a concise summary of what IP Protection can and cannot
do. For full technical details, refer to the [README](./README.md) and the
other explainer documents in this repository.

## What IP Protection Can Do

### Mask IP Addresses in Third-Party Contexts

IP Protection routes qualifying third-party traffic through a two-hop proxy
system so that destination servers see a masked IP address instead of the
user's real IP address. This prevents third-party domains on the
[Masked Domain List (MDL)](./Masked-Domain-List.md) from using IP addresses to
track users across websites over time.

### Protect Users in Incognito Mode

IP Protection is available exclusively in Chrome's Incognito mode on Android
and Desktop. Users can disable the feature at any time. Enterprise-managed
versions of Chrome can enable the feature, but it is off by default.

### Preserve Coarse Geolocation

The masked IP addresses assigned by the proxy retain coarse geolocation
information down to the country level and, where population density allows, to
a metropolitan area. This means that IP-based geolocation continues to work for
broad use cases such as content localisation, regional compliance, and
geo-targeted advertising. See the
[IP Geolocation Explainer](./Explainer-IP-Geolocation.md) for details.

### Prevent Any Single Entity from Linking User Identity to Destination

The two-hop proxy architecture ensures that:

- **proxyA** (operated by Google) can see the user's real IP address but **not**
  the destination domain.
- **proxyB** (operated by an external CDN) can see the destination domain but
  **not** the user's real IP address.

As a result, no single party operating the system can associate a user's IP
address with the sites they visit.

### Support Fraud and Spam Detection via Probabilistic Reveal Tokens (PRTs)

To help services measure invalid traffic (IVT) and detect fraud while IP
Protection is active, Chrome implements
[Probabilistic Reveal Tokens](./prt_explainer.md). A small, random fraction of
PRTs include the user's pre-proxy IP address (revealed only after a delay),
allowing sites to:

- Measure fraud and spam in aggregate.
- Update publisher reputation signals.
- Identify new attack patterns.

The vast majority of PRTs contain no IP information, keeping user privacy intact
while still enabling fraud detection.

### Apply Selectively Based on the Masked Domain List

Only domains that appear on the [MDL](./Masked-Domain-List.md) **and** are
loaded in a **third-party context** are affected. First-party requests to MDL
domains, and all requests to non-MDL domains, continue to use the user's real
IP address unchanged.

## What IP Protection Cannot Do

- **Protect traffic outside Incognito mode.** IP Protection only applies when
  the user is browsing in Chrome's Incognito mode.
- **Mask all traffic.** Only third-party requests to domains on the MDL are
  proxied. First-party traffic and traffic to domains not on the MDL are
  unaffected.
- **Guarantee precise geolocation.** The masked IP retains country-level and
  coarse sub-country accuracy but cannot guarantee exact city, state, or
  regional accuracy, especially near borders.
- **Replace VPNs or full anonymisation tools.** IP Protection addresses
  cross-site tracking via IP addresses in a third-party context; it is not
  designed to hide a user's IP address for all internet activity. See the
  [README section on IP Protection and VPNs](./README.md#ip-protection-and-vpns)
  for a comparison.
- **Provide real-time fraud signals.** PRTs are subject to a delay period
  before the contained IP addresses can be decrypted, so they are unsuitable
  for real-time fraud prevention.

## Availability

IP Protection is available in the countries listed in
[Supported-Countries.md](./Supported-Countries.md). The feature launched to
Chrome Stable no sooner than July 2025 and availability is expanding over time.
