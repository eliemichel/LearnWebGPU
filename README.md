<div align="center">
	<picture>
		<source media="(prefers-color-scheme: dark)" srcset="images/webgpu-dark.svg">
		<source media="(prefers-color-scheme: light)" srcset="images/webgpu-dark.svg">
		<img alt="Learn WebGPU Logo" src="images/webgpu-dark.svg" width="150">
	</picture>
</div>

Learn WebGPU
============

This is the source files of the website learnwgpu.com.

Building
--------

Building the website requires Python.

1. It is recommended, but not mandatory, to set up a virtual Python environment:

```
$ virtualenv venv
$ venv/Scripts/activate
```

2. Then install Python packages

```
pip install -r requirements.txt
```

2. And finally build the website by running:

```
make html
```
