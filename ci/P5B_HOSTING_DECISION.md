# P5B hosting decision — direction endorsed, not provisioned

31 October 2026. Implementation uses a provider-neutral static repository snapshot.
Recommendation: R2-compatible object storage for the eventual update remote, with
GitHub Releases as an optional bundle/provenance mirror.
**R2-compatible direction owner-endorsed.** Specific provider/account, endpoint,
domain and cost/provisioning approval remain separate; no infrastructure is authorized.
No account, bucket, domain, endpoint, DNS, payment or public deployment was created.

## Actual baseline and measurement limits

Source: accepted P5A run 41181510439, implementation 1ee2077; acceptance docs 1a28f68.
The downloaded artifact was independently hashed again during P5B inspection.
Owner Ubuntu evidence is preserved in `evidence/p5b/owner-native-2026-10-31/`;
the active signed generation was independently verified and rehashed. Earlier
unmeasured figures remain in the archived pre-native assessment.

| Quantity | Value | Evidence |
| --- | --- | --- |
| Standalone Flatpak bundle | 209,189,544 bytes | SHA 93957ce5590818e016c5b9e86ed9c6c1d32a684f6c644af44531c316020b26db |
| GitHub CI ZIP | 210,238,004 bytes | P5A artifact metadata; not repository size |
| Logical installed application | 980,984,007 bytes | Accepted payload inventory |
| Audited payload entries | 5,320 | Files/links, not repository object-file count |
| Initial archive repository | 301,341,805 bytes / 287.38 MiB; 5,554 files | Owner native PASS; independently recomputed from signed inventory |
| Signed metadata counter | 2,016 bytes | `.sig` and `.commitmeta` bytes; not a comparative before/after storage benchmark |
| Static deltas | Disabled; 0 delta bytes | Enabled-delta overhead/savings unmeasured |
| Generation / signing-summary / total rehearsal | 102.06 / 0.13 / 161.167 seconds | One host; signing included in generation; all native drills included in total |
| Actual fresh-install / small-update transfer | Not measured | File-remote rehearsal is not an HTTP or version-to-version benchmark |

Do not compare the uncompressed application directly to a provider's published
repository limit. Native storage/count/timing figures above are measured; retention
growth, client transfers and request/cost figures below remain estimates.

## Provider comparison

| Criterion | GitHub Pages | GitHub Releases | Object storage: R2 | Alternative: Netlify static deploy |
| --- | --- | --- | --- | --- |
| Appropriate role | Small static remote, conditional on size/traffic | Bundle, checksums, notes and provenance mirror | Main archive-z2 update remote | Atomic static snapshot hosting |
| Capacity / file count | Published site 1 GB; many small objects consume it | Assets under 2 GiB each, up to 1,000 per release | Object layout; capacity scales with billing | Static files; confirm per-file/deploy constraints before approval |
| Bandwidth | 100 GB/month soft limit | No documented release bandwidth limit | No direct R2 egress fee; request costs still matter | Credit-metered transfer and requests |
| HTTP and deltas | Static HTTP; requests/rate limits need P5C measurement | Stable OSTree object URL layout not supplied by assets alone | HTTPS GET/HEAD, object paths and deltas fit; test cache/range/keep-alive | HTTPS/CDN; test binary headers, rewrites and cache behavior |
| Updates | Possible when a complete repository is served | A bundle download is not an update remote | Native Flatpak remote model | Native remote if snapshot layout preserved |
| Safe publication | Actions deploy snapshot; retained old objects needed | Asset upload is not multi-object repository publication | Objects before metadata; generation/pointer adapter required | Atomic deploy primitive; include retained client objects |
| Actions integration | Extra Pages deployment permissions | Future contents-write publication job | Future narrow object-prefix credentials | Future project-scoped deploy token |
| Geographic access | CDN/service availability; no universal-access guarantee | GitHub regional/network access applies | CDN/domain choice; regional/legal access needs validation | Global CDN; regional access needs validation |
| Portability | Static layout portable; avoid Git history for object storage | URLs and release API specific | S3-style object layout portable; domain migration/trust must be planned | Static layout portable; deployment control plane specific |
| Maintenance/security | Avoid aggressive pruning, avoid committing binary history | Retain authenticated trust anchor separately from checksums | Protect write credentials; prevent cached mutable metadata inconsistencies | Quota/paused-site risk; scoped credentials and snapshot retention |

Official limits: [Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits),
[Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases).
One measured repository uses approximately 30% of Pages' 1 GB published-site limit:
Pages is viable for a small pilot. Three full equal-sized snapshots would occupy
904,025,415 bytes; four would occupy 1,205,367,220 bytes and 22,216 files before
extra site files/deltas. This full-copy estimate does not measure deduplicated
multi-release history. In-place object reuse may reduce growth; generation copies
duplicate it. No automatic pruning is justified. Retention headroom and growth
traffic still favor R2 as the proposed long-term remote. HTTP request latency and
cache behavior need subsequent validation.

## Cost model — USD, official prices checked 31 October 2026

R2 Standard: $0.015/GB-month, $4.50/million Class A operations and $0.36/million
Class B operations; included monthly allowances are 10 GB, 1 million A and 10 million
B operations. Direct egress is free. Billing rounds units; these are not a quote
or spending guarantee. [Official pricing](https://developers.cloudflare.com/r2/pricing/).

Assumptions, **not measured transfers**: 0.301341805 GB initial application-download
proxy from the entire measured repository, replacing the former 0.25 GB guess;
two 0.01 GB small application updates per installation/month, 6,400 read requests
per installation/month, four releases/month, approximately 24,000 write requests,
and 2 GB retained storage. Runtime/SDK downloads, custom domain, routing, taxes,
CI consumption and abusive traffic are excluded. The proxy is not an observed
fresh-install transfer: clients fetch needed refs/objects, not necessarily every
file. The 5,554 files anchor request order, but HEAD/metadata/cache/update behavior
is unmeasured. Four full snapshots require 22,216 repository writes plus other
metadata/list/readback operations, supporting the rounded 24,000-write allowance.
Actual multi-release deduplication is unknown. Arithmetic and assumptions are in
`evidence/p5b/owner-native-2026-10-31/hosting-model.json`.

| Scenario | Installations | Monthly app traffic | Reads | R2 core estimate | Pages traffic assessment |
| --- | ---: | ---: | ---: | --- | --- |
| Small | 5 | 1.61 GB | 32,000 | $0 within stated allowances | Below soft cap; one snapshot fits |
| Moderate | 100 | 32.13 GB | 640,000 | $0 within stated allowances | Below soft cap; retention needs planning |
| Growth | 1,000 | 321.34 GB | 6.4 million | $0 within stated allowances | Exceeds 100 GB soft cap |

At 20 GB retained storage the storage-only increment would be approximately
$0.15/month above the included 10 GB, subject to rounding and other services.
Growth assumptions can change substantially if files are highly compressible,
clients reinstall, metadata is fetched frequently or static deltas alter requests.

Netlify currently meters bandwidth at 20 credits/GB and requests at 2 credits/10k;
four production deploys consume another 60 credits. The same modeled scenarios
need about 98.53 / 830.68 / 7,766.84 credits per month. Free includes 300; Personal is
$9/month with 1,000; Pro starts at $20/month with 3,000. Growth requires a larger
tier or approved add-ons: obtain the actual quote before choosing it. Old
bandwidth-only Netlify prices are not used. [Official plans](https://docs.netlify.com/manage/accounts-and-billing/billing/billing-for-credit-based-plans/credit-based-pricing-plans/),
[pricing](https://www.netlify.com/pricing/).

Public-repository P5A CI already ran in roughly fourteen minutes wall time, with
parallel application jobs; promotion avoids duplicating that application build.
Native P5B rehearsal took 161.167 seconds total; generation took 102.06 seconds,
including 0.13 seconds for signing/summary on that host. Hosted runner/billing time
is unmeasured; do not represent this local timing as an actual Actions bill.

## Publication architecture and static deltas

Current implementation publishes only to a marked private local staging store:

1. Verify approved artifact/source/CI lineage and the P5A exported-payload audit.
2. Generate a signed repository, descriptors and signed inventory.
3. Copy and verify a complete immutable generation before activating it.
4. Retain all prior immutable object/delta bytes required by existing clients.
5. Serialize publication; atomically replace the local active pointer on one
   filesystem, after syncing data and directory entries. Never prune automatically.

R2 does not offer atomic replacement of an entire directory. A future adapter must
upload generation objects, read back/verify them, then update an active-generation
pointer with concurrency protection. It needs a verified stable-URL mapping and
cache policy; the present local symlink is a contract model, not an R2 deployment.
No cloud adapter or production network writer is enabled. Netlify's atomic deploy
is a possible alternative when an extra pointer-serving layer is undesirable.

Multi-request clients can straddle any metadata switch; signatures must reject a
mixed summary/signature pair. Native client convergence, caches and concurrent
updates require P5C validation. Do not claim a local atomic rename proves HTTP
transactionality. R2 origin consistency does not remove CDN cache effects:
[consistency](https://developers.cloudflare.com/r2/reference/consistency/).
Its rate-limited `r2.dev` URL is for development; production needs an approved
domain/access design, not an invented endpoint:
[public buckets](https://developers.cloudflare.com/r2/buckets/public-buckets/).

Static deltas default **off**. The optional staging flag measures their cost;
full deltas can duplicate roughly a bundle's worth of compressed data, but exact
overhead and small-update savings remain unmeasured. Ordinary object pulls remain
supported. [Flatpak hosting guidance](https://docs.flatpak.org/en/latest/hosting-a-repository.html).

Before final selection: owner reviews hosting/domain costs, native measurements,
retention, cache/metadata-switch testing and publication credentials. Changing hosts
must preserve signed refs, retained objects and trust/bootstrap paths; test remote
URL migration and rollback before retiring the old endpoint. No approval is needed
to continue the already-authorized provider-neutral local implementation.
