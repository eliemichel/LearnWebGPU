Screen capture (<span class="bullet">🟠</span>WIP)
==============

Render screen to file
---------------------

Download [save_image.h](../data/save_image.h) and [stb_image_write.h](../data/stb_image_write.h) next to your `main.cpp`.

```C++
// for debug
#include "save_image.h"


int frame = 0;
while (!glfwWindowShouldClose(window)) {

	uniforms.time = frame / 25.0f;
	queue.writeBuffer(uniformBuffer, offsetof(MyUniforms, time), &uniforms.time, sizeof(MyUniforms::time));

	// [...]

	// export video frame
	saveTextureView(resolvePath(frame), device, nextTexture, 640, 480);
	++frame;
	if (frame >= 100) {
		break;
	}

	wgpuTextureViewDrop(nextTexture);
	m_swapChain.present();
}
```

After introducing the `Application` class:

```C++
// for debug
#include "save_image.h"


void Application::onFrame() {
	static int frame = 0;

	// [...]

	m_uniforms.time = frame / 25.0f;
	queue.writeBuffer(m_uniformBuffer, offsetof(MyUniforms, time), &m_uniforms.time, sizeof(MyUniforms::time));

	// Optional: mock mouse clicks to rotate the view point
	double xpos = m_swapChainDesc.width / 2 + 50 * cos(PI / 2 * m_uniforms.time);
	double ypos = m_swapChainDesc.height / 2 + 50 * sin(PI / 2 * m_uniforms.time);
	glfwSetCursorPos(m_window, xpos, ypos);
	if (frame == 0) {
		onMouseButton(GLFW_MOUSE_BUTTON_LEFT, GLFW_PRESS, 0);
	}

	// [...]

	// export video frame
	saveTextureView(resolvePath(frame), m_device, nextTexture, m_swapChainDesc.width, m_swapChainDesc.height);
	++frame;
	if (frame >= 100) {
		onFinish();
		exit(0);
	}

	wgpuTextureViewDrop(nextTexture);
	m_swapChain.present();
}
```

