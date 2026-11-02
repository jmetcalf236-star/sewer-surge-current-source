# Debug-only SDK-generated output — NOT FOR SUBMISSION

This directory contains the actual output of the Stake Engine Math SDK `create_books`, `generate_configs`, and local verifier smoke run for 100 books per mode. It is included solely for transparent inspection/reproducibility.

It is NOT an optimized or certified release. The unoptimized RTP / volatility checks failed. Do not upload these books, LUTs, configs or force files to Stake Engine. Regenerate from the pinned Math SDK after Rust/Cargo and the official pinned Python dependencies are installed, then run optimizer and the complete RGS verification workflow.

The compressed `.jsonl.zst` files were created through a temporary adapter backed by the system `zstd` executable because Python `zstandard==0.23.0` was unavailable in this offline environment. They are valid standard Zstandard frames, but regenerate with the SDK-pinned dependency for release.
