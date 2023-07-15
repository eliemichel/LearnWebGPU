"""
This script tries to convert a file based on the C++ wrapper into one based on
vanilla WebGPU. Don't try using it on fancy C++ things though, this is a quick
and dirty search and replace to ease my life but not a bulletproof tool (and
good luck properly parsing C++ if that's what you want...)
"""

import argparse
from dataclasses import dataclass, field
import re
from difflib import SequenceMatcher
import os

#-------------------------------

# Arguments
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('filenames', type=str, nargs='*', default=["main.cpp"])
parser.add_argument('-u', '--webgpu', type=str, default="build-wgpu/_deps/webgpu-backend-wgpu-src/include/webgpu/webgpu.h")
parser.add_argument('-d', '--dry-run', action='store_true')

#-------------------------------

@dataclass
class Pattern:
    """
    A pattern to recognize and replace a wgpu function call in the C++ file
    """
    returned_type: str = ""
    function_name: str = ""
    method_name: str = ""
    first_argument: str = ""

@dataclass
class EnumPattern:
    """
    A pattern to recognize and replace an enum value in the C++ file
    """
    enum_name: str = ""

@dataclass
class TypePattern:
    """
    A pattern to recognize and replace a type name in the C++ file
    """
    type_name: str = ""

@dataclass
class Registry:
    """
    Registry extracted from webgpu.h header, to define what must be searched
    and replaced.
    """
    patterns: list[Pattern] = field(default_factory=list)
    enum_patterns: list[EnumPattern] = field(default_factory=list)
    type_patterns: list[TypePattern] = field(default_factory=list)

#-------------------------------

def main(args):
    registry = parse_webgpu_header(args)
    for filename in args.filenames:
        process_file(registry, filename)

#-------------------------------

def parse_webgpu_header(args):
    registry = Registry()
    with open(args.webgpu, "r", encoding="utf-8") as f:
        it = iter(f)
        while (line := next(it, None)) is not None:
            # Function calls
            if line.startswith('WGPU_EXPORT') and line.rstrip().endswith('WGPU_FUNCTION_ATTRIBUTE;'):
                signature = line.rstrip()[11:-24].strip()
                m = re.match("^(.*) wgpu[A-Z]", signature)
                assert(m is not None)
                pattern = Pattern()
                end_return = m.span()[1] - 6
                pattern.returned_type = signature[:end_return]
                end_function_name = signature.find("(", end_return)
                pattern.function_name = signature[end_return+1:end_function_name]
                if pattern.function_name == "wgpuCreateInstance":
                    continue
                end_first_argument = signature.find(",", end_function_name)
                pattern.first_argument = signature[end_function_name+1:end_first_argument]
                pattern.handle_type = pattern.first_argument.split()[0][4:]
                end_function_prefix = len(pattern.handle_type) + 4
                pattern.method_name = pattern.function_name[end_function_prefix].lower() + pattern.function_name[end_function_prefix+1:]
                registry.patterns.append(pattern)

            # Enums
            if line.startswith('typedef enum WGPU'):
                enum_name = line.strip()[17:-2]
                entries = []
                while (line := next(it, None)) is not None:
                    if line.rstrip().endswith('WGPU_ENUM_ATTRIBUTE;'):
                        break
                    entries.append(line)
                registry.enum_patterns.append(EnumPattern(enum_name))
                registry.type_patterns.append(TypePattern(enum_name))

            # Type (handle)
            if line.rstrip().endswith('WGPU_OBJECT_ATTRIBUTE;'):
                type_name = line.split()[-2][4:]
                registry.type_patterns.append(TypePattern(type_name))

            # Type (descriptor)
            if line.startswith('typedef struct WGPU'):
                type_name = line.strip()[19:-2]
                registry.type_patterns.append(TypePattern(type_name))
    return registry

#-------------------------------

def process_file(registry, filename):
    with (
        open(filename, "r", encoding="utf-8") as f,
        open(filename + ".tmp", "w", encoding="utf-8") as out,
    ):
        for line in f:
            # Search & Replace function call
            best_match_score = 0.0
            best_match_replace = None
            for p in registry.patterns:
                m = re.search(r"(\S+)\." + p.method_name + r"\(", line)
                if m is None:
                    continue
                begin, end = m.span()
                comma = "" if line[end] == ")" else ", "
                instance_name = m.group(1)
                # Guess instance type
                score = similar(p.handle_type, instance_name)
                if best_match_replace is None or score > best_match_score:
                    best_match_score = score
                    best_match_replace = line[:begin] + p.function_name + "(" + instance_name + comma + line[end:]
            if best_match_replace is not None:
                line = best_match_replace

            # Search & Replace enum
            for p in registry.enum_patterns:
                m = re.search(p.enum_name + "::", line)
                if m is None:
                    continue
                begin, end = m.span()
                line = line[:begin] + "WGPU" + p.enum_name + "_" + line[end:]

            # Search & Replace types
            for p in registry.type_patterns:
                m = re.search(r"\s" + p.type_name + r"\s", line)
                if m is None:
                    continue
                begin, end = m.span()
                line = line[:begin+1] + "WGPU" + p.type_name + line[end-1:]
            
            out.write(line)
    
    if not args.dry_run:
        os.replace(filename + ".tmp", filename)
    print("Ok")

#-------------------------------
# Utils

def similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

#-------------------------------

if __name__ == "__main__":
    main(parser.parse_args())
