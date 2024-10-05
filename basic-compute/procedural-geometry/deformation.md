Deformation (<span class="bullet">🟠</span>WIP)
===========

*Resulting code:* [`step240`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step240)

**Procedural geometry** plays is a very important role in 3D modeling tools. They usually take the form of a **stack of post-effects** and/or **a graph of nodes** where procedural operations are connected to each others. For instance Blender calls these respectively *Modifiers* and *Geometry Nodes*:

```{figure} /images/procgen/geometry-nodes.jpg
:align: center
:class: with-shadow
Modifiers and Geometry Nodes are two examples of procedural (a.k.a. non-destructive) mesh effects in Blender.
```

Motivation
----------

These effects are powerful, but can only be used during the creation of 3D models, **not at runtime** during a game or application. We thus need to program ourselves the procedural effects that we intend to run live.

```{seealso}
The impossibility to exchange procedural effects (also known as "non-destructive effects") is something that I have been trying to address for some time with [OpenMfx](https://openmfx.org/). This "standard" is not really adopted by anybody yet but I still believe we need such an API, and would be happy to discuss about it if you are interested!
```

We could reproduce mesh effects on CPU, but since this guide is about GPU programming, **let's try to write them in shaders**! Not all effects are a good fit for GPU programming, but a lot of them are. Furthermore, some operations are much easier to parallelize on a GPU than others.

The **simplest case** of procedural geometry effect consists in **deforming an existing mesh**, by just moving the existing vertices, not affecting the connectivity.

First of all, if you just need to **move vertices**, you might be able to do it **in the vertex shader**! But there may be multiple reasons for which you should rather use a compute shader:

 - If the deformation process is a **heavy task** that you don't want to run at each frame.
 - If you want to **read the deformed mesh back** to the CPU.
 - If you need to **access connectivity** information such as the neighbors' vertices/faces of a vertex when processing a mesh.
 - If you want to **share information across vertices**.

Example case
------------

Our first example is a "squarification" effect, that takes a quad mesh as input and try to make its faces be as square as possible by iteratively moving vertices.

```{figure} /images/procgen/quad-input.png
:align: center
Our input mesh is made solely of quads, but they are quite distorted.
```

Input file: [`quad-input.obj`](../../data/procgen/quad-input.obj)

TODO

*Resulting code:* [`step240`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step240)


