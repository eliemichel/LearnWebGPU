Resizing the window (WIP)
===================

````{tab} With webgpu.hpp
*Resulting code:* [`step085`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step085)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step085-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step085-vanilla)
````

TODO

```C++
class Application {
public:
	// A function called when the window is resized.
	void onResize();
}
```

We also extract the steps of `onInit` that creates the swap chain and the depth buffer, so that we can reuse it.

```C++
private:
	void buildSwapChain();
	void buildDepthBuffer();
```

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

In the end the `onResize` function only consists in calling this and updating the uniforms:

```C++
void Application::onResize() {
	buildSwapChain();
	buildDepthBuffer();

	float ratio = swapChainDesc.width / (float)swapChainDesc.height;
	uniforms.projectionMatrix = glm::perspective(45 * PI / 180, ratio, 0.01f, 100.0f);
	device.getQueue().writeBuffer(uniformBuffer, offsetof(MyUniforms, projectionMatrix), &uniforms.projectionMatrix, sizeof(MyUniforms::projectionMatrix));
}
```

When should this be called?

```C++
// GLFW callbacks
void onWindowResize(GLFWwindow* window, int width, int height) {
	auto pApp = reinterpret_cast<Application*>(glfwGetWindowUserPointer(window));
	if (pApp != nullptr) pApp->onResize();
}

Application::onInit() {
	// [...]

	// Add window callbacks
	glfwSetWindowUserPointer(window, this);
	glfwSetFramebufferSizeCallback(window, onWindowResize);

	// [...]
}
```

Also change `glfwWindowHint(GLFW_RESIZABLE, GLFW_FALSE);` to `GLFW_TRUE`.

We also need to update resize the **depth buffer**.

Conclusion
----------

````{tab} With webgpu.hpp
*Resulting code:* [`step085`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step085)
````

````{tab} Vanilla webgpu.h
*Resulting code:* [`step085-vanilla`](https://github.com/eliemichel/LearnWebGPU-Code/tree/step085-vanilla)
````
