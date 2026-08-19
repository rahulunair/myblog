# Xe2 GEMM post evidence plan

This underscore-prefixed file is an authoring ledger and is not reader-facing.

| Section | Claim | Artifact | Reading after artifact | Status |
|---|---|---|---|---|
| Geometry | heads and TP become N/K while workload becomes M | xkcd shape diagram | identical math creates different operating regimes | planned |
| Baseline | the B70 crosses from bandwidth to compute bound as M rises | roofline plus p50/p90/p99 | the knee determines where large tiles start paying | needs fresh run |
| Ownership | tiles create reuse by changing output ownership | ownership diagram and code slice | reuse consumes accumulator registers | planned |
| XMX | Triton dot is intent and DPAS in vISA is delivery | lowering pipeline and vISA slice | arithmetic can be right while loads remain wrong | historical artifact exists |
| Memory path | descriptors change generated loads | pointer/descriptor distributions and instruction counts | block2D helps but the SLM route and spill leave a gap | needs current compiler rerun |
| Registers | tile size exchanges occupancy for working set | GRF diagram and tile ablation | no universal winner exists across M | needs run |
| Scheduling | persistence needs enough residents | program-count distributions | scheduling cannot repair a weak tile | historical run exists |
| Dispatch | winners change with M and TP | final all-kernel shape sweep | a small dispatch table beats a universal kernel | needs run |
| Production gap | SYCL-TLA retains mechanisms Triton is missing | normalized feature and timing table | the remaining gap has named mechanisms | needs matched run |

Canonical charts use the cream background and xkcd line style from the Qwen3.8
post. Every performance chart shows p50, p90, and p99 or the underlying
distribution, the sample count, and the complete hardware/software identity.

Palette: cream #fffdf7, ink #243447, green #06d6a0, yellow #ffd166,
purple #8e6cff, coral #ef476f, and blue #118ab2. Labels carry the meaning; color
groups concepts locally and never acts as the only semantic channel.

## Editorial contract

- Primary archetype: performance deep-dive
- Absorbed archetype: developer tutorial
- Audience: peer-engineer-deep
- Depth: a short opening, R3-R5 internals with a plain-language reading after
  every intervention, and a short close
- Traversal: a first-principles staircase braided with a
  hypothesis-measurement spiral
- Length: no word-count target; every paragraph must either build the model,
  present evidence, or help the reader interpret it
- Code repository: private during investigation

The opening starts with a small PyTorch reference and derives the concrete
Qwen3-Coder-Next projection it represents. It explains why changing only `M`
turns the same GEMM into different kernel problems. The reader encounters the
hardware and compiler questions in the same order as the investigation.

The teaching pattern is concrete-first, one abstraction at a time:

1. show the actual tensor operation;
2. explain every dimension in ordinary language;
3. build a tiny worked version;
4. map the tiny version back to the real model;
5. introduce one new mechanism, artifact, or equation;
6. ask what physically happens to the tensor next.

This is concreteness fading applied to systems work. It does not remove
technical detail. It changes the order in which the detail arrives. We are
learning through the investigation, so uncertainty, wrong turns, and source or
measurement corrections stay in the narrative when they teach something.

## Section notes

- **B70 constraints:** Introduce only the hardware facts that predict this
  workload: 32 Xe-cores, eight XMX engines per core, 24 MiB L2, the 128/256 GRF
  switch, rated clock, measured bandwidth, theoretical BF16 peak, and measured
  oneDNN peak. Separate source/spec, measured, and derived values. Select one
  card with `ZE_AFFINITY_MASK=0`.
- **Definition of fast:** Define FLOPs, logical bytes, arithmetic intensity,
  measured bandwidth, measured oneDNN roof, p50/p90/p99, fixed sample count,
  cache policy, and correctness. Count one fused multiply-add as two FLOPs. Do
  not use MFU for a single kernel; report percentage of the measured
  oneDNN/SYCL-TLA roof.
- **Evidence collection:** Name the pinned SGLang-XPU container and Bash
  entrypoint, one-card affinity, fixed-count XPU events, Torch profiler, oneDNN
  verbose, unitrace, Triton dumps, IGC dumps, vISA, and `zeinfo`. State what each
  tool can and cannot prove.
- **Readable kernel:** Start with Torch, then one output per Triton program.
  Explain ownership and duplicate input traffic. Keep the code excerpt to its
  load-bearing lines.
- **Tiling:** Derive reuse and accumulator cost for a `BLOCK_M × BLOCK_N` owner.
  Follow timings with a figure of output ownership and fragment lifetime.
- **XMX proof:** Trace Triton source through TTIR, TTGIR, LLVM, and vISA. Identify
  DPAS, explain repeat count and the BF16 8×16×16 atom, and show a minimal
  assembly slice.
- **Memory path:** Run a controlled pointer-versus-descriptor experiment.
  Inspect block2D instructions, the A-operand SLM round trip, GRF count, and
  spills on the current Triton-XPU compiler.
- **Registers:** Explain the 128/256 GRF choice, threads per XVE, subgroup limit,
  accumulator footprint, and spills. Sweep tile, warps, and stages and show
  distributions, not only the winning median.
- **Scheduling:** Measure grouped-M and persistent scheduling. Preserve negative
  results, including too few persistent programs leaving the B70 idle.
- **Dispatch:** Compare every candidate for `M=1,8,32,128,512,4096,16384` at TP1
  and TP2, plus one restrained Llama-shaped contrast. The hero chart includes
  oneDNN and SYCL-TLA.
- **Production comparison:** Use SYCL-TLA as the production comparator. Compare
  2D loads, prefetch, fragment layouts, GRF, DPAS, scheduling, and epilogue.
- **Close:** Show the final shape predicates, correctness boundary, and
  compile-variant cost. End on the next unresolved measured gap.
