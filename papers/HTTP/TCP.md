# Transmission Control Protocol (TCP)

Source: https://en.wikipedia.org/wiki/Transmission_Control_Protocol (revision oldid 1386775603, CC BY-SA 4.0). These notes are a section-by-section paraphrase of that page, in page order.

---

## Overview

**TCP** is one of the main protocols of the Internet protocol suite. It gives **reliable, ordered, error-checked delivery of a byte stream** between applications on hosts across an IP network. It complemented IP, so the suite is often called **TCP/IP**.

- Major applications rely on it: web, email, remote administration, file transfer, streaming. **SSL/TLS** often runs on top of it.
- TCP is **connection-oriented** and uses a **three-way handshake**. The server must listen first (**passive open**).
- Retransmission and error detection add reliability but also **add latency**.
- **UDP** is the connectionless alternative for applications that prefer timeliness.
- TCP vulnerabilities named in the lead: denial of service, connection hijacking, TCP veto, reset attack.

**Infobox**

| Item | Value |
|---|---|
| Developers | Vint Cerf and Robert Kahn |
| Introduced | 1974 |
| Based on | Transmission Control Program |
| Layer | Transport (OSI layer 4) |
| IP protocol number | 6 |
| Current specification | RFC 9293 |

---

## Core concepts explained (intuition first)

**The problem TCP solves.** IP only promises "best effort": a packet may be lost, duplicated, reordered or delayed. Applications such as a browser or a database client want something simpler: a pipe where the bytes you write come out the other end, complete and in order. TCP builds that pipe on top of IP.

**Byte stream, not messages.** TCP has no concept of message boundaries. If you `send()` 100 bytes then 200 bytes, the receiver may get them as 300 bytes in one `recv()`, or 50 + 250. Application protocols add their own framing (a length prefix, a delimiter such as `\r\n`, or a fixed header). This is why HTTP has `Content-Length` and chunked encoding.

**Sequence numbers = a position counter.** Every byte in the stream has a number. A segment's sequence number is the position of its first byte. The receiver uses this to put segments in order, spot gaps and discard duplicates.

**ACK = "I have everything up to here".** The acknowledgment number is the next byte the receiver expects. It is cumulative: ACK 2000 means bytes up to 1999 all arrived. It does not say the application has read them.

**Worked example: loss and recovery.** The sender sends segments covering bytes 1000-1999, 2000-2999, 3000-3999, 4000-4999, and the second one is lost.

1. Receiver gets 1000-1999 and replies `ACK 2000`.
2. Receiver gets 3000-3999. It cannot advance past the gap, so it replies `ACK 2000` again (duplicate ACK #1).
3. Receiver gets 4000-4999 and replies `ACK 2000` again (duplicate ACK #2).
4. After three duplicate ACKs the sender assumes 2000-2999 is lost and **resends it right away** (fast retransmit), without waiting for a timer. With SACK, the receiver also says "I already have 3000-4999", so only the missing range is resent.
5. The receiver then has everything and sends `ACK 5000`.

If duplicate ACKs never arrive (for example the last segment is lost), the sender's **retransmission timer** fires instead and it resends. Each time the timer fires, the wait doubles.

**Why the three-way handshake.** Each direction of the stream needs its own starting sequence number that the other side has confirmed. SYN (my starting number is x), SYN-ACK (got x, mine is y), ACK (got y) confirms both. Starting numbers are random so a stranger cannot easily forge segments into your connection.

**Flow control vs congestion control (often confused).**

| | Flow control | Congestion control |
|---|---|---|
| Protects | The **receiver** from being overwhelmed | The **network** from being overwhelmed |
| Signal | Receiver advertises its free buffer in the **window** field | Sender infers from loss and delay |
| Limit on sender | Receive window | Congestion window (cwnd) |

The sender may have at most `min(receive window, congestion window)` unacknowledged bytes in flight.

**Congestion control in four steps.**
1. **Slow start:** begin with a small window and roughly double it each round trip, to find the capacity quickly.
2. **Congestion avoidance:** past a threshold, grow by about one segment per round trip, which is cautious.
3. **On loss:** cut the window (fast retransmit and fast recovery halve it, a timeout resets it much lower).
4. Repeat. The window grows slowly and drops sharply, so throughput rises and falls like a sawtooth.

**Window size and speed.** A connection can only send one window of data per round trip. Throughput is roughly `window / RTT`. With a 64 KB window and a 100 ms RTT, the limit is about 5 Mbit/s however fast the link is. That is why **window scaling** exists for fast, long-distance links.

**Why Nagle's algorithm and `TCP_NODELAY`.** Sending many tiny segments wastes bandwidth (a 1-byte payload carries at least 40 bytes of headers). Nagle's algorithm holds small writes until earlier data is acknowledged so they can be combined. That helps bulk transfers but hurts interactive traffic. Latency-sensitive applications (chat, RPC, game servers) set `TCP_NODELAY` to send immediately.

**Why TIME-WAIT.** The side that closes first lingers so that (a) it can re-send the last ACK if it was lost, and (b) stray old segments from this connection expire and are not mistaken for a new connection on the same four-tuple. On a busy client or proxy, many TIME-WAIT sockets can exhaust ephemeral ports.

**What TCP does not give you.**
- No message boundaries (see above).
- No encryption or authentication (that is TLS).
- No guarantee about time: retransmissions can stall a connection for seconds.
- Head-of-line blocking: one lost segment delays all later bytes on that connection, even if they arrived.

---

## 1. Network function

- TCP provides **host-to-host connectivity at the transport layer**, between applications and IP. Applications do not handle fragmentation or MTU details. TCP presents a **socket** abstraction.
- IP packets may be **lost, duplicated or reordered**. TCP detects this, retransmits, reorders, and helps reduce congestion. If data stays undelivered, the source is notified.
- TCP is tuned for **accuracy over timeliness**. Delays can reach seconds, so the page recommends **RTP over UDP** for real-time traffic such as VoIP.
- It uses **positive acknowledgment with retransmission**: the receiver acknowledges, the sender keeps a timer per packet and retransmits on timeout.
- **Terminology by layer:**

| Term | Layer |
|---|---|
| Segment | TCP |
| Datagram | IP |
| Frame | Link |

A web server splits a file into segments. IP adds the destination address. The receiver reassembles the segments.

---

## 2. TCP segment structure

TCP takes data from a stream, chunks it, adds a header and produces a **segment**, which is encapsulated in an IP datagram.

The header has **10 mandatory fields** plus an optional Options area. **The data length is not in the header.** It equals the IP total length minus the IP header and TCP header lengths.

### Header layout

| Field | Size | Notes |
|---|---|---|
| Source Port | 16 bits | Sending port |
| Destination Port | 16 bits | Receiving port |
| Sequence Number | 32 bits | If SYN set: initial sequence number (ISN). Otherwise the sequence number of the first data byte |
| Acknowledgment Number | 32 bits | Valid when ACK set. The next byte the ACK sender expects. The first ACK acknowledges the peer's ISN, with no data |
| Data Offset | 4 bits | Header length in 32-bit words. 5 (minimum, 20 bytes) to 15 (maximum, 60 bytes), leaving up to 40 bytes for options |
| Reserved | 4 bits | Set to zero for future use |
| Flags | 8 bits | CWR, ECE, URG, ACK, PSH, RST, SYN, FIN (1 bit each) |
| Window | 16 bits | Receive window size in window units |
| Checksum | 16 bits | Covers header, payload and an IP pseudo-header |
| Urgent Pointer | 16 bits | Valid when URG set. Offset from the sequence number to the last urgent byte |
| Options | variable, up to 40 bytes | Present only if Data Offset > 5. Zero-padded to a 32-bit boundary |
| Data | variable | Payload |

**Reserved field notes:**
- Senders set the bits to zero. Receivers ignore them unless specified.
- From 2003 to 2017 the last reserved bit (bit 103) was the **NS (Nonce Sum)** flag under experimental RFC 3540, later moved to Historic status.
- A draft proposes reusing this bit to negotiate **Accurate ECN**.

### Flags

| Flag | tcpdump letter | Meaning |
|---|---|---|
| CWR | W | Sender reduced its congestion window after receiving ECE (RFC 3168) |
| ECE | E | With SYN set: the peer is ECN-capable. With SYN clear: a packet arrived with Congestion Experienced set |
| URG | U | The urgent pointer is significant |
| ACK | . | The acknowledgment field is significant. Every segment after the initial SYN should have it set |
| PSH | P | Push buffered data to the wire and to the receiving application |
| RST | R | Reset the connection |
| SYN | S | Synchronize sequence numbers. Only the first segment from each end |
| FIN | F | Last segment from the sender |

### Checksum

16 bits, covering the header, payload and a **pseudo-header** (source IP, destination IP, protocol 6, TCP length in bytes). See section 14.

### Options

Each option has an **Option-Kind** (1 byte, mandatory) and, for most kinds, an **Option-Length** (1 byte, counting kind and length) and **Option-Data**.
- **Kind 0** ends the list. **Kind 1** is a one-byte no-op used for padding.
- Example: an MSS option is kind 2, length 4, then a 2-byte value.
- Header length rule: (Data Offset - 5) × 4 bytes of options.

| Kind | Length | Data | Purpose | Notes |
|---|---|---|---|---|
| 0 | N/A | N/A | End of options list | One byte |
| 1 | N/A | N/A | No operation | Padding, aligns options to 32 bits |
| 2 | 4 | 2-byte MSS | Maximum segment size | SYN only |
| 3 | 3 | 1-byte shift | Window scale | SYN only. RFC 7323 |
| 4 | 2 | none | SACK permitted | SYN only. RFC 2018 |
| 5 | 10, 18, 26 or 34 | 32-bit begin/end blocks | Selective acknowledgment (SACK) | 1 to 4 blocks |
| 8 | 10 | timestamp, echo | Timestamps | RFC 7323 |
| 28 | 4 | none | User Timeout Option | RFC 5482 |
| 29 | N | none | TCP Authentication Option (TCP-AO) | RFC 5925. Replaces the MD5 option (19) from RFC 2385, used for BGP |
| 30 | N | none | Multipath TCP | See section 7 |

Remaining kinds are historical, obsolete, experimental, unstandardized or unassigned. IANA maintains the assignments.

---

## 3. Protocol operation

TCP has **three phases**: connection establishment (handshake), data transfer, and connection termination (which releases resources).

The OS manages a connection through a **socket**. The local endpoint moves through these states:

| State | Endpoint | Description |
|---|---|---|
| LISTEN | Server | Waiting for any remote connection request |
| SYN-SENT | Client | Sent a connection request, waiting for a matching one |
| SYN-RECEIVED | Server | Has received and sent a request, awaiting the confirming ACK |
| ESTABLISHED | Both | Open. Data can be delivered. The normal data-transfer state |
| FIN-WAIT-1 | Both | Waiting for the peer's termination request, or an ACK of the one sent |
| FIN-WAIT-2 | Both | Waiting for the peer's termination request |
| CLOSE-WAIT | Both | Waiting for a termination request from the local user |
| CLOSING | Both | Waiting for the peer's ACK of the termination |
| LAST-ACK | Both | Waiting for the ACK of the termination request sent to the peer |
| TIME-WAIT | Server or client | Waiting for remaining packets on the connection to expire |
| CLOSED | Both | No connection state |

### 3.1 Connection establishment

The server binds and listens first (**passive open**). The client's **active open** is a three-step handshake:

1. **SYN:** the client sends SYN with a random sequence number **x**.
2. **SYN-ACK:** the server replies with acknowledgment **x+1** and its own random sequence number **y**.
3. **ACK:** the client sends sequence **x+1** and acknowledgment **y+1**.

Steps 1 and 2 establish one direction's sequence number. Steps 2 and 3 establish the other. Afterward both sides have **full-duplex** communication.

### 3.2 Connection termination

- A **four-way handshake**: each side closes its half independently. Each side sends a FIN and gets an ACK, so a typical teardown uses two FIN/ACK pairs.
- The side that sent the first FIN waits a timeout after its final ACK (**TIME-WAIT**), keeping the local port unavailable so it can resend the ACK if it was lost. Common values are 30 seconds, 1 minute or 2 minutes, depending on the implementation. Then it enters CLOSED.
- **Three-way variant:** A sends FIN, B replies with FIN and ACK combined, A replies with ACK.
- **Linux** implements a half-duplex close: if the host closes while unread data remains, it sends **RST** instead of FIN, so the application learns that data was lost.
- A **half-open connection** is one where one side has closed while the other is still open. The closed side can no longer send but should keep reading until the peer closes.

### 3.3 Resource usage

- Most implementations map each session to an OS process via a table. Packets carry **no session ID**, so endpoints identify sessions by address and port.
- Each table entry is a **Transmission Control Block (TCB)**: endpoint info, status, packet bookkeeping, and send/receive buffers.
- Server-side session count is limited only by memory.
- The client must allocate an **ephemeral port** before the first SYN. It stays allocated for the conversation, which limits outgoing connections per IP address. Unclosed connections can exhaust resources across applications.
- Both endpoints allocate space for unacknowledged packets and for received-but-unread data.

### 3.4 Data transfer

Differences from UDP:
- **Ordered** delivery by sequence number.
- **Retransmission** of unacknowledged data.
- **Error-free** delivery: corrupt packets are treated as lost.
- **Flow control.**
- **Congestion control:** loss is presumed to mean congestion, so the rate is reduced.

#### 4.4.1 Reliable transmission

- **Each byte has a sequence number.** The first byte's number is chosen by the transmitter in the SYN and should be unpredictable, to resist sequence-prediction attacks.
- ACKs say data is received up to a certain byte. They do **not** mean the application has read it.
- Loss is detected by **retransmission timeout (RTO)** and by **duplicate cumulative ACKs (DupAcks)**.
- A retransmitted segment keeps its original sequence number, so the sender cannot tell which transmission an ACK covers. This is the **retransmission ambiguity**.

**Duplicate-ACK-based retransmission (4.4.1.1)**
- Example: segment 100 is lost. Because ACKs are cumulative, the receiver repeats its ACK of 99 for each later arrival.
- **Three duplicate ACKs** trigger retransmission of the last unacknowledged segment. The threshold of three avoids spurious retransmits caused by reordering.
- **SACK** gives explicit feedback and improves the choice of what to retransmit.
- Reordering beyond the threshold causes spurious fast retransmits. Linux scales the threshold heuristically.
- **RACK (RFC 8985)** is a time-based loss-detection algorithm. The page says it is the default in Linux and Windows.

**Timeout-based retransmission (4.4.1.2)**
- A timer starts per transmitted segment. On expiry the segment is retransmitted and the timeout **doubles** (exponential backoff).
- Initial timer: smoothed RTT plus the larger of clock granularity G and 4 × RTT variation (RFC 6298).
- **Spurious timeouts** occur when RTT is underestimated. The retransmit triggers slow start, and later ACKs can cause more needless retransmits. SACK helps.
- RFC 6298: implementations must not use retransmitted segments for RTT estimation.
- **Karn's algorithm:** wait for an unambiguous ACK before adjusting the RTO.
- **TCP timestamps** also resolve RTO ambiguity, though they do not necessarily improve RTT estimates.

#### 4.4.2 Error detection

- Sequence numbers let receivers discard duplicates and reorder. ACKs let senders retransmit.
- The **16-bit checksum is weak** by modern standards. It is normally paired with a layer-2 CRC (PPP or Ethernet). It still catches most errors introduced between CRC-protected hops.

#### 4.4.3 Flow control

- End-to-end, so senders do not outrun receivers (for example a PC sending to a slow smartphone).
- **Sliding window:** the receiver advertises its **receive window**, the bytes it will buffer. The sender can send only that much before waiting for ACKs and window updates.
- Sequence numbers and windows behave like a clock and **wrap around**.
- **Zero window:** the sender stops and starts a **persist timer**. On expiry it sends a small probe so the receiver re-advertises the window. This prevents deadlock if a window update is lost.
- **Silly window syndrome:** a receiver consuming data in small increments advertises tiny windows, which is inefficient given the header overhead.

#### 4.4.4 Congestion control

- Aims to avoid **congestive collapse** and to approximate **max-min fairness** between flows.
- Modern TCP uses four intertwined algorithms (RFC 5681): **slow start, congestion avoidance, fast retransmit, fast recovery**.
- Senders also use an RTO based on estimated RTT and its variance (RFC 6298). RTT samples from retransmitted packets need care (Karn's algorithm or timestamps, RFC 7323). Samples are averaged into a **smoothed RTT (SRTT)** using Jacobson's algorithm.
- Many congestion-avoidance variants exist.

### 3.5 Maximum segment size (MSS)

- MSS is the largest amount of data per segment a TCP will receive. It should be small enough to **avoid IP fragmentation**.
- Each side announces its MSS in the MSS option during establishment, derived from the MTU of directly attached links. **Path MTU discovery** can adjust it.
- MSS is **announced, not strictly negotiated**. The two directions can have independent values (RFC 1122, RFC 9293).

### 3.6 Selective acknowledgments (SACK)

- Example: bytes 1,000 to 10,999 are sent in 10 segments, and the segment covering 2,000 to 2,999 is lost. A pure cumulative ACK can only say 2,000, so the sender may resend everything from 2,000.
- **SACK (RFC 2018, 1996)** lets the receiver report non-contiguous received blocks, each with a left edge (first sequence number) and a right edge (one past the last).
  - With a cumulative ACK of 2,000 plus a SACK block of 3,000 to 11,000, the sender resends only 2,000 to 2,999.
- A sender may mistake out-of-order arrival for loss. **D-SACK (RFC 2883, May 2000)** lets the receiver signal a duplicate so the sender restores its rate.
- SACK is optional and negotiated at setup. All popular stacks support it. SCTP also uses selective acknowledgment.
- Receivers may **renege** (discard SACKed data). RFC 2018 discouraged but did not forbid it. Reneging adds complexity and sender memory cost.

### 3.7 Window scaling

- The 16-bit window field caps at **65,535 bytes**. The **window scale option** (RFC 1323) raises the maximum to **1 gigabyte**.
- The scale is a left-shift count from **0 to 14**, set per direction and sent only during the handshake. Both sides must send the option in their SYN.
- Some routers and firewalls rewrite the factor, causing mismatched window sizes and slow traffic.

### 3.8 TCP timestamps

- Defined in RFC 1323 (1992). Used to determine packet order. They are not aligned to system time and start at a random value. Many OSes tick every millisecond, though the RFC only requires proportional ticks.
- Two 4-byte fields: the sender's timestamp and the echoed most recent peer timestamp.
- **PAWS** (Protection Against Wrapped Sequence numbers) uses them when the window crosses sequence wraparound.
- The **Eifel detection algorithm** uses them to tell loss from reordering.
- Enabled by default in Linux, and disabled by default in Windows Server 2008, 2012 and 2016.
- The page says adoption has stagnated near **40%**, citing a 2017 study.

### 3.9 Out-of-band data

- **Urgent data** can interrupt the queued stream and is processed immediately. TCP then informs the application and resumes the queue. Example: a keystroke sequence aborting a remote program.
- The urgent pointer changes only remote-side processing, **not network priority**.
- Support varies and is poorly tested. Assume only single bytes of OOB data are reliable. Associated with vulnerabilities such as **WinNuke**.

### 3.10 Forcing data delivery

- TCP normally waits up to **200 ms** to fill a packet (**Nagle's algorithm**). Page example: a 4 KB block, MSS 1460, 10 Mbit/s Ethernet. Two full packets go out, then a 1176-byte third after a 197 ms pause. Telnet keystroke echo would be annoying.
- Setting the **TCP_NODELAY** socket option overrides the delay.
- RFC 793 defines **PSH** as asking the receiver to deliver data immediately. Berkeley sockets cannot control PSH from user space. Only the stack does.

---

## 4. Vulnerabilities

A 2009 security assessment and IETF work through 2012 covered TCP attacks and mitigations. Notable: DoS, connection hijacking, TCP veto, and the TCP reset attack.

### 4.1 Denial of service

- **SYN flood:** spoofed IPs send many SYNs (then ACKs), so the server holds resources for bogus connections.
- Mitigations: **SYN cookies** (which have their own vulnerabilities) and cryptographic puzzles.
- **Sockstress** is a similar attack and may be mitigated by resource management.
- Persist-timer exploitation was analyzed in Phrack No. 66. PUSH and ACK floods are variants.

### 4.2 Connection hijacking

- An attacker who can eavesdrop and redirect packets learns the sequence number and forges the next segment. One packet may be accepted. Synchronization is lost when the receiver ACKs the forgery.
- Combined with ARP spoofing or routing attacks, permanent control is possible.
- **Before RFC 1948**, guessable initial sequence numbers let attackers impersonate an IP address blind, if the real host was down (for example through DoS). Initial sequence numbers are now random.

### 4.3 TCP veto

- An attacker who can eavesdrop and predict the next packet's size injects a packet with the expected sequence number and payload size. The legitimate packet is then dropped as a duplicate.
- The connection stays synchronized, so the attack is hard to detect. The sender never sees evidence.

---

## 5. TCP ports

- A connection is identified by a **four-tuple**: source address, source port, destination address, destination port. Equivalently it is a pair of sockets.
- Ports are **16-bit**, giving 65,536 values each.
- Connections are bound to one network path. Multihomed hosts cannot use other routes, and connections break if an address changes.

**Three port categories:**

| Category | Range | Use |
|---|---|---|
| Well-known | 0-1023 | IANA-assigned, system services |
| Registered | 1024-49151 | Third-party-assignable, sometimes used for ephemeral ports |
| Dynamic / private | 49152-65535 | Ephemeral client ports |

**Well-known examples:** FTP 20 and 21, SSH 22, Telnet 23, SMTP 25, HTTP 80, HTTPS 443.

With **HTTP/3, QUIC replaces TCP** as the transport.

**NAT** uses dynamic public-side ports to disambiguate flows, letting many private hosts share one public address.

---

## 6. Development

- Basic operation has changed little since RFC 675 (1974) and **RFC 793** (September 1981, version 4).
- **RFC 1122** (October 1989) clarified implementation requirements. **RFC 7414** lists 8 required specifications and over 20 strongly encouraged enhancements.
- **RFC 2581** (TCP Congestion Control) is called one of the most important recent TCP RFCs. **RFC 3168** (2001) defined ECN.
- **Congestion algorithms:** the original was **Tahoe**. Alternatives include **Reno, Vegas, FAST TCP, New Reno and Hybla**.
- **Multipath TCP (MPTCP; RFC 6182 architecture, RFC 6824)** uses multiple paths for redundancy and throughput. Useful for wireless and datacenters. The Linux kernel has the reference implementation. The page says **Apple's Siri** uses it on iPhone, iPad and Mac.
- **tcpcrypt** (proposed July 2010, RFC 8548 published May 2019) encrypts TCP transparently. Unlike TLS, it does not authenticate.
- **TCP Fast Open (RFC 7413, 2014)** skips the handshake on repeat connections using a cryptographic cookie. Earlier **T/TCP** was not widely adopted because of security issues.
- **Proportional Rate Reduction (PRR; RFC 6937)**, proposed in May 2013 by Google engineers, keeps the post-recovery window near the slow-start threshold. It is the default congestion control in Linux 3.2+.

## 7. Hardware implementations

- **TCP offload engines (TOEs)** implement TCP in hardware. They are hard to integrate and require extensive OS changes.
- **TCP low power (TCPlp)** has been shown to work in constrained environments where UDP-based CoAP is usually preferred.

---

## 8. Wire image and ossification

- TCP metadata is in **cleartext**, which gives on-path observers information and modification opportunities. This helps operators and researchers but may reduce end-user privacy.
- This visibility makes TCP **hard to extend**, a problem called **protocol ossification**. Middleboxes act on or change metadata, breaking the end-to-end principle.
- One measurement: a **third of Internet paths** meet an intermediary that modifies TCP metadata, and **6.5%** encounter harmful ossifying effects.
- This constrained MPTCP's design and hindered **TCP Fast Open** deployment in browsers.
- Endpoint changes are hard too, since TCP lives in the kernel or in TOE hardware.

---

## 9. Performance

- **Head-of-line blocking:** reordering or loss delays later data even when it has already arrived. Multiplexing several messages on one connection amplifies this.
- Browsers open **parallel connections** to mitigate it. That costs repeated handshakes and resources, and parallel connections congest independently and can monopolize resources.
- **Connection establishment** is a major latency source. The three-way handshake adds one RTT before data. TLS handshakes run serially after TCP: TLS 1.2 needs two RTTs, TLS 1.3 allows zero-RTT resumption in some cases but TCP still needs one RTT. TCP Fast Open removes one RTT, but as of 2020 no browser used it by default.
- **Reordering** can trigger spurious retransmission and bursty transmission. Blanton and Allman (2002) found throughput inversely related to reordering up to a threshold.
- **SACK:** Bruyeron, Hemon and Zhang (1998) measured gains of up to **45%**, mostly by avoiding slow start.
- The page states TCP can selectively acknowledge **at most three blocks**, limiting recovery in high-loss environments. *This conflicts with the options table, which allows 1 to 4 SACK blocks. The page does not resolve it.*
- **Wireless losses** (fading, handover, interference) are not congestion, yet TCP reduces its window. Solutions are end-to-end, link-layer (such as Radio Link Protocol) or proxy-based. Vegas, Westwood, Veno and Santa Cruz were proposed (citation needed).

---

## 10. Acceleration

*(Not to be confused with TOEs.)*

- A **TCP accelerator** terminates connections in a network processor and relays data over a second connection. It buffers and retransmits locally, which shortens the feedback loop for faster recovery and a shorter RTT.
- **Drawbacks:**
  - Traffic must route through the accelerator, so a routing change breaks the connection.
  - The **end-to-end ACK property is lost**: an ACK means the data is stored at the accelerator, not delivered.

---

## 11. Debugging

- **Packet sniffers** tap a link to see packets.
- The **SO_DEBUG** socket option (set with `setsockopt`) dumps packets, TCP states and events on a socket.
- **netstat** is another tool.

---

## 12. Alternatives

TCP is unsuitable for **real-time media, games and VoIP**, because data after a loss waits for the retransmission.

- **Fibre Channel Protocol:** most SANs use it over Fibre Channel.
- **Simple uses:** embedded systems, network booting and simple request servers such as DNS find TCP complex. NAT traversal via STUN is simpler without TCP.
- **UDP:** the generic alternative. It has multiplexing and checksums but no streams or retransmission, leaving the developer to add them or to use forward error correction or error concealment.
- **SCTP:** reliable, stream-oriented service. More complex, with limited deployment. Designed for reliability with near-real-time needs.
- **Venturi Transport Protocol (VTP):** patented, proprietary, meant to replace TCP transparently for wireless.
- **Timing-based protocols such as ATM** avoid retransmission overhead in predictable environments. TCP congestion avoidance suits ad hoc networks.
- **UDT:** targets high bandwidth-delay-product environments such as large transfers and streaming.
- **Multipurpose Transaction Protocol (MTP/IP):** patented proprietary software for high throughput and transactions where TCP performs poorly.

---

## 13. Checksum computation

### 13.1 TCP checksum for IPv4

- The checksum is the **16-bit ones' complement of the ones' complement sum** of all 16-bit words in the header and text.
- Odd-length data is zero-padded on the right for computation only. The pad is not transmitted. The checksum field is zeroed during computation.

**IPv4 pseudo-header**

| Field | Size |
|---|---|
| Source address | 32 bits |
| Destination address | 32 bits |
| Zeroes | 8 bits |
| Protocol | 8 bits (6 for TCP) |
| TCP length | 16 bits (header plus data, in octets) |

Page example: IPv4 total length 200 bytes and IHL 5 (20 bytes) give a TCP length of 180.

### 13.2 TCP checksum for IPv6

Upper-layer protocols that include IP addresses in their checksum must be modified for 128-bit IPv6 addresses (RFC 8200).

**IPv6 pseudo-header**

| Field | Size |
|---|---|
| Source address | 128 bits |
| Destination address | 128 bits (the IPv6 destination, or the last Routing header address when a Routing header is present) |
| TCP length | 32 bits |
| Zeroes | 24 bits |
| Next header | 8 bits (6 for TCP) |

### 13.3 Checksum offload

- Many stacks offload the checksum to the **network adapter**, on transmit or receive, reducing CPU load.
- Packet analyzers may report valid outbound packets as invalid when captured **before** the adapter computes the checksum. Virtual machines on one host can show the same thing, since virtual drivers may skip the calculation.

---

## 14. See also

Micro-bursting (networking) · TCP global synchronization · TCP fusion · TCP pacing · TCP Stealth · Transport layer comparison of protocols · WTCP (proxy-based wireless TCP modification)

## 15. Notes

1. CWR and ECE were added to the header by RFC 3168.
2. Window size units are bytes by default.
3. Window size is relative to the segment identified by the sequence number in the acknowledgment field.
4. A connection is equivalently a pair of sockets (address plus port each for source and destination).
5. As of the latest standard, HTTP/3 uses QUIC instead of TCP.

## 16. References (key items; the page has about 140)

**RFCs cited:** 675, 760, 791, 793, 1122, 1323, 1948, 2018, 2385, 2581, 2883, 3168, 3522, 3540, 5681, 6013, 6182, 6298, 6824, 6937, 7323, 7413, 7414, 7805, 8200, 8546, 8548, 8558, 8985, 9002, 9065, 9170, 9293.

| RFC | Date | Subject |
|---|---|---|
| 675 | Dec 1974 | Specification of Internet Transmission Control Program |
| 793 | Sept 1981 | Transmission Control Protocol |
| 1122 | Oct 1989 | Requirements for Internet Hosts, communication layers |
| 1323 | May 1992 | TCP Extensions for High Performance |
| 1948 | May 1996 | Defending Against Sequence Number Attacks |
| 2018 | Oct 1996 | TCP Selective Acknowledgment Options |
| 2581 | Apr 1999 | TCP Congestion Control |
| 2883 | Jul 2000 | SACK extension (D-SACK) |
| 3168 | Sept 2001 | ECN added to IP |
| 3522 | Apr 2003 | Eifel Detection Algorithm |
| 3540 | Jun 2003 | Robust ECN signaling with nonces |
| 5681 | Sept 2009 | TCP Congestion Control |
| 6013 | Jan 2011 | TCP Cookie Transactions |
| 6182 | Mar 2011 | Architectural guidelines for Multipath TCP |
| 6298 | Jun 2011 | Computing TCP's Retransmission Timer |
| 6824 | Jan 2013 | TCP Extensions for Multipath Operation |
| 6937 | May 2013 | Proportional Rate Reduction for TCP |
| 7323 | Sept 2014 | TCP Extensions for High Performance |
| 7413 | Dec 2014 | TCP Fast Open |
| 7414 | Feb 2015 | Roadmap for TCP Specification Documents |
| 7805 | Apr 2016 | Moving outdated TCP extensions to Historic |
| 8200 | Jul 2017 | IPv6 Specification |
| 8546 | Apr 2019 | The Wire Image of a Network Protocol |
| 8558 | Apr 2019 | Transport Protocol Path Signals |
| 8985 | Feb 2021 | RACK-TLP loss detection |
| 9002 | May 2021 | QUIC Loss Detection and Congestion Control |
| 9065 | Jul 2021 | Transport header confidentiality |
| 9170 | Dec 2021 | Long-Term Viability of Protocol Extension Mechanisms |
| 9293 | Aug 2022 | Transmission Control Protocol (TCP) |

**Textbooks:** Comer, *Internetworking with TCP/IP*; Kurose and Ross; Tanenbaum, *Computer Networks*; Peterson, *Computer Networks*.

**Papers and articles:** Cerf and Kahn (1974); Mathis et al. (1997); Karn and Partridge (1991); Zhang (1986); Blanton and Allman (2002); Ludwig and Katz (2000); Gurtov and Ludwig (2003); Gurtov and Floyd (2004); Hesmans et al. (2013); Papastergiou et al. (2017); Edeline and Donnet (2019); Hagen and Mullins (2013) on TCP veto; Joncheray (1995); plus LWN and Cloudflare articles.

## 17. Further reading

- Stevens, *TCP/IP Illustrated, Volume 1: The Protocols* (1994)
- Stevens and Wright, *Volume 2: The Implementation* (1994)
- Stevens, *Volume 3: TCP for Transactions, HTTP, NNTP, and the UNIX Domain Protocols* (1996)

## 18. External links

- IANA Port Assignments
- IANA TCP Parameters
- Oral history interview with Robert E. Kahn (University of Minnesota)
- Wikiversity learning resources on TCP

**Page categories:** 1974 introductions · TCP · Transport layer protocols

---

## Conflicts and caveats from the source page

- **SACK block count:** the options table allows 1 to 4 blocks, but the Performance section says "at most three".
- **Options length:** "× 4 bytes" and "× 32 bits" are equivalent.
- **Unverified claims on the page:** Linux and Windows defaults, adoption percentages (such as timestamps near 40%), Siri's use of MPTCP, and the 2009 and 2012 security work.

---

## Related notes

- `Internet_protocol_suite.md`: where TCP sits in the four-layer model.
- `OSI_model.md`: TCP mapped to OSI layer 4, and the TP0-TP4 classes it is closest to (TP4).
- `HTTP.md`: HTTP over TCP, and why HTTP/3 moved to QUIC.
- `L4_Load_Balancers.md`: balancing at the TCP connection level.
- `Application_Layer_Protocols.md`: protocols that run on top of TCP.
