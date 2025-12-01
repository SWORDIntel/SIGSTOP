# DSLLVM + DSSSL Integration Quick Guide

Use this to build DSLLVM, then compile DSSSL with it, and verify everything works end-to-end.

## 1) Prerequisites
- Ubuntu/Debian: `sudo apt-get update && sudo apt-get install -y build-essential cmake ninja-build python3 git libssl-dev`
- Ensure enough disk/RAM (DSLLVM build is large); use `nproc` cores for speed.

## 2) Build DSLLVM (toolchain)
```bash
cd DSLLVM_full
cmake -G Ninja -S llvm -B build \
  -DCMAKE_BUILD_TYPE=Release \
  -DLLVM_ENABLE_PROJECTS="clang;lld" \
  -DLLVM_ENABLE_DSMIL=ON \
  -DLLVM_TARGETS_TO_BUILD="X86"
ninja -C build
```
Optional install: `sudo ninja -C build install`

## 3) Export toolchain for downstream builds
```bash
export CC=$(pwd)/build/bin/dsmil-clang
export CXX=$(pwd)/build/bin/dsmil-clang++
export LLVM_DIR=$(pwd)/build
```
Add those to your shell profile if you want them persistent.

## 4) Build DSSSL with DSLLVM
```bash
cd ~/Documents/DSSSL
./util/build-dsllvm-world.sh --clean          # portable x86-64-v3
# or optimized/secure profiles:
# ./util/build-dsllvm-dsmil.sh --clean        # Meteor Lake focus
# ./Configure dsllvm-world && make -j$(nproc) # manual path
```
Artifacts land in the local tree (`libssl.so`, `libcrypto.so`, apps/tests built with DSLLVM).

## 5) Test DSSSL
```bash
cd test/dsmil
./run-all-tests.sh                 # quick (3–6 min)
./test-comprehensive.sh --all      # full sweep
./test-security-validation.sh      # security-only
./test-performance-benchmarks.sh   # perf
```

## 6) Use DSSSL in your projects
- CMake: `-DOPENSSL_ROOT_DIR=/path/to/DSSSL -DOPENSSL_USE_STATIC_LIBS=OFF` and keep `CC/CXX` pointing to DSLLVM.
- Make: link against DSSSL libs and include headers from the DSSSL tree.
- Runtime: ensure `LD_LIBRARY_PATH=/path/to/DSSSL` (or install system-wide).

## 7) Profiles and TPM
- Profiles: `WORLD_COMPAT` (default), `DSMIL_SECURE`, `ATOMAL`. Choose per risk/overhead; TPM recommended for DSMIL/ATOMAL.
- TPM 2.0: follow `docs/TPM_INTEGRATION.md` in DSSSL if you need hardware-backed keys.

## 8) Quick sanity checks
- `openssl version` from DSSSL build should report DSMIL branding.
- Run a sample handshake or PQC check from `examples/` after building.

## 9) Where to dive deeper
- DSLLVM build details: `DSLLVM-BUILD-GUIDE.md`
- DSSSL overview: `DSSSL-README.md`
- DSSSL doc map: `DSSSL-DOCUMENTATION_INDEX.md`
- Deployment specifics: `DSSSL-DEPLOYMENT_GUIDE.md`
