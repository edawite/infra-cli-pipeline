# Infra CLI Pipeline

**Infra CLI Pipeline** is a production‑ready command line application
for high‑throughput batch processing of documents.  It was designed as
a learning project to demonstrate real infrastructure skills: robust
orchestration, concurrency, idempotency, observability and clean
engineering practices.  Given an input directory of PDF or text files
the pipeline discovers documents, parses their contents, classifies
them using a pluggable interface and writes the results to a JSON
Lines file.  The codebase is modular, heavily documented and
configuration‑driven so that it can be extended or swapped into
larger systems.

## Key Features

* **Parallelism** – A `ProcessPoolExecutor` is used to fan out CPU
  bound tasks such as parsing and classification.  Bounded queues
  provide backpressure so the producer cannot overwhelm downstream
  stages.
* **Idempotency** – Documents are hashed using SHA‑256 and recorded
  in a checkpoint file.  Re‑running the pipeline will skip any file
  whose hash already appears in the checkpoint.
* **Rate limiting** – A token‑bucket limiter regulates how many
  documents per second enter the pipeline.  This prevents
  uncontrolled bursts against external services such as LLM APIs.
* **Retries with backoff** – Transient parsing or classification
  errors trigger exponential backoff with jitter.  The maximum
  number of retries is configurable.
* **Metrics** – Prometheus counters, gauges and histograms track
  total files processed, queue depth and per‑stage latencies.  A
  built‑in HTTP server exposes a `/metrics` endpoint for scraping.
* **Structured logging** – Logs are emitted as JSON with timestamps,
  levels, file identifiers and stage information.  Logs are written
  both to stdout and to a rotating file.
* **Config driven** – All tunables (directories, queue sizes,
  worker counts, rate limits, backoff settings, metrics port, log
  levels) live in YAML under `config/default.yaml`.  Command line
  flags can override any field.
* **LLM ready** – Classification is defined via a protocol.  The
  default implementation is a dummy classifier based on document
  length, but the interface can be swapped with a call to a large
  language model or other service.

## Architecture

The pipeline consists of four stages wired together by queues and
executors.  Each stage is responsible for a single concern and
exposes a simple API.  A high‑level overview is shown below:

```
           ┌─────────────┐
           │ Discover    │
           │ (generator) │
           └───────┬─────┘
                   │ file paths
                   ▼
           ┌─────────────┐
           │   Parse     │
           │ (pool of    │
           │  processes) │
           └───────┬─────┘
                   │ text
                   ▼
           ┌─────────────┐
           │  Classify   │
           │ (pool of    │
           │  processes) │
           └───────┬─────┘
                   │ label + meta
                   ▼
           ┌─────────────┐
           │   Write     │
           │ (synchronous│
           │  writer)    │
           └─────────────┘
```

* **Discover** walks the input directory recursively, skipping
  hidden files/directories and emitting only supported suffixes.
* **Parse** reads the file contents.  Plain text files are read
  directly; PDFs are parsed via `pdfminer.six` when installed.
* **Classify** runs a `Classifier` implementation over the text and
  returns a dictionary containing at least a label.  Users can
  implement their own classifier by subclassing `Classifier` or
  fulfilling the protocol.
* **Write** appends classification results to a JSONL file.  A
  thread lock ensures that concurrent processes do not interleave
  writes.  Each record contains the file path, hash and result.

## Quick Start

1. **Install dependencies**

   ```sh
   git clone https://github.com/edawite/infra-cli-pipeline.git
   cd infra-cli-pipeline
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Generate some demo data**

   Use the provided script to create 100 random text files in the
   `./data` directory:

   ```sh
   python scripts/generate_demo_data.py generate --output-dir ./data --n-files 100
   ```

3. **Run the pipeline**

   ```sh
   infra-cli run --input ./data --output ./results/output.jsonl --workers 8 --config config/default.yaml
   ```

   While the pipeline is running you can query metrics via HTTP:

   ```sh
   curl localhost:8000/metrics | grep files_processed_total
   ```

4. **Benchmark throughput**

   To measure approximate throughput on your machine run:

   ```sh
   infra-cli bench --n 500
   ```

## Example Metrics

The Prometheus histogram below illustrates stage latencies from an
example run on a four‑core laptop processing 200 text files.  Your
numbers will vary; see `infra-cli bench` to produce your own.

| Metric                     | p50 (ms) | p95 (ms) |
|---------------------------:|---------:|---------:|
| `processing_seconds{stage="discover"}` |    1.5  |    3.2  |
| `processing_seconds{stage="parse"}`     |   15.0  |   35.0  |
| `processing_seconds{stage="classify"}` |    5.0  |   12.0  |
| `processing_seconds{stage="write"}`    |    0.4  |    1.0  |

These metrics can be scraped by a Prometheus server and visualised
with Grafana.  See the optional `docker/compose.yaml` for a turnkey
setup.

## Troubleshooting

* **Empty output file** – Ensure that the input directory actually
  contains supported documents (``.pdf`` or ``.txt``).  Hidden files
  are ignored.
* **Permission errors** – The writer stage creates the results
  directory on demand.  When running inside Docker mount volumes
  read/write or adjust file permissions accordingly.
* **Long path names on Windows** – Windows has a 260 character path
  limit by default.  Enable long path support or keep your project
  closer to the drive root.
* **Stalled pipeline** – Check the rate limiter configuration.  If
  the rate is too low relative to your hardware you may see idle
  workers waiting for tokens.

## Security

This project contains no secrets or credentials and makes no
outbound network requests by default.  When integrating with LLM
providers or other services ensure that you manage API keys securely
via environment variables or your cloud provider's secret manager.

## License

This project is licensed under the terms of the MIT License; see
the [LICENSE](LICENSE) file for details.