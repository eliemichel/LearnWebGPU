Shadow maps (<span class="bullet">🔴</span>TODO)
===========

Basic shadow mapping:
 1. Render a depth-only view from the point of view of your light
 2. Render your scene from the camera as usual
 3. In the fragment shader of this draw call, compute the vector going from the light to your fragment, and use it for 2 things:
    a. Given its direction, determine which pixel it corresponds to in the depth-only view from step 1, fetch the depth for this pixel
    b. Compare that depth to the length of the fragment-light vector.

If the saved depth is smaller, this means there is an obstacle between your fragment and the light, so the fragment is in a shadow. If the saved depth roughly equals the length, fragment is lit. If it is larger, there's sth wrong (or just aliasing going on)

```{warning}
It is easy to go wrong in **3.a.** with the math, I'd advise to double check. Also for **3.b.** be aware that a depth buffer does not directly store a length, you must linearize its value to be able to compare it with the length of a vector.
```
