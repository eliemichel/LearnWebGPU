Resizing the window
===================

````{tab} With webgpu.hpp
*Resulting code:* [`step085`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step085)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step085-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step085-vanilla)
````

When we introduced the swap chain, **we prevented the window from resizing** by setting the `GLFW_RESIZABLE` window "hint" to false, because the swap chained is tied to a specific size.

Now that our code is better organized, it becomes easy to **get rid of this limitation**: we add a `onResize` handler that we call when the window is resized, and rebuild the swap chain with the new resolution. And we also need to resize the **depth buffer** by the way.

```C++
glfwWindowHint(GLFW_RESIZABLE, GLFW_TRUE);
```

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
Application::onInit() {
	// [...]

	// Add window callbacks
	glfwSetFramebufferSizeCallback(window, Application::onResize);
}
```

**This cannot work** because a non-static class method like `Application::onResize` needs a value of `this` when it is called, so it cannot be used as a function pointer (which `glfwSetFramebufferSizeCallback` expects).

The usual trick here is to define a simple callback function that does nothing but to call the `onResize()` method.

> 🤔 But how do I specify "this"? Should I use a global variable?

It is precisely for this pattern that GLFW provides a **user pointer**, namely an arbitrary value that can be associated to a window. Since the callback receives the window as first argument, we can get the user pointer back and use it:

```C++
// The raw GLFW callback
void onWindowResize(GLFWwindow* window, int width, int height) {
	// We know that even though from GLFW's point of view this is
	// "just a pointer", in our case it is always a pointer to an
	// instance of the class `Application`
	auto that = reinterpret_cast<Application*>(glfwGetWindowUserPointer(window));

	// Call the actual class-member callback
	if (that != nullptr) that->onResize();
}

Application::onInit() {
	// [...]

	// Set the user pointer to be "this"
	glfwSetWindowUserPointer(window, this);
	// Add the raw `onWindowResize` as resize callback
	glfwSetFramebufferSizeCallback(window, onWindowResize);
}
```

Resize event handler
--------------------

We can now focus on the actual content of `onResize()`. Let's extract the steps of `onInit` that creates the swap chain and the depth buffer, so that we can reuse them when resizing:

```C++
private:
	void buildSwapChain();
	void buildDepthBuffer();
```

````{tab} With webgpu.hpp
```C++
void Application::buildSwapChain() {
	int width, height;
	glfwGetFramebufferSize(window, &width, &height);
	// [...]
}

void Application::buildDepthBuffer() {
	// Destroy previously allocated texture
	if (depthTexture != nullptr) depthTexture.destroy();
	// [...]
}
```
````

````{tab} Vanilla webgpu.h
```C++
void Application::buildSwapChain() {
	int width, height;
	glfwGetFramebufferSize(window, &width, &height);
	// [...]
}

void Application::buildDepthBuffer() {
	// Destroy previously allocated texture
	if (depthTexture != nullptr) wgpuTextureDestroy(depthTexture);
	// [...]
}
```
````

The `onResize` function simply consists in calling these, and updating the uniforms:

````{tab} With webgpu.hpp
```C++
void Application::onResize() {
	buildSwapChain();
	buildDepthBuffer();

	float ratio = swapChainDesc.width / (float)swapChainDesc.height;
	uniforms.projectionMatrix = glm::perspective(45 * PI / 180, ratio, 0.01f, 100.0f);
	device.getQueue().writeBuffer(
		uniformBuffer,
		offsetof(MyUniforms, projectionMatrix),
		&uniforms.projectionMatrix,
		sizeof(MyUniforms::projectionMatrix)
	);
}
```
````

````{tab} Vanilla webgpu.h
```C++
void Application::onResize() {
	buildSwapChain();
	buildDepthBuffer();

	float ratio = swapChainDesc.width / (float)swapChainDesc.height;
	uniforms.projectionMatrix = glm::perspective(45 * PI / 180, ratio, 0.01f, 100.0f);
	WGPUQueue queue = wgpuDeviceGetQueue(device);
	wgpuQueueWriteBuffer(
		queue,
		uniformBuffer,
		offsetof(MyUniforms, projectionMatrix),
		&uniforms.projectionMatrix,
		sizeof(MyUniforms::projectionMatrix)
	);
}
```
````

Conclusion
----------

This pattern that we used to connect the raw GLFW resize event to our C++ idiomatic object-oriented application skeleton is **a commonly used pattern**: we will do the same for all the other interaction callbacks we need. We see in the next chapter the case of mouse button and mouse move callbacks to get the **camera controller**!

````{tab} With webgpu.hpp
*Resulting code:* [`step085`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step085)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step085-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step085-vanilla)
````
