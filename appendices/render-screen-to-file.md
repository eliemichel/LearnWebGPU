Render screen to file (WIP)
=====================

Use [save_image.h](../data/save_image.h).

```C++
// for debug
#include "save_image.h"


int frame = 0;
while (!glfwWindowShouldClose(window)) {

	uniforms.time = frame / 25.0f;

	// [...]

	if (0) { // export video
		saveImage(resolvePath(frame), device, nextTexture, 640, 480);
		++frame;
		if (frame >= 100) {
			break;
		}
	}
}
```
