Our first shader <span class="bullet">🟠</span>
================

```{lit-setup}
:tangle-root: 019 - Our first shader - Next
:parent: 017 - Playing with buffers - Next
```

*Resulting code:* [`step019-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step019-next)

We have introduced how to **allocate GPU memory** in chapter [*Playing with buffers*](playing-with-buffers.md), and we now see how to **run a custom program on the GPU**.

GPU Pipelines
-------------

There are **similarities and differences** between the way programs run on a CPU and on a GPU.

Like a CPU, **a GPU can be programmed**. The program is written in a human language, then compiled into a binary representation. Traditionally, a GPU program is called a **shader program**.

The **programming languages** used to program a GPU **are different** from the ones used to program a CPU. This is because the **computing models** are quite different, and in particular **a GPU cannot allocate/free memory for itself**. We can cite for instance GPU languages like GLSL, HLSL, MSL, Slang, etc. and the one we'll be using: WGSL ("SL" stands for *Shader Language*).

GPU programs are **fundamentally parallel**, following a _**Single Instruction/Multiple Data**_ model: the **execution pointer** (address of the currently executed instruction) **is shared** among neighbor threads, only they fetch and process slightly different data. This enables the hardware to **mutualize some operations** like memory access, which is key to data-intensive applications.

Besides programmable stages, a GPU also features **fixed-function** stages. It typically contains hardware circuits **dedicated to some performance critical operations**. A canonical example of such stage is the **rasterization**, which projects 3D triangles onto the pixels of a texture. Fixed-function stages can be **configured** through some options, but are not programmable.

What we call a **pipeline** is a series of fixed-function with a specific configuration and programmable stages with a given shader.

**WIP**

Conclusion
----------

*Resulting code:* [`step019-next`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step019-next)
