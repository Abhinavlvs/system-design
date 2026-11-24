# OSI Model (Open Systems Interconnection)

Source: https://en.wikipedia.org/wiki/OSI_model (revision oldid 1384423801, last edited 8 November 2026, CC BY-SA 4.0). These notes are a section-by-section paraphrase of that page, in page order, with extra weight on the comparison with the TCP/IP model.

---

## Overview

The **OSI model** is a **reference model** published in **1984 by ISO**. Its stated aim is to provide "a common basis for the coordination of standards development for the purpose of systems interconnection".

- It has **seven abstraction layers**: Physical, Data Link, Network, Transport, Session, Presentation, Application.
- It describes communication from **transmitting bits over a medium** up to the **highest-level representation of data** for a distributed application.
- Each layer **serves the layer above** and **is served by the layer below**. Protocols are decomposed into the model's hierarchy of function calls.
- The **Internet protocol suite** (RFC 1122 and RFC 1123) was developed at about the same time. It was funded mainly by the **US Department of Defense**, assumed generic physical links, and focused on software layers with a less rigorous structure.
- OSI is the standard model for **discussing and teaching** networking. It allows **peer-to-peer communication** through the equivalent exchange of PDUs. (The page tags the claim that no other model has been as successful as [citation needed].)

---

## 1. Definitions

*(The page tags this section as needing more citations, November 2019.)*

- Communication protocols let an entity on one host interact with a **peer entity at the same layer** on another host.
- **Service definitions** describe what layer N-1 provides to layer N.
- Layers are numbered from **1** (most basic, usually at the bottom) to **7**.

**PDUs and SDUs.** At each layer N, peers exchange **PDUs (protocol data units)** using a layer N protocol. A PDU has a payload, called the **SDU (service data unit)**, plus headers and/or footers.

**Processing steps:**
1. Data is composed at the top layer of the sender into a PDU.
2. That PDU is passed down to layer N-1, where it becomes an SDU.
3. Layer N-1 adds its own header and/or footer to the SDU, making a layer N-1 PDU, and passes it down.
4. This repeats down to the lowest layer, and the data is transmitted.
5. At the receiver, data climbs the layers as SDUs. Each layer strips its header or footer, until the top layer consumes the data.

### 1.1 Standards documents

The model is defined in **ISO/IEC 7498**, which has four parts:

| Part | Title |
|---|---|
| 7498-1 | The Basic Model |
| 7498-2 | Security Architecture |
| 7498-3 | Naming and Addressing |
| 7498-4 | Management Framework |

ISO/IEC 7498-1 is also published as **ITU-T Recommendation X.200**.

---

## 2. Layer architecture

*(Tagged as needing more citations, December 2025.)*

X.200 describes seven layers numbered 1 to 7, with layer 1 at the bottom. Layers 7 to 4 are called the **host layers** and layers 3 to 1 the **media layers**.

| No. | Layer | PDU | Function (condensed) |
|---|---|---|---|
| 7 | Application | Data | High-level protocols for resource sharing and remote file access (e.g. HTTP) |
| 6 | Presentation | Data | Translation between network service and application: character encoding, compression, encryption/decryption |
| 5 | Session | Data | Managing sessions, meaning continuous multi-exchange communication between two nodes |
| 4 | Transport | Segment | Reliable transmission of segments between points, including segmentation, acknowledgement and multiplexing |
| 3 | Network | Packet, Datagram | Structuring and managing a multi-node network: addressing, routing, traffic control |
| 2 | Data link | Frame | Transmission of frames between two nodes connected by a physical layer |
| 1 | Physical | Bit, Symbol | Transmission and reception of raw bit streams over a physical medium |

**Example protocols per layer** (from the page's navigation box):

| Layer | Examples |
|---|---|
| 7 | NNTP, SIP, SSI, DNS, FTP, Gopher, HTTP (including HTTP/3), NFS, NTP, SMPP, SSH, SMTP, SNMP, Telnet, DHCP, NETCONF |
| 6 | MIME, XDR, ASN.1, ASCII, TLS, PGP |
| 5 | Named pipe, NetBIOS, SAP, PPTP, RTP, SOCKS, X.225 |
| 4 | TCP, UDP, SCTP, DCCP, QUIC, SPX |
| 3 | IP (IPv4, IPv6), ICMP (ICMPv6), IPsec, IGMP, IPX, IS-IS, AppleTalk, X.25 PLP |
| 2 | ATM, ARP, SDLC, HDLC, CSLIP, SLIP, GFP, PLIP, IEEE 802, LLC, MAC, L2TP, Frame Relay, ITU-T G.hn DLL, PPP, X.25 LAPB, Q.922 LAPF |
| 1 | RS-232, RS-449, ITU-T V-Series, I.430, I.431, PDH, SONET/SDH, PON, OTN, DSL, IEEE 802, IEEE 1394, ITU-T G.hn PHY, USB, Bluetooth, X.21 |

### 2.1 Layer 1: Physical layer

- Sends and receives **unstructured raw data** between a device (NIC, Ethernet hub, switch) and a **transmission medium**. It converts bits into **electrical, radio or optical signals**.
- Defines: voltage levels, signal timing, data rates, maximum distance, modulation, channel access, connector pinouts, impedance, cable specifications, and frequency for wireless links.
- Bit rate control is done here. Transmission mode can be **simplex, half duplex or full duplex**. The topology can describe the physical components.
- Standards named: **Bluetooth, Ethernet, USB**, and **CAN** as a less well-known example.
- Encoding example: on copper, a 1 might be a transition from 0 V to 5 V and a 0 a transition from 5 V to 0 V.
- Common problems: incorrect media termination, EMI or noise, misconfigured or faulty NICs and hubs.

### 2.2 Layer 2: Data link layer

- Provides **node-to-node transfer** over a directly connected link. It detects, and may correct, errors from the physical layer. It defines connection establishment and termination between physically connected devices, and **flow control**.
- IEEE 802 splits it into two sublayers:
  - **MAC (Media Access Control):** controls access to the medium and permission to transmit.
  - **LLC (Logical Link Control):** identifies and encapsulates network-layer protocols, and handles error checking and frame synchronisation.
- **IEEE 802.3 Ethernet, 802.11 Wi-Fi** and **802.15.4 Zigbee** operate here.
- **PPP** is a data link protocol that runs over synchronous and asynchronous serial lines.
- **ITU-T G.hn** gives high-speed networking over power lines, phone lines and coax, with error correction and flow control via a selective-repeat sliding window.
- Security: (authenticated) encryption at this layer can use **MACsec**.

### 2.3 Layer 3: Network layer

- Moves **packets from one node to another across different networks**. Each node has an address. The sender supplies the message and the destination address, and the network finds the route, possibly through intermediate nodes.
- If a message is too large for a data link, the network layer may **fragment** it at one node and reassemble it at another. It may report delivery errors but need not.
- Delivery is **not necessarily reliable**. A network-layer protocol may be reliable but need not be.
- **Layer-management protocols** from the ISO 7498/4 management annex belong here: routing protocols, multicast group management, network-layer information and error reporting, and network-layer address assignment. The page says it is the **function of the payload**, not the carrying protocol, that places them in this layer.
- Security: (authenticated) encryption can use **IPsec**.

### 2.4 Layer 4: Transport layer

- Transfers **variable-length data sequences** from a source host to a destination host, application to application, while maintaining quality of service. It can be **connection-oriented** or **connectionless**.
- Large data is split into **segments** because of the network layer's **MTU**.
  - Worked example: Ethernet MTU 1500 bytes, minimum TCP header 20 bytes, minimum IPv4 header 20 bytes. Maximum segment size = 1500 - (20 + 20) = **1460 bytes**.
- Segmentation is optional. Connection-oriented protocols (**TCP, OSI COTP**) segment and reassemble on the receiving side. Connectionless protocols (**UDP, OSI CLTP**) usually do not.
- Controls link reliability through **flow control, error control, and sequence and existence acknowledgements**. State-keeping connection-oriented protocols can **retransmit** failed segments.
- Reliability is not strictly required. **UDP** is used where some loss, reordering, errors or duplication are tolerable: streaming media, real-time multiplayer games, VoIP.

**OSI transport classes.** OSI connection-oriented transport has five classes, from **TP0** (fewest features) to **TP4** (for less reliable networks, similar to the Internet). All classes provide expedited data and record-boundary preservation.

| Feature | TP0 | TP1 | TP2 | TP3 | TP4 |
|---|---|---|---|---|---|
| Connection-oriented network | Yes | Yes | Yes | Yes | Yes |
| Connectionless network | No | No | No | No | Yes |
| Concatenation and separation | No | Yes | Yes | Yes | Yes |
| Segmentation and reassembly | Yes | Yes | Yes | Yes | Yes |
| Error recovery | No | Yes | Yes | Yes | Yes |
| Reinitiate connection (if an excessive number of PDUs are unacknowledged) | No | Yes | No | Yes | No |
| Multiplexing/demultiplexing over a single virtual circuit | No | No | Yes | Yes | Yes |
| Explicit flow control | No | No | Yes | Yes | Yes |
| Retransmission on timeout | No | No | No | No | Yes |
| Reliable transport service | No | Yes | No | Yes | Yes |

- **Class 0** has no error recovery and assumes an error-free network layer.
- **Class 4** is closest to TCP. TCP also includes the **graceful close**, which OSI assigns to the **session layer**.
- Analogy: a post office inspects only the outer envelope.
- **Tunnelling protocols** operate at this layer, for example carrying SNA or IPX over IP. GRE is discussed as a possible transport-like protocol. **L2TP** carries PPP frames inside transport segments. **IPsec** is noted for end-to-end encryption.
- **TCP and UDP** are commonly classed as layer 4 in OSI terms, although they were not developed under the OSI model and do not strictly conform. **TLS** does not strictly fit either, as it has traits of both the transport and presentation layers.

### 2.5 Layer 5: Session layer

- Creates, controls and ends **sessions (connections)** between two or more computers.
- Includes **logon and logoff**, and authentication built into client software (the page's examples are an FTP client and an NFS client).
- Supports full-duplex, half-duplex or simplex operation. (This sentence is tagged [citation needed].)
- Defines **checkpointing, suspend, restart and termination** for related data streams, for example the audio and video in web conferencing.
- Commonly implemented explicitly in environments that use **remote procedure calls**.

### 2.6 Layer 6: Presentation layer

- Formats and translates data into the form the application layer specifies. When sending, data is converted to the application's format. When receiving, the conversion is reversed.
- Handles protocol conversion, **encryption and decryption**, **compression and decompression**, differences in data representation between operating systems, and graphics commands.
- Also called the **"syntax layer"**.
- Negotiates syntax transfer using **ASN.1 Basic Encoding Rules**.
- Examples: EBCDIC-to-ASCII file conversion, and serialisation of objects and data structures to and from XML.

### 2.7 Layer 7: Application layer

- Closest to the end user.
- **Application programs** such as File Explorer and Microsoft Word sit **outside** the OSI model unless they integrate its communication functions. Web browsers and email programs are the page's examples of programs that do integrate them.
- Other examples: Microsoft network file and printer sharing software, and the Unix/Linux NFS client.
- Common functions: file sharing, message handling, database access. Named protocols: **HTTP, FTP, SMB/CIFS, TFTP, SMTP**.
- Identifies communication partners and checks their identity and availability.
- **Application entity vs application.** Example: a reservation website may use HTTP for users and a remote database protocol for records. Neither protocol handles the reservation logic, which lives in the application itself.
- The layer **cannot determine network resource availability**.

---

## 3. Cross-layer functions

Some services are not tied to one layer but affect several. **Management and security affect all layers** (ITU-T X.800). The aim is to improve **confidentiality, integrity and availability (the CIA triad)**. The page says cross-layer functions are the norm in practice, because service availability depends on network design and management protocols together.

Examples:
- **Security services** as defined in **ITU-T X.800**.
- **Management functions** to configure, instantiate, monitor and terminate communications. The application-layer protocol is **CMIP**, with service **CMIS**, which must interact with every layer.
- **MPLS, ATM and X.25** are called **"3a" protocols**. OSI splits the network layer into three sublayers:
  - **3a** Subnetwork Access
  - **3b** Subnetwork Dependent Convergence
  - **3c** Subnetwork Independent Convergence

  They are designed to carry circuit and packet clients and can carry IP, native ATM, SONET and Ethernet frames. The page also mentions a **"Layer 2.5"**.
- **Cross MAC and PHY scheduling** for wireless: transmissions are scheduled when channel conditions are good, using channel state information passed from PHY to MAC, to raise throughput and save energy.

---

## 4. Programming interfaces

- Neither the OSI Reference Model nor the OSI protocol specifications define **programming interfaces**, beyond abstract service descriptions. Software interfaces are implementation-specific.
- Example: **NDIS** and **ODI** are interfaces between the media layer (layer 2) and the network protocol (layer 3).

---

## 5. Comparison to other networking suites

The page has a long table that lists OSI layers, the original OSI protocols and approximate modern equivalents. The mapping is **rough**, because OSI has features not found in the modern IP stack.

> Limitation: the table was flattened in the fetched text, so some protocol entries cannot be assigned to a specific column with certainty. The condensed version below reflects that.

| Layer | OSI protocols | TCP/IP and others |
|---|---|---|
| 7 Application | FTAM, X.400, X.500, DAP, ROSE, RTSE, ACSE, CMIP | HTTP, HTTPS, FTP, SMTP. SS7: INAP, MAP, TCAP, ISUP, TUP. AppleTalk: AFP, ZIP, RTMP, NBP. IPX: SAP. SNA: Transaction/Presentation Services. HTTP-based: WebDAV, SOAP, OpenID, REST, OAuth, GraphQL, ActivityPub, Git, DNS over HTTP. Misc: HL7, Modbus, WebSocket, CoAP |
| 6 Presentation | ISO/IEC 8823, X.226, ISO/IEC 9576-1, X.236 | MIME, SSL/TLS, XDR. AppleTalk: AFP. HTTP-based: XML, JSON, MIME, percent-encoding, base64, gzip, brotli. Misc: TDI, ASCII, EBCDIC, MIDI, MPEG |
| 5 Session | ISO/IEC 8327, X.225, ISO/IEC 9548-1, X.235 | Sockets (session establishment in TCP, RTP, PPTP). AppleTalk: ASP, ADSP, PAP. IPX: NWLink. SNA: Data Flow Control. HTTP-based: HTTP headers incl. cookies, CSRF tokens, WebSocket. Misc: named pipes, NetBIOS, SAP, RPC, SOCKS |
| 4 Transport | ISO/IEC 8073, TP0-TP4 (X.224), ISO/IEC 8602, X.234 | TCP, UDP, SCTP, QUIC, DCCP, uTP. AppleTalk: DDP. IPX: SPX. SNA: Data Flow/Transmission Control. HTTP-based: HTTP/2, HTTP/3, WebSocket, DTLS. Misc: NBF |
| 3 Network | ISO/IEC 8208, X.25 PLP, ISO/IEC 8878, X.223, ISO/IEC 8473-1 (CLNP, X.233), ISO/IEC 10589 (IS-IS) | IP, IPsec, ICMP, IGMP, OSPF, RIP. SS7: SCCP, MTP. AppleTalk: ATP. IPX: IPX. SNA: Path Control. UMTS: RRC/BMC. HTTP-based: out of scope. Misc: NBF, Q.931 |
| 2 Data link | ISO/IEC 7666, X.25 LAPB, Token Bus, X.222, ISO/IEC 8802-2, LLC (IEEE 802.2) | PPP, SLIP, MACsec. SS7: MTP. AppleTalk: LocalTalk, ARA, PPP. IPX: IEEE 802.3 / Ethernet II framing. SNA: Data Link Control. UMTS: PDCP, LLC, MAC. Misc: ARP, NDP, ATM, CDP, DOCSIS, FDDI, Fibre Channel, Frame Relay, HDLC, IEEE 802.3/802.11 MAC, 802.1Q, ISL, G.hn DLL, Linux bonding, Q.921, Token Ring, IS-IS |
| 1 Physical | X.25 (X.21bis), EIA/TIA-232, EIA/TIA-449, EIA-530, G.703 | TCP/IP does not care about the medium as long as it can carry octets. Other: RS-422, PhoneNet, UMTS air interfaces, RJ45, V.35, V.34, I.430/I.431, T1, E1, 10BASE-T/100BASE-TX/1000BASE-T, POTS, SONET/SDH, Bluetooth, DSL, IEEE 802.11 PHY, G.hn PHY, DOCSIS, DWDM, OTN |

### 5.1 Comparison with the TCP/IP model

Points the page makes:

**Design philosophy.**
- TCP/IP protocol design does **not care about strict hierarchical encapsulation or layering**. RFC 3439 has a section titled **"Layering Considered Harmful"**.
- TCP/IP recognises **four broad layers**, based on the operating scope of their protocols:
  1. The scope of the application software.
  2. The host-to-host transport path.
  3. The internetworking range.
  4. The direct links to other nodes on the local network.

**Layer mapping** (based on the original seven-layer ISO 7498 model, not on later refinements of the network layer):

| TCP/IP layer | OSI layer(s) covered |
|---|---|
| Application | OSI application, presentation, and most of the session layer |
| Transport | OSI transport layer, plus the **graceful-close** function of the OSI session layer |
| Internet | A subset of the OSI network layer |
| Link | OSI data link layer, possibly physical-layer-like functions, plus some OSI network-layer protocols |

**Why OSI lost.**
- Many saw the OSI protocol suite as **too complicated, inefficient and largely unimplementable**.
- It proposed replacing all existing networking protocols at every layer, a **"forklift upgrade"**, which vendors with existing investments resisted.
- It had **many optional features**, so implementations were not interoperable.
- OSI is still referenced, but the Internet protocol suite became the networking standard because of its **pragmatic approach** and **simpler, independent implementations**.

**What survived.** Some OSI-stack specifications are still in use. **IS-IS** was specified for OSI as **ISO/IEC 10589:2002** and adapted for TCP/IP as **RFC 1142**.

---

## 6. See also

Government Open Systems Interconnection Profile · Hierarchical internetworking model · History of the Internet · Layer 8 · List of information technology initialisms · Management plane · Recursive Internetwork Architecture · Service layer · Session multiplexing

## 7. References (key items; the page has 51 numbered notes)

| Source | Detail |
|---|---|
| ISO/IEC 7498-1:1994 | Basic Reference Model |
| ITU-T X.200 | Same model as ISO/IEC 7498-1 |
| ITU-T X.224 / ISO/IEC 8073 | Connection-oriented transport protocol |
| ITU-T X.225 | Session protocol specification |
| ITU-T X.800 | Security architecture for OSI |
| ISO/IEC 7498-4:1989 | Management framework |
| IEEE Std 802-2014 | Section 5.2 |
| RFC 3439 | "Layering Considered Harmful", Dec 2002 |
| RFC 1142 | OSI IS-IS intra-domain routing protocol |
| Russell, *OSI: The Internet That Wasn't* | IEEE Spectrum, 30 July 2013 |
| Russell | "Rough Consensus and Running Code and the Internet-OSI Standards War", IEEE Annals, 2006 |
| Campbell-Kelly and Garcia-Swartz | *The History of the Internet: The Missing Narratives*, 2013 |
| Tomsho | *Guide to Networking Essentials*, 7th ed., 2016 |
| Goralski | *The Illustrated Network*, 2009 |
| Tanenbaum | *Computer Networks*, 2003 |
| Crawford | "The actual OSI model", 2021 |
| Donald Davies interview | By James L. Pelkey (Computer History Museum). Davies credits Hubert Zimmermann as the driving force |

## 8. Further reading

- John D. Day, *Patterns in Network Architecture: A Return to Fundamentals* (2008)
- Gary Dickson and Alan Lloyd, *Open Systems Interconnection* (1992)
- David M. Piscitello and A. Lyman Chapin, *Open Systems Networking: TCP/IP and OSI* (1993)
- Marshall T. Rose, *The Open Book: A Practical Perspective on OSI* (1990)
- Andrew L. Russell, *Open Standards and the Digital Age* (2014)
- Hubert Zimmermann, "OSI Reference Model: The ISO Model of Architecture for Open Systems Interconnection", IEEE Transactions on Communications, vol. 28, no. 4, April 1980, pp. 425-432

## 9. External links

- Microsoft Learn: "Windows network architecture and the OSI model"
- ISO/IEC 7498-1:1994 on the ISO Standards Maintenance Portal
- ITU Recommendation X.200 (PDF)
- Cisco Internetworking Technology Handbook (archived)
- ByteXD, "7 Layers of OSI Model Explained" (2021)
- Wikiversity: Network+ Old guides/OSI Model

**Page categories:** OSI model · Computer-related introductions in 1977 · ISO standards · ISO/IEC 7498 · ITU-T recommendations · ITU-T X Series Recommendations · Reference models

---

## Related notes

- `Internet_protocol_suite.md`: the TCP/IP model and its own comparison with OSI (section 8 there).
- `HTTP.md`: HTTP as an application-layer protocol.
- `L4_Load_Balancers.md`: what layer 4 vs layer 7 means in practice.
