## LAPORAN UAS SISTEM TERDISTRIBUSI
## Distributed Log Aggregator Berbasis Publish–Subscribe

Nama: Michael Peter Valentino Situmeang
NIM: 11231039
Mata Kuliah: Sistem Paralel dan Terdistribusi

## 1. Ringkasan Sistem dan Arsitektur
Sistem yang dibangun merupakan Distributed Log Aggregator berbasis arsitektur publish–subscribe yang diimplementasikan menggunakan Docker Compose. Sistem ini terdiri dari beberapa layanan utama, yaitu publisher, aggregator API, worker, message broker, dan database persisten.

Publisher berfungsi sebagai penghasil event log yang mengirimkan event ke sistem melalui endpoint POST /publish. Aggregator bertindak sebagai API utama yang menerima event, melakukan validasi skema, dan meneruskan event ke message broker internal. Broker (Redis) digunakan sebagai media antrean untuk mendukung komunikasi asinkron dan menjamin skema at-least-once delivery.

Worker berjalan secara paralel dan bertanggung jawab memproses event dari broker. Untuk mencegah pemrosesan ganda, setiap event diproses secara idempotent menggunakan deduplication store persisten pada database PostgreSQL. Deduplication dilakukan berdasarkan kombinasi unik (topic, event_id) yang dilindungi oleh constraint unik di tingkat database. Seluruh proses pemrosesan event dan pembaruan statistik dilakukan dalam satu transaksi database.

Database PostgreSQL digunakan sebagai penyimpanan state utama dan dikonfigurasi dengan volume persisten, sehingga data tetap bertahan meskipun container direstart. Sistem menyediakan endpoint observabilitas seperti GET /stats dan GET /events untuk memantau jumlah event unik, duplikasi, dan status sistem. Arsitektur ini dirancang untuk mendukung skalabilitas horizontal, toleransi kegagalan, dan konsistensi eventual.

## 2. Keputusan Desain Sistem
Beberapa keputusan desain utama dalam sistem ini adalah:
1. At-least-once delivery dipilih untuk meningkatkan availability dan throughput.
2. Idempotent consumer diterapkan pada worker untuk menangani duplikasi event.
3. Deduplication store persisten digunakan untuk menjamin konsistensi lintas restart.
4. Transaksi database digunakan untuk mencegah race condition dan lost-update.
5. Ordering best-effort menggunakan timestamp tanpa memaksakan total ordering.
6. Docker Compose digunakan untuk orkestrasi layanan dengan jaringan internal.

Keputusan-keputusan ini dipilih berdasarkan pertimbangan trade-off antara konsistensi, kompleksitas, dan performa.

## 3. Bagian Teori (T1–T10)
# T1 – Karakteristik Sistem Terdistribusi & Trade-off Pub-Sub
Sistem terdistribusi terdiri dari komponen otonom yang berkomunikasi melalui jaringan dan dapat mengalami kegagalan secara independen (Tanenbaum & Van Steen, 2017). Sistem aggregator ini menunjukkan karakteristik concurrency, absence of global clock, dan independent failure. Trade-off utama yang diambil adalah memilih availability dan scalability melalui Pub-Sub dengan konsekuensi penanganan duplikasi secara eksplisit.

# T2 – Publish–Subscribe vs Client–Server
Arsitektur publish–subscribe cocok ketika produsen dan konsumen perlu dipisahkan secara temporal dan struktural (Coulouris et al., 2012). Dalam sistem ini, Pub-Sub memungkinkan publisher mengirim event tanpa menunggu pemrosesan langsung, berbeda dengan client–server yang sinkron dan rentan bottleneck.

# T3 – At-Least-Once Delivery & Idempotent Consumer
At-least-once delivery menjamin pesan dikirim minimal satu kali, namun memungkinkan duplikasi. Sistem ini menghindari exactly-once delivery yang kompleks dengan menerapkan idempotent consumer berbasis deduplication store (Kleppmann, 2017).

# T4 – Skema Topic dan event_id
Setiap event memiliki topic dan event_id unik. Kombinasi ini digunakan sebagai kunci deduplication. Pendekatan ini lebih efisien dibanding membandingkan payload dan mendukung routing serta query berbasis topic.

# T5 – Ordering Praktis
Sistem menggunakan timestamp ISO-8601 sebagai informasi urutan best-effort. Total ordering tidak dipaksakan karena keterbatasan clock terdistribusi dan tidak kritis untuk use-case log aggregator.

# T6 – Failure Modes & Mitigasi
Failure seperti retry, crash worker, dan restart container dimitigasi melalui deduplication persisten, retry publisher, dan volume database. Dengan demikian, sistem tetap konsisten meskipun terjadi kegagalan parsial.

# T7 – Eventual Consistency
Sistem menganut eventual consistency, di mana state akhir akan konsisten setelah semua event diproses. Idempotency memastikan tidak ada efek samping ganda meskipun pemrosesan asinkron.

# T8 – Desain Transaksi & Isolation Level
Transaksi digunakan untuk menjamin atomicity dan consistency saat insert event dan update statistik. Isolation level READ COMMITTED dipilih karena unique constraint sudah cukup untuk mencegah race condition tanpa overhead tinggi (Silberschatz et al., 2020).

# T9 – Kontrol Konkurensi
Kontrol konkurensi dilakukan menggunakan unique constraint dan operasi INSERT ... ON CONFLICT DO NOTHING. Pendekatan ini memanfaatkan mekanisme database sebagai arbiter kebenaran dan menghindari locking manual di aplikasi.

# T10 – Orkestrasi, Keamanan & Observability
Docker Compose digunakan untuk orkestrasi layanan dengan jaringan internal. Data disimpan pada volume persisten dan observability disediakan melalui endpoint statistik dan logging worker (Merkel, 2014).

## 4. Pengujian dan Evaluasi Sistem
Pengujian dilakukan menggunakan pytest dan pytest-asyncio dengan cakupan:
- Deduplication event
- Validasi skema API
- Uji konkurensi multi-worker
- Persistensi data setelah restart container
- Stress test event dalam jumlah besar

Hasil pengujian menunjukkan bahwa sistem mampu memproses event secara konsisten tanpa double-processing, bahkan pada kondisi duplikasi dan konkurensi tinggi.

## 5. Kesimpulan
Sistem Distributed Log Aggregator yang dibangun berhasil mengimplementasikan prinsip sistem terdistribusi secara praktis. Dengan mengombinasikan Pub-Sub, idempotent consumer, transaksi database, dan orkestrasi container, sistem mampu mencapai skalabilitas, toleransi kegagalan, dan konsistensi data. Implementasi ini membuktikan bahwa pendekatan at-least-once delivery dengan deduplication persisten merupakan solusi yang efektif dan realistis.

## Daftar Pustaka (APA 7th)
Coulouris, G., Dollimore, J., Kindberg, T., & Blair, G. (2012). Distributed systems: Concepts and design (5th ed.). Pearson.
Kleppmann, M. (2017). Designing data-intensive applications. O’Reilly Media.
Merkel, D. (2014). Docker: Lightweight Linux containers for consistent development and deployment. Linux Journal, 2014(239).
Silberschatz, A., Korth, H. F., & Sudarshan, S. (2020). Database system concepts (7th ed.). McGraw-Hill.
Tanenbaum, A. S., & Van Steen, M. (2017). Distributed systems: Principles and paradigms (3rd ed.). Pearson.
