Instanced Drawing (<span class="bullet">🔴</span>TODO)
=================

Drawing the **same geometry multiple times** is very common. It happens when **scattering objects** like rocks or trees on a terrain, when drawing **particle systems**, etc.

Turns out that the GPU is particularly good at drawing such repeated geometry thanks to the mechanism of **instancing**.

```{note}
It is much **more efficient** than issuing multiple draw calls, not only because it avoids repeating the **overhead of building a draw command**, but also because it enables the GPU to better **manage memory** by streaming the instances through the rendering pipeline simultaneously.
```

Both the `draw` and `drawIndexed` methods of a render pipeline encoder support instancing (`wgpuRenderPipelineEncoderDraw` and `wgpuRenderPipelineEncoderDrawIndexed`) through their second argument.

```C++
renderPipeline.draw(vertexCount, instanceCount, 0, 0);
```

But as you will quickly notice if changing this instance count argument, all instances get drawn at the **very same position**!

A first solution to distinguish instances is in the shader, using the `@builtin(instance_id)` attribute in the vertex shader inputs.

```rust
TODO
```

A second solution is to use instance-level vertex attributes. TODO
