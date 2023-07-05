Dawn vs wgpu-native
===================

Despite the kind of click-bait title, this page does not intend to tell which implementation is better, but rather to list the key divergence that it is important to be aware of while reading the guide because I did not update all examples and chapters to support both backend yet (I'm waiting for the API to settle before taking the time to review all code examples).

Most annoying divergences are:

 - Drop vs Release
 - Drop on finish()
 - Poll vs Tick

Another limiting issue:

 - GLFW did not merge https://github.com/glfw/glfw/pull/2333 yet
 - Dawn uses size_t vs uint32_t everywhere in standard header
