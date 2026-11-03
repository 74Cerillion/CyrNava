# Draft only — Flathub object GET returns 200/403 with different client identification

Not submitted. This report concerns repository delivery, before any application
build or launch. Please help identify the denying delivery rule and the supported
way for the normal OSTree/Flatpak client to acquire the approved content.

## Immutable object and client context

- Official repository: https://dl.flathub.org/repo/
- Ref: `runtime/org.kde.Platform/x86_64/6.11`
- Commit: `fb23e178d082b117df7924f9a84710992ec233ebc007385feb85d349c4c81415`
- Object: https://dl.flathub.org/repo/objects/fb/23e178d082b117df7924f9a84710992ec233ebc007385feb85d349c4c81415.commit
- Ubuntu x86_64 host; libostree `2025.7`. The reviewed acquisition client also
  reports Flatpak `1.16.6`. Host curl version/default User-Agent were not retained;
  the earlier isolated Codex environment reported curl `8.18.0`.
- The original isolated `ostree pull --disable-static-deltas --network-retries=0
  --depth=0` failed on this URL. No full payload was acquired.

## Observations on 2 November 2026, UTC

| Environment / response Date | Default curl | curl with `libostree/2025.7` | Clean-environment curl |
| --- | --- | --- | --- |
| Codex; 09:55:04 / 09:55:34 / 09:55:34 | HTTP/2 200 | HTTP/2 403 | HTTP/2 200 |
| Normal Ubuntu terminal; all 10:08:32 | HTTP/2 200 | HTTP/2 403 | HTTP/2 200 |

Every 200 body is 5,020 bytes with SHA-256 equal to the commit above. Earlier
fresh official ref readback advertised this commit; separately fetched commitmeta
validated with the configured upstream public key and the exact signed ref binding.
This proves metadata availability, not complete runtime acquisition.

200 headers: `server: nginx`, `content-type: application/octet-stream`,
`via: 1.1 varnish, 1.1 varnish`, `x-cache: HIT, HIT`.
403 headers: `server: Varnish`, `content-type: text/html; charset=utf-8`,
`retry-after: 0`, `via: 1.1 varnish`, `x-cache: MISS`; body 420 bytes.
No redirect was advertised. Host curl reported TLS verification result `0` for
all three requests. Proxy/CA override environment variables checked by the host
diagnostic were absent; that does not rule out network intermediaries.

Host responses used different edges: success `cache-icn1450023-ICN` and
`cache-icn1450049-ICN`, with `cache-lhr-egwu1540075-LHR` as the other reported
node; refusal `cache-icn1450055-ICN`. Earlier refusal used `cache-icn1450086-ICN`.
No client/peer IP address is included. These names do not establish the client path.

## Small reproduction definition

These are diagnostic requests, not a proposed way to disguise an acquisition
client. The two calls intentionally differ only in User-Agent. They run as
separate connections in fixed order; CDN node, address family, TLS session and
timing were not controlled. The full native OSTree request was not captured.

```bash
object_url='https://dl.flathub.org/repo/objects/fb/23e178d082b117df7924f9a84710992ec233ebc007385feb85d349c4c81415.commit'
curl --disable --silent --show-error --connect-timeout 5 --max-time 15 \
  --max-filesize 1048576 --proto '=https' --output /dev/null \
  --write-out 'status=%{http_code} http=%{http_version} tls=%{ssl_verify_result}\n' "$object_url"
curl --disable --silent --show-error --connect-timeout 5 --max-time 15 \
  --max-filesize 1048576 --proto '=https' --user-agent 'libostree/2025.7' \
  --output /dev/null \
  --write-out 'status=%{http_code} http=%{http_version} tls=%{ssl_verify_result}\n' "$object_url"
```

`--disable` ignores curlrc; TLS verification stays enabled. No retries, redirect
following, authentication, Range, compression or explicit HTTP-version options
were supplied. The retained diagnostic saved bodies privately for hash checks.
Its third call used default identification with a minimal environment, also 200.

Could infrastructure maintainers check the recorded UTC requests and ICN delivery
policy/cache routing for this object and client identification? We cannot yet
attribute the refusal exclusively to User-Agent, an operator, a proxy or a VPN.
We have not changed dependencies, signatures, client identification for actual
acquisition, TLS settings, mirrors or normal host configuration.

Raw response bodies, arbitrary headers, environment values and personal paths
are intentionally excluded. Flathub's [network troubleshooting guide](https://docs.flathub.org/docs/for-users/slow-connection)
links to the [infrastructure issue template](https://github.com/flathub/flathub/issues/new?template=3-slow-connection.md).
The owner can review this draft and choose whether to submit it; no contact has
been made on their behalf.
