Index Buffer
============

````{tab} With webgpu.hpp
*Resulting code:* [`step034`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step034)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step034-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step034-vanilla)
````

Let's draw a square, which is made of 2 triangles.

```{image} /images/quad-light.svg
:align: center
:class: only-light
```

```{image} /images/quad-dark.svg
:align: center
:class: only-dark
```

TODO A straightforward way:

```C++
std::vector<float> vertexData = {
	// Triangle #0
	-0.5, -0.5, // A
	+0.5, -0.5,
	+0.5, +0.5, // C

	// Triangle #1
	-0.5, -0.5, // A
	+0.5, +0.5, // C
	-0.5, +0.5,
};
```

But as you can see some data is duplicated. And this could be much worst on larger shapes with connected triangles.

So instead we can split the **position** from the **connectivity**:

```C++
// The de-duplicated list of point positions
std::vector<float> vertexData = {
	-0.5, -0.5, // A
	+0.5, -0.5,
	+0.5, +0.5, // C
	-0.5, +0.5,
};

// This is a list of indices referencing positions in the vertexData
std::vector<uint16_t> indexData = {
	0, 1, 2, // Triangle #0
	0, 2, 3  // Triangle #1
};

int indexCount = static_cast<int>(indexData.size());
```

````{note}
I also kept the interleaved color attribute in this example:

```C++
std::vector<float> vertexData = {
	// x,   y,     r,   g,   b
	-0.5, -0.5,   1.0, 0.0, 0.0,
	+0.5, -0.5,   0.0, 1.0, 0.0,
	+0.5, +0.5,   0.0, 0.0, 1.0,
	-0.5, +0.5,   1.0, 1.0, 0.0
};
```

````

```C++
// Create index buffer
bufferDesc.size = indexData.size() * sizeof(uint16_t);
bufferDesc.usage = BufferUsage::CopyDst | BufferUsage::Index;
bufferDesc.mappedAtCreation = false;
Buffer indexBuffer = device.createBuffer(bufferDesc);

// Upload geometry data to the buffer
queue.writeBuffer(indexBuffer, 0, indexData.data(), bufferDesc.size);
```

```C++
// Set both vertex and index buffers
renderPass.setVertexBuffer(0, vertexBuffer, 0, vertexData.size() * sizeof(float));
renderPass.setIndexBuffer(indexBuffer, IndexFormat::Uint16, 0, indexData.size() * sizeof(uint16_t));

// Replace `draw()` with `drawIndexed()` and `vertexCount` with `indexCount`
renderPass.drawIndexed(indexCount, 1, 0, 0, 0);
```

```{figure} /images/deformed-quad.png
:align: center
:class: with-shadow
The square is deformed because its coordinates are expressed relative to the window's dimensions.
```

```rust
// In vs_main():
let ratio = 640.0 / 480.0; // The width and height of the target surface
out.position = vec4<f32>(in.position.x, in.position.y * ratio, 0.0, 1.0);
```

Conclusion
----------

TODO

```{figure} /images/quad.png
:align: center
:class: with-shadow
The expected square
```

````{tab} With webgpu.hpp
*Resulting code:* [`step034`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step034)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step034-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step034-vanilla)
````


