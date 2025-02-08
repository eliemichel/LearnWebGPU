Resizing the window <span class="bullet">🟡</span>
===================

````{tab} With webgpu.hpp
*Resulting code:* [`step085`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step085)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step085-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step085-vanilla)
````

When we introduced the swap chain, **we prevented the window from resizing** by setting the `GLFW_RESIZABLE` window "hint" to false, because the swap chained is tied to a specific size.

Now that our code is better organized, it becomes easy to **get rid of this limitation**: in this chapter, we restore the possibility to resize the window:

```C++
glfwWindowHint(GLFW_RESIZABLE, GLFW_TRUE);
```

To do so, we add a `onResize` handler that we call when the window is resized, and **rebuild the swap chain** with the new resolution. And we also need to resize the **depth buffer** by the way.

Callback setup
--------------

Let us first add the `onResize()` method:

```C++
class Application {
public:
	// A function called when the window is resized.
	void onResize();
}
```

GLFW provides a mechanism for setting a callback to be invoked each time the window size changes: [`glfwSetFramebufferSizeCallback`](https://www.glfw.org/docs/3.0/group__window.html#ga3203461a5303bf289f2e05f854b2f7cf). Naively, we could consider the following:

```C++
// DON'T (this will not work)
bool Application::initWindowAndDevice() {
	// [...]

	// Add window callbacks
	glfwSetFramebufferSizeCallback(m_window, Application::onResize);

	return /* [...] */;
}
```

**This cannot work** because a non-static class method like `Application::onResize` needs a value of `this` when it is called, so it cannot be used as a function pointer (which `glfwSetFramebufferSizeCallback` expects).

The usual trick here is to define a simple callback function that does nothing but to call the `onResize()` method.

> 🤔 But how do I specify "this"? Should I use a global variable?

It is precisely for this pattern that GLFW provides a **user pointer**, namely an arbitrary value that can be associated to a window. Since the callback receives the window as first argument, we can get the user pointer back and use it:

```C++
// The raw GLFW callback, that must always have the same signature
// even though we do not use the 'width' and 'height' arguments here.
void onWindowResize(GLFWwindow* window, int /* width */, int /* height */) {
	// We know that even though from GLFW's point of view this is
	// "just a pointer", in our case it is always a pointer to an
	// instance of the class `Application`
	auto that = reinterpret_cast<Application*>(glfwGetWindowUserPointer(window));

	// Call the actual class-member callback
	if (that != nullptr) that->onResize();
}

bool Application::initWindowAndDevice() {
	// [...]

	// Set the user pointer to be "this"
	glfwSetWindowUserPointer(m_window, this);
	// Add the raw `onWindowResize` as resize callback
	glfwSetFramebufferSizeCallback(m_window, onWindowResize);

	return /* [...] */;
}
```

If we want to make this more compact and avoid creating a dedicated function, we can use a **lambda** when calling `glfwSetFramebufferSizeCallback`:

```C++
bool Application::initWindowAndDevice() {
	// [...]

	// Set the user pointer to be "this"
	glfwSetWindowUserPointer(m_window, this);
	// Use a non-capturing lambda as resize callback
	glfwSetFramebufferSizeCallback(m_window, [](GLFWwindow* window, int, int){
		auto that = reinterpret_cast<Application*>(glfwGetWindowUserPointer(window));
		if (that != nullptr) that->onResize();
	});

	return /* [...] */;
}
```

```{important}
I did not show the lambda version right away because it is slightly misleading: **it is tempting** to use the **capturing context** of the lambda (the `[]` before the lambda's arguments) to provide `this` to the callback.

However, **only non-capturing lambdas** may be cast to the raw function pointer that GLFW expects for a callback. In fact, this is true for any C API.
```

Resize event handler
--------------------

### Swap Chain and Depth Buffer

With our new design, the content of `onResize()` is pretty simple:

```C++
void Application::onResize() {
	// Terminate in reverse order
	terminateDepthBuffer();
	terminateSwapChain();

	// Re-init
	initSwapChain();
	initDepthBuffer();
}
```

```{note}
On this simple example, **managing the lifetime** of WebGPU objects (e.g., destroying before rebuild them, releasing at the end of the application, etc.) can be done manually. But since this is in general quite **error-prone**, the [RAII](../../advanced-techniques/raii) chapter presents a common C++ **design pattern** that makes this easier.
```

However, we need to **update** `initSwapChain()` and `initDepthBuffer()` to take into account **the actual size of the window**, rather than the hardcoded $(640,480)$.

```C++
bool Application::initSwapChain() {
	// Get the current size of the window's framebuffer:
	int width, height;
	glfwGetFramebufferSize(m_window, &width, &height);

	// [...]
	swapChainDesc.width = static_cast<uint32_t>(width);
	swapChainDesc.height = static_cast<uint32_t>(height);
	// [...]
}

bool Application::initDepthBuffer() {
	// Get the current size of the window's framebuffer:
	int width, height;
	glfwGetFramebufferSize(m_window, &width, &height);

	// [...]
	depthTextureDesc.size = { static_cast<uint32_t>(width), static_cast<uint32_t>(height), 1 };
	// [...]
}
```

### Camera Projection

If you look for "640" in your code to ensure nothing relies any more on the original window size, you'll find that **we use the size when defining the camera projection**. Thus the `onResize` function must also update the projection matrix uniform:

```C++
void Application::onResize() {
	// [...] Rebuild swap chain and depth buffer
	updateProjectionMatrix();
}
```

Where `updateProjectionMatrix` is a new private method:

````{tab} With webgpu.hpp
```C++
void Application::updateProjectionMatrix() {
	int width, height;
	glfwGetFramebufferSize(m_window, &width, &height);
	float ratio = width / (float)height;
	m_uniforms.projectionMatrix = glm::perspective(45 * PI / 180, ratio, 0.01f, 100.0f);
	m_queue.writeBuffer(
		m_uniformBuffer,
		offsetof(MyUniforms, projectionMatrix),
		&m_uniforms.projectionMatrix,
		sizeof(MyUniforms::projectionMatrix)
	);
}
```
````

````{tab} Vanilla webgpu.h
```C++
void Application::updateProjectionMatrix() {
	int width, height;
	glfwGetFramebufferSize(m_window, &width, &height);
	float ratio = width / (float)height;
	m_uniforms.projectionMatrix = glm::perspective(45 * PI / 180, ratio, 0.01f, 100.0f);
	wgpuQueueWriteBuffer(
		m_queue,
		m_uniformBuffer,
		offsetof(MyUniforms, projectionMatrix),
		&m_uniforms.projectionMatrix,
		sizeof(MyUniforms::projectionMatrix)
	);
}
```
````

```{note}
If your screen is larger than the 2048 limit we set for texture dimensions, you need to use [`glfwGetMonitors`](https://www.glfw.org/docs/3.3/group__monitor.html#ga70b1156d5d24e9928f145d6c864369d2) and then [`glfwGetMonitorWorkarea`](https://www.glfw.org/docs/3.3/group__monitor.html#ga7387a3bdb64bfe8ebf2b9e54f5b6c9d0) when initializing WebGPU limits to set them to at least the size of your biggest monitor!
```

Conclusion
----------

This pattern that we used to connect the raw GLFW resize event to our C++ idiomatic object-oriented application skeleton is **a commonly used pattern**: we will do the same for all the other interaction callbacks we need. We see in the next chapter the case of mouse button and mouse move callbacks to get the **camera controller**!

````{tab} With webgpu.hpp
*Resulting code:* [`step085`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step085)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step085-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step085-vanilla)
````
