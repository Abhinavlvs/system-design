# Protocols by Layer: A Working Catalog

Sourcing note: this file is **general networking knowledge, not taken from the four Wikipedia pages** fetched earlier. Those pages give the layer models (see `Internet_protocol_suite.md`, `OSI_model.md`) and HTTP/TCP detail, but not a full protocol inventory. Port numbers and RFC numbers below are from memory and should be checked against the IANA registries and the RFC index before you rely on them.

**On "every protocol":** a complete list is not possible. IANA's port registry alone has thousands of entries and anyone can invent a new application protocol. This catalog covers the protocols you will actually meet, grouped so you can see how they relate, and explains each one.

---

## 1. The map

```
 Application   HTTP/1.1  HTTP/2  HTTP/3  WebSocket  gRPC  Thrift  DNS  DHCP  NTP
               SMTP  IMAP  SSH  FTP  MQTT  AMQP  Kafka  Postgres  Redis  SNMP  SIP ...
 -----------------------------------------------------------------------------------
 Security*     TLS (over TCP)          DTLS (over UDP)       QUIC has TLS 1.3 inside
 -----------------------------------------------------------------------------------
 Transport     TCP         UDP         QUIC (on UDP)         SCTP    DCCP
 -----------------------------------------------------------------------------------
 Internet      IPv4        IPv6        ICMP / ICMPv6         IGMP / MLD       IPsec
 -----------------------------------------------------------------------------------
 Link          Ethernet    Wi-Fi       PPP     ARP / NDP     VLAN     Bluetooth  5G
```

\* TLS has no clean home in the layer models. See `HTTPS.md`.

How the layers relate (recap):
- Each layer **uses the one below** and hides its details from the one above.
- **IP is the narrow waist.** Many protocols above and below, one protocol in the middle.
- Real protocols often break the tidy layering. This catalog notes where.

---

## 2. Link layer: how bits move on one network segment

The link layer covers communication between **directly connected** devices (same cable, same Wi-Fi network, same VLAN). It is hardware-specific, so there is a protocol per medium.

| Protocol | What it does | Why it matters |
|---|---|---|
| **Ethernet (IEEE 802.3)** | Wired LAN framing: source and destination **MAC addresses**, a type field, payload (up to 1500 bytes by default, the usual MTU), and a CRC checksum | Nearly every wired network and data center. Switches forward frames by MAC address |
| **Wi-Fi (IEEE 802.11)** | Wireless LAN. Handles shared-air access (collision avoidance, not detection), association with an access point, encryption (WPA2/WPA3) | Everyday wireless access. Different framing from Ethernet but looks like Ethernet to IP |
| **PPP** | Point-to-point link between two nodes, with authentication and option negotiation | Dial-up, DSL, and as the base for tunnels such as L2TP |
| **HDLC / Frame Relay / ATM** | Older WAN link technologies | Mostly legacy, but still appear in carrier networks and in textbooks |
| **ARP (Address Resolution Protocol, RFC 826)** | Asks "who has IP 10.0.0.5?" and gets back a MAC address | IP needs a MAC to deliver a frame on the local link. Sits on the boundary between link and internet layers |
| **NDP (Neighbor Discovery, RFC 4861)** | IPv6's replacement for ARP, built on ICMPv6. Also does router discovery and address autoconfiguration | Required for IPv6 to work |
| **VLAN (IEEE 802.1Q)** | Adds a tag to Ethernet frames so one physical network carries many isolated logical networks | Network segmentation in offices and data centers |
| **STP / RSTP (IEEE 802.1D / 802.1w)** | Prevents loops in switched networks by blocking redundant links | Without it, a looped Ethernet network collapses in a broadcast storm |
| **LLDP / CDP** | Devices announce who they are to their neighbors | Network discovery and troubleshooting |
| **MACsec (IEEE 802.1AE)** | Encrypts and authenticates Ethernet frames hop by hop | Link-level security. Named in the OSI notes as the layer 2 security option |
| **Bluetooth, Zigbee (802.15.4), LoRa** | Short-range and low-power radio links | IoT and personal devices |
| **Cellular (LTE, 5G NR)** | Mobile access networks with their own full protocol stacks (RRC, PDCP, MAC, ...) | Phones and mobile IoT. The OSI notes list UMTS entries at layers 1-3 |
| **MPLS ("layer 2.5")** | Forwards by short **labels** instead of IP lookups, sits between link and IP | Carrier backbones and traffic engineering. The OSI notes mention it as a cross-layer "3a" protocol |

Key idea: the link layer only has to get a frame to the **next hop**. A packet crossing the internet is re-wrapped in a new link-layer frame at every router.

---

## 3. Internet layer: addressing and routing across networks

| Protocol | What it does | Details |
|---|---|---|
| **IPv4 (RFC 791)** | Addressing and best-effort delivery of **datagrams** | 32-bit addresses, about 4 billion. **Unreliable**: packets can be lost, duplicated or reordered, and higher layers deal with it. Fragments large packets if needed |
| **IPv6 (RFC 8200)** | Successor to IPv4 | 128-bit addresses, fixed simpler header, no router fragmentation, built-in autoconfiguration. Created to fix address exhaustion |
| **ICMP / ICMPv6 (RFC 792 / 4443)** | Error and diagnostic messages from the network | "Destination unreachable", "time exceeded" (what `traceroute` uses) and echo (`ping`). ICMPv6 also carries NDP. IP protocol number 1 |
| **IGMP (v3: RFC 3376) / MLD (IPv6)** | Hosts tell routers which **multicast** groups they want | IPTV and some discovery protocols |
| **IPsec** | Encrypts and authenticates IP packets. Two protocols: **ESP** (encryption, IP protocol 50) and **AH** (authentication, 51). **IKE** negotiates keys | The basis of many site-to-site VPNs |
| **GRE (IP protocol 47)** | Wraps one packet inside another to make a tunnel | Simple tunnels. The Internet-suite notes mention it as recursive encapsulation |
| **NAT (not a protocol)** | Rewrites addresses and ports so many private hosts share one public IP | Breaks the end-to-end principle, as the TCP/IP notes say |

### Routing protocols (a classification puzzle)

Routers use these to learn where networks are. They do not carry user data, but they run **over** IP, so the Wikipedia notes classify them as **application-layer** protocols (Tanenbaum puts them with IP).

| Protocol | Scope | Runs over |
|---|---|---|
| **OSPF** | Inside one organization (link-state) | Directly on IP (protocol 89) |
| **IS-IS** | Inside one organization | Its own encapsulation. The OSI notes say it is a network-layer protocol |
| **RIP** | Inside one organization (distance-vector, small networks) | UDP 520 |
| **BGP (RFC 4271)** | **Between** organizations. The protocol that glues the global internet together | TCP 179 |

BGP is one of the most important and most fragile protocols in the internet. A bad route announcement can send traffic to the wrong place. **RPKI** is the signing system being deployed to make it safer.

---

## 4. Transport layer: process-to-process delivery

The transport layer turns host-to-host delivery into **application-to-application** delivery, using **port numbers**.

| Protocol | Connection? | Reliable? | What it adds |
|---|---|---|---|
| **UDP (RFC 768)** | No | No | Ports and an optional checksum. Nothing else. 8-byte header |
| **TCP (RFC 9293)** | Yes | Yes | Ordered byte stream, retransmission, flow control, congestion control. Full detail in `TCP.md` |
| **QUIC (RFC 9000)** | Yes | Yes | TCP-like reliability **on top of UDP**, with multiple independent streams, built-in TLS 1.3, connection migration |
| **SCTP (RFC 9260)** | Yes | Yes | Message-oriented, multiple streams, multihoming. Used in telecom signalling and WebRTC data channels |
| **DCCP (RFC 4340)** | Yes | No | Congestion control for unreliable flows (streaming). Rarely deployed |
| **UDP-Lite (RFC 3828)** | No | No | Lets partly damaged payloads through, for codecs that tolerate bit errors |
| **MPTCP (RFC 8684)** | Yes | Yes | One TCP connection spread across several network paths (Wi-Fi plus cellular) |

### UDP vs TCP: when to use which

| Need | Choose |
|---|---|
| Every byte, in order (web, email, files, databases) | TCP |
| Fresh data matters more than old data (voice, video, games, DNS lookups) | UDP |
| Reliability and multiplexing without TCP's head-of-line blocking | QUIC |

### Why QUIC exists

- TCP lives in the OS kernel and its metadata is visible to middleboxes, so it is hard to change (**ossification**, see `TCP.md`).
- QUIC runs in user space on UDP, encrypts almost all of its own headers, and can evolve quickly.

---

## 5. The security "layer" (it does not fit neatly)

| Protocol | Runs over | What it does |
|---|---|---|
| **TLS (1.2 / 1.3)** | TCP | Encryption, integrity and server authentication for any application protocol. Detailed in `HTTPS.md` |
| **DTLS** | UDP | TLS adapted for datagrams. Used by WebRTC and some VPNs |
| **SSH** | TCP | Its own secure transport, authentication and channel multiplexing. Also an application protocol |
| **QUIC** | UDP | Includes TLS 1.3 inside the transport |
| **IPsec / WireGuard** | IP / UDP | Encrypt at the network level so all traffic between two endpoints is protected, as in a VPN |

---

## 6. Application layer

The application layer is the largest group. These are grouped by purpose.

### 6.1 Web and browser protocols

| Protocol | Notes |
|---|---|
| **HTTP/1.1** | Text-based request/response, one request at a time per connection (pipelining unsafe), keep-alive for reuse. See `HTTP.md` |
| **HTTP/2** | Same semantics, binary framing, multiplexed streams. Details in section 7 |
| **HTTP/3** | Same semantics over QUIC. Details in section 7 |
| **WebSocket (RFC 6455)** | Persistent two-way messaging, started with an HTTP request. Details in section 7 |
| **Server-Sent Events (SSE)** | Server pushes a stream of text events over a long-lived HTTP response. One-way, simpler than WebSocket |
| **WebRTC** | Browser-to-browser real-time media and data. A bundle: ICE/STUN/TURN for NAT traversal, DTLS-SRTP for media, SCTP over DTLS for data channels |
| **WebTransport** | Newer browser API for bidirectional streams and datagrams over HTTP/3 |

### 6.2 Naming, addressing and time

| Protocol | Port | What it does |
|---|---|---|
| **DNS (RFC 1035)** | UDP/TCP 53 | Translates names such as `example.com` to IP addresses. Hierarchical, distributed and cached. UDP for small queries, TCP for large ones |
| **DNS over TLS (DoT)** | TCP 853 | DNS encrypted with TLS |
| **DNS over HTTPS (DoH, RFC 8484)** | TCP 443 | DNS queries as HTTPS requests. Blends with web traffic |
| **DNS over QUIC (DoQ)** | UDP 853 | DNS over QUIC |
| **mDNS / DNS-SD** | UDP 5353 | Local-network name discovery with no server (printers, `.local` names) |
| **DHCP (RFC 2131)** | UDP 67/68 | Hands out IP address, gateway and DNS server when a device joins a network |
| **NTP** | UDP 123 | Clock synchronization |

### 6.3 Email

| Protocol | Port | Role |
|---|---|---|
| **SMTP (RFC 5321)** | 25 (relay), 587 (submission) | Sending mail and server-to-server transfer. Text commands (`HELO`, `MAIL FROM`, `RCPT TO`, `DATA`) |
| **IMAP** | 143, 993 (TLS) | Reading mail kept on the server, with folders and sync across devices |
| **POP3** | 110, 995 (TLS) | Older: download mail then usually delete it from the server |

Mail protocols use **STARTTLS** (upgrade a plain connection to TLS) or an implicit TLS port.

### 6.4 Remote access and file transfer

| Protocol | Port | Notes |
|---|---|---|
| **SSH** | 22 | Encrypted remote shell, tunnelling and port forwarding. Replaced Telnet |
| **SFTP / SCP** | over SSH | File transfer through an SSH channel. **SFTP is not FTP over TLS**, it is a different protocol |
| **Telnet** | 23 | Unencrypted remote shell. Obsolete for security reasons |
| **FTP (RFC 959)** | 20/21 | Original file transfer, with separate control and data connections. Plain text, awkward with NAT and firewalls |
| **FTPS** | 990 or 21 | FTP wrapped in TLS |
| **SMB / CIFS** | 445 | Windows file and printer sharing |
| **NFS** | 2049 | Unix network file system. Uses RPC |
| **WebDAV** | 80/443 | File management built on HTTP methods |
| **RDP** | 3389 | Remote desktop for Windows |

### 6.5 RPC, serialization and API styles

This is where gRPC and Thrift live. The terms get confused, so here is the vocabulary:

- **RPC** (remote procedure call): call a function on another machine as if it were local.
- **Serialization format**: how data is turned into bytes (JSON, Protocol Buffers, Thrift's binary, Avro, MessagePack).
- **IDL** (interface definition language): a schema file from which client and server code is generated.
- **Transport**: how those bytes move (raw TCP, HTTP/2, HTTP/1.1).

| Technology | Serialization | Transport | Notes |
|---|---|---|---|
| **REST** | Usually JSON | HTTP | An architectural style, not a protocol. Resources addressed by URL, using HTTP methods |
| **GraphQL** | JSON | HTTP (usually one `POST` endpoint) | Client asks for exactly the fields it wants |
| **SOAP** | XML | HTTP (and others) | Older, heavyweight enterprise web services |
| **JSON-RPC / XML-RPC** | JSON / XML | HTTP or others | Minimal RPC conventions |
| **gRPC** | Protocol Buffers | HTTP/2 | Google-origin RPC framework. See section 7 |
| **Apache Thrift** | Thrift binary, compact or JSON | Its own transports, usually raw TCP | RPC plus serialization in one framework. See section 7 |
| **Apache Avro / Cap'n Proto / MessagePack** | Schema-based binary formats | Not tied to one | Mostly serialization. Avro is common with Kafka |

### 6.6 Messaging and streaming

| Protocol | Port | What it does |
|---|---|---|
| **MQTT** | 1883, 8883 (TLS) | Lightweight publish/subscribe for IoT and mobile. Tiny headers, small devices, unreliable links |
| **AMQP** | 5672 | Feature-rich message queuing (used by RabbitMQ). Routing, acknowledgements, transactions |
| **Kafka protocol** | 9092 | Kafka's own binary protocol over TCP for producing and consuming log streams |
| **NATS** | 4222 | Simple, fast text-based messaging |
| **STOMP** | 61613 | Simple text messaging protocol, often over WebSocket |
| **CoAP (RFC 7252)** | UDP 5683 | HTTP-like REST for constrained IoT devices, over UDP |

### 6.7 Databases and caches

Each database defines its own application-layer protocol over TCP, usually with optional TLS.

| System | Port | Protocol character |
|---|---|---|
| PostgreSQL | 5432 | Binary messages, startup then query/response |
| MySQL | 3306 | Binary packets, handshake with auth negotiation |
| Redis (RESP) | 6379 | Simple prefix-framed text-like protocol, supports pipelining |
| MongoDB | 27017 | Binary (BSON) wire protocol |
| Memcached | 11211 | Text and binary protocols |

### 6.8 Real-time media and telephony

| Protocol | What it does |
|---|---|
| **RTP / RTCP (RFC 3550)** | Carry audio and video with timestamps and sequence numbers, over UDP. Loss is tolerated rather than retransmitted |
| **SIP** | Sets up, modifies and ends voice and video sessions (VoIP calls). Port 5060 |
| **STUN / TURN / ICE** | Find the route between two peers behind NAT |
| **HLS / DASH** | Adaptive video streaming built on plain HTTP (chunks of video fetched over HTTP) |

### 6.9 Management, monitoring and identity

| Protocol | What it does |
|---|---|
| **SNMP** (UDP 161/162) | Query and manage network devices |
| **NETCONF / RESTCONF / gNMI** | Modern programmatic device configuration |
| **Syslog** (UDP/TCP 514) | Log transport |
| **LDAP** (389/636) | Directory lookups (users, groups) |
| **Kerberos** (88) | Ticket-based authentication in enterprise networks |
| **RADIUS / TACACS+** | Authentication for network access |
| **OAuth 2.0 / OpenID Connect / SAML** | Delegated authorization and single sign-on, usually carried over HTTPS redirects and tokens |

---

## 7. Where HTTP/2, HTTP/3, WebSocket, gRPC and Thrift fit

### 7.1 HTTP/2

```
HTTP semantics (methods, headers, status codes, bodies)
HTTP/2 framing (streams, HPACK)
TLS 1.2+  (browsers require it; ALPN negotiates "h2")
TCP
IP
```

- **Layer:** application layer. Same semantics as HTTP/1.1 (RFC 9110), with a different wire format.
- **What changed (from the HTTP page):** compressed binary headers (HPACK), one connection per domain instead of 2-8, bidirectional **streams** multiplexed inside it, and server push.
- **What it fixed:** HTTP/1.1 could only have one outstanding request per connection, so browsers opened many connections. HTTP/2 puts many requests on one.
- **What it did not fix:** it still runs on **one TCP connection**. If one packet is lost, TCP holds back **all** streams until it is recovered. This is **TCP-level head-of-line blocking**, which motivated HTTP/3.
- **Server push** (the server sends resources before the client asks) was largely abandoned in practice.
- **Adoption (HTTP page):** supported by about 71% of websites.

### 7.2 HTTP/3

```
HTTP semantics
HTTP/3 framing (QPACK header compression)
QUIC  (streams, reliability, congestion control, TLS 1.3 built in)
UDP
IP
```

- **Layer:** application layer on top of a **new transport** (QUIC), which itself runs on UDP. This is why the TCP/IP notes say "HTTP/3 works only over QUIC".
- **Key properties:**
  - Each stream is **independent**. Loss on one stream does not stall the others.
  - The TLS handshake is part of the QUIC handshake, so setup is about **1 RTT** (0 RTT on resumption).
  - Connections are identified by a **connection ID**, not the IP-and-port four-tuple, so they survive a network change (Wi-Fi to cellular).
  - Almost everything is encrypted, which reduces ossification.
- **Discovery:** a client usually starts on TCP and learns about HTTP/3 from an `Alt-Svc` response header or DNS records, then switches. If UDP is blocked, it falls back to HTTP/2 or HTTP/1.1.
- **Adoption (HTTP page):** about 40% of websites, 97% of users have at least partial browser support.
- **Operational note:** many firewalls and load balancers treat UDP differently. An L4 balancer must handle UDP and QUIC connection IDs.

### 7.3 WebSocket

```
Your messages (text or binary frames)
WebSocket framing   (RFC 6455)
TLS (for wss://)
TCP
IP
```

- **Layer:** its own application-layer protocol that **starts life as HTTP**.
- **How it starts:** the client sends an HTTP/1.1 `GET` with `Upgrade: websocket`, `Connection: Upgrade` and a `Sec-WebSocket-Key`. The server answers `101 Switching Protocols`. After that, the same TCP connection is **no longer HTTP**. It carries WebSocket frames.
- **What you get:** a persistent, full-duplex channel where either side can send at any time, with small frame headers (no repeated HTTP headers).
- **Frame types:** text, binary, ping, pong, close. Client-to-server frames are masked.
- **URL schemes:** `ws://` (port 80) and `wss://` (port 443, over TLS).
- **Over HTTP/2:** RFC 8441 defines bootstrapping WebSockets over HTTP/2 (it is in the HTTP page's infobox).
- **Use cases:** chat, live dashboards, collaborative editing, games, trading feeds.
- **Compared with alternatives:**
  - *Polling:* the client keeps asking. Wasteful.
  - *SSE:* server-to-client only, simple, works over plain HTTP.
  - *WebSocket:* two-way, but you manage reconnection, auth and scaling yourself.
- **Load balancer notes:** an L7 balancer must support the upgrade. Connections are long-lived, which skews load and complicates draining during deploys.

### 7.4 gRPC

```
Your service methods (generated stubs)
Protocol Buffers messages
gRPC framing
HTTP/2
TLS
TCP
```

- **Layer:** application layer on top of HTTP/2.
- **Defined by:** a `.proto` file (IDL). Code for clients and servers is generated in many languages.
- **Four call types:** unary, server streaming, client streaming, bidirectional streaming. They map to HTTP/2 streams.
- **Status** is returned in HTTP/2 trailers.
- **Browsers** cannot use full gRPC directly, so gRPC-Web or a proxy is used.
- **Load balancing caution:** many calls share one long-lived HTTP/2 connection, so a layer 4 balancer can pin them all to one backend. Use an HTTP/2-aware (L7) balancer or client-side balancing.

### 7.5 Apache Thrift

```
Your service methods (generated from a .thrift file)
Thrift Processor
Thrift Protocol   (serialization: binary / compact / JSON)
Thrift Transport  (byte movement: socket / buffered / framed / HTTP)
TCP
IP
```

- **What it is:** a cross-language RPC and serialization framework. It was created at Facebook (open-sourced in 2007) and is now an Apache project.
- **How you use it:** write a `.thrift` IDL file with types and services. The compiler generates client and server code for many languages.
- **Own internal layering:**
  - **Processor:** dispatches calls to your handler.
  - **Protocol:** how data is serialized. Options: **TBinaryProtocol** (simple binary), **TCompactProtocol** (smaller, variable-length integers), **TJSONProtocol** (readable).
  - **Transport:** how bytes move: plain TCP socket, buffered, **framed** (length-prefixed, needed by non-blocking servers), or over HTTP.
- **Naming trap:** a "Thrift protocol" is a **serialization** format (presentation-layer-like). It is not a network protocol in the Internet-suite sense. The Thrift "transport" is closer to what networking people mean by moving bytes.
- **Layer:** application layer. By default it runs directly on **TCP**, with no HTTP involved, so a layer 4 balancer works well, but you give up HTTP tooling (no standard headers, caching, or browser access).
- **Thrift vs gRPC:**

| | Thrift | gRPC |
|---|---|---|
| Origin | Facebook | Google |
| Serialization | Thrift binary, compact, JSON | Protocol Buffers |
| Transport | Pluggable, typically raw TCP | HTTP/2 only |
| Streaming | Limited | First-class (4 call types) |
| Ecosystem today | Strong in existing large deployments | Dominant for new cloud-native services |

---

## 8. Quick comparison of the "web-adjacent" options

| Technology | Layer | Runs over | Direction | Typical use |
|---|---|---|---|---|
| HTTP/1.1 | App | TCP (TLS) | Request/response | Basic web and APIs |
| HTTP/2 | App | TCP + TLS | Request/response, multiplexed | Modern web and APIs |
| HTTP/3 | App | QUIC / UDP | Request/response, independent streams | Lossy or mobile networks, low latency |
| WebSocket | App (started from HTTP) | TCP (TLS) | Full duplex | Real-time browser apps |
| SSE | App (on HTTP) | TCP (TLS) | Server to client | Live feeds, notifications |
| gRPC | App | HTTP/2 | Unary and streaming | Microservice RPC |
| Thrift | App | TCP (or HTTP) | RPC | Cross-language RPC, legacy and large-scale systems |
| MQTT | App | TCP (TLS) | Publish/subscribe | IoT |
| WebRTC | App bundle | UDP (DTLS/SRTP/SCTP) | Peer-to-peer | Video calls, P2P data |

---

## 9. What matters most today

Ranked by how often you meet them in current systems:

1. **IP (v4 and v6)**, **TCP**, **UDP**: the base that everything uses.
2. **TLS 1.3**: effectively mandatory. HTTPS is about 90% of web traffic.
3. **HTTP/2 and HTTP/3**: the default for web and API traffic. HTTP/3 and QUIC are growing fast.
4. **DNS** (including DoH/DoT): every connection starts with a lookup, and DNS is a frequent source of outages.
5. **gRPC and REST/JSON**: the dominant ways services talk to each other. Thrift remains in many large existing systems.
6. **WebSocket and SSE**: real-time features in the browser.
7. **BGP**: the routing glue of the internet, with high blast radius when it goes wrong.
8. **Message and streaming protocols** (Kafka, MQTT, AMQP): backbone of event-driven systems and IoT.
9. **OAuth 2.0 / OpenID Connect**: how authentication and authorization work over HTTPS for most apps.
10. **WireGuard, VXLAN, IPsec**: VPNs and overlay networks in cloud and Kubernetes environments.
11. **IPv6**: slow but steady adoption, important as IPv4 addresses run out.

---

## 10. Choosing a protocol (decision guide)

| Question | Answer |
|---|---|
| A browser needs to call my service | HTTPS with REST/JSON, or GraphQL |
| Service-to-service inside my cluster | gRPC (or Thrift if the ecosystem already uses it) |
| Server must push live updates to a browser | SSE if one-way, WebSocket if two-way |
| Real-time voice or video | WebRTC, RTP over UDP |
| Millions of small devices on poor links | MQTT or CoAP |
| Durable event stream between services | Kafka |
| Need reliability with low latency on mobile networks | HTTP/3 (QUIC) |
| Need to load balance blindly with minimal CPU | L4 balancer, accept no HTTP awareness |
| Need routing by URL or header | L7 balancer that terminates TLS |

---

## Related notes

- `Internet_protocol_suite.md` and `OSI_model.md`: the layer models and how protocols are classified.
- `TCP.md`: TCP in depth, including why HTTP/3 and QUIC moved off it.
- `HTTP.md` and `HTTPS.md`: HTTP versions and how TLS wraps them.
- `L4_Load_Balancers.md`: what layer 4 vs layer 7 balancing means for these protocols.
- `Application_Layer_Protocols.md`: the original short note on Postgres, Redis, SSH, SMTP and gRPC.
