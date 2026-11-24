# Internet Protocol Suite (TCP/IP)

Source: https://en.wikipedia.org/wiki/Internet_protocol_suite (revision oldid 1386775607, last edited 20 November 2026, CC BY-SA 4.0). These notes are a section-by-section paraphrase of that page, in page order.

---

## Overview

The **internet protocol suite**, commonly known as **TCP/IP**, is a framework that organizes the communication protocols used on the Internet and similar networks according to the functional criteria each protocol serves. The foundational protocols of the suite are:

- **TCP**: Transmission Control Protocol
- **UDP**: User Datagram Protocol
- **IP**: Internet Protocol

Early versions of the suite were called the **DoD Internet Architecture Model**. The research behind it was funded by **DARPA**, the US Defense Advanced Research Projects Agency.

The suite provides **end-to-end data communication**. That covers every step of moving data between hosts:

1. Packetizing the data.
2. Addressing it.
3. Transmitting it.
4. Routing it.
5. Receiving it at the destination.

### The four abstraction layers

Following RFC 1122 and RFC 1123, functionality is split into four abstraction layers. Each layer classifies protocols by the scope of the networking it covers. From lowest to highest:

| Layer | Scope |
|---|---|
| Link layer | Communication within a single network segment (the link) |
| Internet layer | Internetworking between independent networks |
| Transport layer | Host-to-host communication |
| Application layer | Process-to-process communication |

A **protocol stack** is the software implementation of these layers.

### Standards and relation to OSI

The **IETF** (Internet Engineering Task Force) maintains the standards. The suite **predates the OSI model**, which is a broader reference framework for general networking systems.

---

## Core concepts explained (intuition first)

**Why layers at all.** Sending data between two programs on different continents involves wires, radio, addressing, routing, loss recovery and application formats. Splitting it into layers lets each layer solve one problem and hide it from the one above. A web browser does not need to know whether it is on Wi-Fi or Ethernet. Wi-Fi hardware does not need to know about HTTP.

**Each layer has a different "scope".**

| Layer | Question it answers | Scope | Address it uses |
|---|---|---|---|
| Application | What do the two programs say to each other? | Process to process | Name / URL, resolved to an IP |
| Transport | Which program on that host, and how reliably? | Host to host (end to end) | **Port** number |
| Internet | Which machine, and how do I get there across networks? | Network to network | **IP address** |
| Link | How do I reach the next device on this wire or Wi-Fi? | One hop | **MAC address** |

**Encapsulation, step by step.** Sending `GET /` to a web server:

1. The browser produces the HTTP text (the **application data**).
2. **Transport** adds a TCP header (source port 51234, destination port 80, sequence number...). The result is a **segment**.
3. **Internet** adds an IP header (your IP, the server's IP, TTL...). The result is a **packet** (datagram).
4. **Link** adds an Ethernet or Wi-Fi header and trailer (your MAC, the next hop's MAC). The result is a **frame** put on the wire.

At every router, the link-layer frame is **removed and rebuilt** for the next hop, while the IP packet and TCP segment inside travel unchanged (apart from the TTL decreasing). The receiver strips the headers in reverse order, and the HTTP text reaches the server program.

**Two kinds of address, two jobs.** An IP address says which network and host you mean and stays the same end to end. A MAC address only matters on the local link and changes at every hop. **ARP** (IPv4) or **NDP** (IPv6) is the local lookup that turns "next hop is 10.0.0.1" into "send the frame to MAC aa:bb:cc...".

**Routers only look as high as the internet layer.** They read the IP header to forward packets. They normally ignore ports and payloads. Firewalls, NAT and load balancers look further up, and that is where "layer 4" and "layer 7" devices come from.

**End-to-end principle.** Keep the network simple (move packets, nothing more) and put the smart parts, such as reliability, ordering and security, at the two ends. IP stays "best effort", and TCP at the endpoints rebuilds reliability. The benefit is that new applications need no changes inside the network. The cost is that things which break the principle (NAT, firewalls, caches, middleboxes) make it hard to change protocols later.

**Robustness principle.** "Be conservative in what you send, liberal in what you accept." Send well-formed data, but tolerate sloppy input from other implementations, so that differing software still interoperates.

**Why IP is the narrow waist.** Everything above (TCP, UDP, QUIC, HTTP, DNS...) assumes IP, and everything below (Ethernet, Wi-Fi, 5G, fibre...) provides IP. Because that middle is one thin protocol, new applications and new link technologies can both appear without needing to change each other.

**Where the layer models disagree.** TCP/IP has four layers and no separate session or presentation layer. OSI has seven. In practice, encryption (TLS) and session handling live inside the application or in libraries, and the IETF does not treat strict layering as a goal. Use the models as a vocabulary, not as a rulebook.

---

## 1. Key architectural principles

**End-to-end principle.**
- Its interpretation has changed over time.
- **Firewalls, NAT and caches** forced changes, because the network now intervenes in traffic that the original design left untouched.

**Robustness principle** (from RFC 791):
- Be **conservative in what you send** and **liberal in what you accept**.
- RFC 1122 adds a warning against exploiting obscure legal features of a protocol.

**Encapsulation.**
- Data from each layer is wrapped by the layer below. Encapsulation aligns with the layers.
- The page shows figures of host-to-host data flow through routers and of RFC 1122 encapsulation.

**RFC 1122 and RFC 1123** ("Requirements for Internet Hosts") stress principles over rigid layering. Their four layers are:

- **Application layer.** Protocols such as SMTP, FTP, SSH and HTTP. Ports represent services.
- **Transport layer.** UDP (unreliable and connectionless) and TCP (flow control, connection setup, reliable delivery).
- **Internet layer.** IP addressing and routing. IP routers forward datagrams toward the destination.
- **Link layer.** The local network link, and the interfaces to neighbor hosts.

---

## 2. Link layer

- Scope: the **local link**, meaning hosts reachable without crossing a router.
- It is **hardware-independent** and includes virtual links such as **VPNs and tunnels**.
- Framing and transmission are handled by **device drivers, firmware or chipsets**.
- It maps IP addresses to **MAC addresses**.
- It corresponds to **OSI Layer 2** (data link).

---

## 3. Internet layer

- Provides **routing** across networks using **hierarchical IP addressing**.
- Delivers **unreliable datagrams** between networks.
- **Protocol numbers** in the IP header identify the upper-layer protocol. Examples: **ICMP = 1**, **IGMP = 2**.
- **IPv4** uses 32-bit addresses, which allows about **four billion** hosts.
- **IPv6** was standardized in **1998**, uses **128-bit addresses**, and reached production use around **2006**.

---

## 4. Transport layer

The transport layer provides **end-to-end message transfer**, independent of the network below. It can be **connection-oriented** (TCP) or **connectionless** (UDP). Its functions include error control, segmentation, flow control, congestion control and port numbers.

**Ports** are logical channels. Many services use standard port numbers.

### TCP guarantees
- Data is delivered **in order**.
- Errors are kept to a minimum.
- **Duplicate** data is discarded.
- **Lost packets** are resent.
- It includes **congestion control**.

### SCTP
- Reliable, connection-oriented and **message-stream oriented**.
- Supports **multiple streams** and **multihoming**.
- Designed for **SS7 over IP**.
- The page also notes that IP can be made reliable over HDLC.

### UDP
- Uses a **checksum** for error detection, with no retransmission.
- Suited to **streaming, VoIP and DNS**.
- **RTP** runs on top of UDP.

### QUIC
- Runs over UDP.
- **HTTP/3 works only over QUIC.**

Well-known ports are a matter of convention. The transport layer corresponds to **OSI Layer 4**.

---

## 5. Application layer

- Defines protocols for **user services and data exchange**, including routing and host configuration.
- Examples: **HTTP, FTP, SMTP, DHCP**.
- The model has **no separate presentation or session layers**. Those functions are provided by libraries and APIs.
- **IANA** assigns well-known ports (for example HTTP 80 and Telnet 23). Clients use **ephemeral** ports.
- RFC 1122 section 1.1.3 distinguishes **user protocols** (like FTP) from **support protocols** (like DNS).
- Routers generally **do not inspect payloads**. Some firewalls and traffic shapers do, using **deep packet inspection** (RSVP is the page's example). Applications affected by NAT may also need their payloads examined.

---

## 6. Layering evolution and representations in the literature

The page has a table comparing how different sources draw the layers. Layer counts range from three to seven:

| Model | Layers |
|---|---|
| ARPANET Reference Model (RFC 871) | 3 |
| Internet Standard (RFC 1122) | 4 |
| Internet model (Cisco Academy) | 4 |
| TCP/IP 5-layer model (Kozierok; Comer) | 4 + 1 |
| TCP/IP 5-layer model (Tanenbaum) | 5 |
| TCP/IP protocol suite / five-layer internet model (Forouzan; Kurose) | 5 |
| TCP/IP model (Stallings) | 5 |
| OSI model (ISO/IEC 7498-1:1994) | 7 |

> Limitation: only the column headings and layer counts were recoverable from the page text. The per-row layer names in the original table are not reproduced here.

**Important caveat:** textbook models may **conflict with RFC 1122 and other IETF primary sources** (see RFC 3439).

---

## 7. Comparison of TCP/IP and OSI layering

- TCP/IP has **one application layer** above the transport layer. OSI splits that space into application, presentation and session layers. X.400 also combined them.
- Example: **NFS** runs over **XDR**, which runs over **RPC**. RPC provides reliable record transfer over UDP, so a single application stack spans what OSI would call several layers.
- There is disagreement about whether TCP/IP includes **OSI Layer 1 (physical)**. Several authors fold OSI layers 1 and 2 into one TCP/IP layer.
- The IETF is **not concerned with strict layering**. RFC 3439 has a section titled **"Layering Considered Harmful"**.
- Session functions appear inside HTTP, SMTP, Telnet and SIP. Presentation functions are done with **MIME**.
- **Routing protocols** are hard to place:
  - **IS-IS** is a network-layer protocol with its own encapsulation.
  - **OSPF, RIP and BGP** run over IP, so they are classed as **application-layer** protocols. Tanenbaum places them with IP.
- **GRE** allows **recursive encapsulation** (a layer carried inside the same layer).

---

## 8. Implementations

- TCP/IP is **independent of hardware and software** and has been implemented on essentially every platform.
- A **minimal TCP/IP implementation** includes: IP, ARP, ICMP, TCP, UDP and IGMP.
- **IPv6** adds NDP, ICMPv6 and MLD, and is often paired with IPsec.
- The page carries a "needs more citations" banner dated March 2014 for this section.

---

## 9. See also

BBN Report 1822 · Fast Local Internet Protocol · Internetwork Packet Exchange (IPX) · List of automation protocols · List of IT initialisms · List of IP protocol numbers · List of TCP and UDP port numbers · Lists of network protocols · Timeline of the history of the Internet

## 10. Notes

1. Donald Davies had the same idea earlier and was the first to implement packet switching (the NPL network).
2. Records of the TCP/IP split are in the IEN index.

## 11. References (key items)

**RFCs and standards**

| Document | Details |
|---|---|
| RFC 1122 | Braden, Oct 1989, STD 3. Updated by RFC 1349, 4379, 5884, 6093, 6298, 6633, 6864, 8029, 9293 |
| RFC 1123 | Braden, Oct 1989, STD 3. Updated by RFC 1349, 2181, 5321, 5966, 7766 |
| RFC 675 | Cerf, Dalal, Sunshine, Dec 1974. Obsolete (obsoleted by RFC 7805) |
| RFC 791 | Postel, Sept 1981, STD 5. Obsoletes RFC 760. Updated by RFC 1349, 2474, 6864 |
| RFC 1812 | Baker, June 1995, Proposed Standard. Obsoletes RFC 1716 and 1009 |
| RFC 1958 | Carpenter, June 1996, Informational. Updated by RFC 3439 |
| RFC 3439 | Bush and Meyer, Dec 2002, Informational |
| RFC 6214 | Carpenter and Hinden, 1 April 2011. An April Fools' RFC |
| RFC 1000 | Reynolds and Postel, Nov 1987 |
| RFC 1180 | Socolofsky and Kale, Jan 1991, "A TCP/IP Tutorial" |
| ISO/IEC 7498-1:1994 | OSI Basic Reference Model |
| IEN 2, IEN 5, IEN 151 | Postel (1977) and Cerf (1977, 1980) |

**Papers and books:** Cerf and Kahn (1974); Clark (1988); Russell (2013 IEEE Spectrum, 2007 thesis); Blumenthal and Clark (2001); Morabito and Jimenez (2020); Abbate (1999), *Inventing the Internet*; Hafner and Lyon (1998); Isaacson (2014); textbooks by Hunt, Comer, Tanenbaum, Forouzan and Fegan, Kurose and Ross, Stallings, Kozierok, Stevens.

## 12. Bibliography

Abbate (1999) *Inventing the Internet* · Comer (2001) *Internetworking with TCP/IP* · Davies and Lee (2003) *Microsoft Windows Server 2003 TCP/IP Protocols and Services* · Forouzan (2003) *TCP/IP Protocol Suite* · Hunt (1998) *TCP/IP Network Administration* · Maufer (1999) *IP Fundamentals* · McLean (2000) *Windows 2000 TCP/IP Black Book* · Mungale (2004) *Pro .NET 1.1 Network Programming* · Stevens (1994, 1996) *TCP/IP Illustrated* Vols 1-3 · Tanenbaum (2003) *Computer Networks*

## 13. External links

- Wikiversity resource page
- livinginternet.com Internet history
- RFC 1180 "A TCP/IP Tutorial"
- The Ultimate Guide to TCP/IP (itprc.com) and The TCP/IP Guide (tcpipguide.com)
- "A Study of the ARPANET TCP/IP Digest" (archived)

**Page categories:** Internet protocols · History of the Internet · Network architecture · Reference models
