#!/usr/bin/env python3

"""
Utility Script with GUI to convert non-standard SEGY files to standard format by converting them to blocks of numpy arrays and saving to individual `.npy` files.
"""

import os
import sys
import timeit
import argparse
import numpy as np
import struct
import json
import tkinter as tk
from tkinter import filedialog, messagebox

K = 12
MIN_VAL = 0
MAX_VAL = 1

def read_textual_header(file):
    file.seek(0)
    textual_header = file.read(3200)  # Textual header is 3200 bytes
    try:
        textual_header_decoded = textual_header.decode('cp500')
    except UnicodeDecodeError:
        try:
            textual_header_decoded = textual_header.decode('ascii')
        except UnicodeDecodeError:
            print("Error: Unknown encoding of textual header.")
            sys.exit(1)
    return textual_header_decoded

def read_binary_header(file):
    file.seek(3200)
    binary_header = file.read(400)  # Binary header is 400 bytes

    # According to the SEGY standard, binary header fields are 2 bytes each (short integers)
    # Byte positions are counted from 1 in the SEGY standard, so we adjust for zero-based indexing

    # Sample interval in microseconds (bytes 17-18)
    sample_interval = struct.unpack('>H', binary_header[16:18])[0]

    # Number of samples per data trace (bytes 21-22)
    num_samples = struct.unpack('>H', binary_header[20:22])[0]

    # Data sample format code (bytes 25-26)
    data_sample_format = struct.unpack('>H', binary_header[24:26])[0]

    return sample_interval, num_samples, data_sample_format

def get_file_info(file):
    file.seek(3200)
    binary_header = file.read(400)
    sample_interval, num_samples, data_sample_format = read_binary_header(file)
    
    # Get file size and calculate expected traces
    file_size = os.path.getsize(file.name)
    trace_size = 240 + (num_samples * 4)  # header + data
    expected_traces = (file_size - 3600) // trace_size
    
    return num_samples, data_sample_format, expected_traces, trace_size
def validate_segy_structure(file):
    """Validate SEGY file structure and return key parameters"""
    file.seek(0)
    file_size = os.path.getsize(file.name)
    
    # Read headers
    textual_header = file.read(3200)
    binary_header = file.read(400)
    
    # Get sample format and count
    sample_interval, num_samples, data_sample_format = read_binary_header(file)
    
    # Calculate trace size
    sample_size = 4  # We'll convert everything to 4-byte IEEE float
    trace_data_size = num_samples * sample_size
    trace_size = 240 + trace_data_size
    
    # Validate file size
    remaining_size = file_size - 3600  # After headers
    if remaining_size % trace_size != 0:
        raise ValueError(f"File size {file_size} is not consistent with trace size {trace_size}")
        
    expected_traces = remaining_size // trace_size
    return num_samples, data_sample_format, expected_traces, trace_size
def get_segy_revision(binary_header):
    """Detect SEGY revision type from binary header"""
    # Rev type is at byte 3500-3502 (300-302 in binary header)
    rev_num = struct.unpack('>H', binary_header[300:302])[0]
    if rev_num == 0:
        return "SEG-Y Rev 0"
    elif rev_num == 1:
        return "SEG-Y Rev 1"
    elif rev_num == 2:
        return "SEG-Y Rev 2"
    else:
        return f"Unknown SEG-Y Revision (code: {rev_num})"
    
def get_binary_header_details(binary_header):
    """Extract all relevant binary header values"""
    return {
        'job_id': struct.unpack('>l', binary_header[0:4])[0],
        'line_num': struct.unpack('>l', binary_header[4:8])[0],
        'reel_num': struct.unpack('>l', binary_header[8:12])[0],
        'traces_per_ensemble': struct.unpack('>h', binary_header[12:14])[0],
        'aux_traces_per_ensemble': struct.unpack('>h', binary_header[14:16])[0],
        'sample_interval': struct.unpack('>h', binary_header[16:18])[0],
        'original_sample_interval': struct.unpack('>h', binary_header[18:20])[0],
        'num_samples': struct.unpack('>h', binary_header[20:22])[0],
        'original_num_samples': struct.unpack('>h', binary_header[22:24])[0],
        'format_code': struct.unpack('>h', binary_header[24:26])[0]
    }
def update_to_rev2(binary_header, trace_count, samples_per_trace):
    """Update binary header to SEG-Y Rev 2 standard"""
    header = bytearray(binary_header)
    
    # Set revision number to 2
    header[300:302] = struct.pack('>H', 2)
    
    # Set fixed length trace flag
    header[302:304] = struct.pack('>H', 1)
    
    # Set extended header count
    header[304:306] = struct.pack('>H', 0)
    
    # Update mandatory Rev 2 fields
    header[16:18] = struct.pack('>H', 2000)  # Sample interval (2ms)
    header[24:26] = struct.pack('>H', 5)     # IEEE float format
    header[20:22] = struct.pack('>H', samples_per_trace)
    
    # Set measurement system to meters
    header[24:25] = struct.pack('B', 1)
    
    # Set major SEG-Y format version (2)
    header[300:302] = struct.pack('>H', 2)
    
    # Set minor SEG-Y format version (0)
    header[302:304] = struct.pack('>H', 0)
    
    # Set fixed length trace flag
    header[304:306] = struct.pack('>H', 1)
    
    # Set total trace count
    header[3212:3216] = struct.pack('>L', trace_count)
    
    return header
    
def validate_and_fix_segy(input_file, output_file):
    """Complete SEGY validation and conversion with strict checking"""
    with open(input_file, 'rb') as infile:
        # Get file size and validate
        file_size = os.path.getsize(input_file)
        if file_size < 3600:
            raise ValueError("Invalid SEGY file: too small")

        # Read and validate headers
        textual_header = infile.read(3200)
        binary_header = bytearray(infile.read(400))
        
        # Get format details with validation
        sample_interval, num_samples, data_format = read_binary_header(infile)
        if num_samples <= 0:
            raise ValueError("Invalid number of samples")
            
        # Calculate standard sizes
        standard_trace_size = 240 + (num_samples * 4)
        expected_traces = (file_size - 3600) // standard_trace_size
        
        # Pre-scan file to validate actual structure
        traces = []
        pos = 3600
        actual_traces = 0
        
        while pos < file_size:
            if pos + 240 > file_size:
                break
                
            infile.seek(pos)
            trace_header = infile.read(240)
            
            # Validate trace header
            if len(trace_header) != 240:
                break
                
            trace_samples = struct.unpack('>H', trace_header[114:116])[0]
            if trace_samples == 0:
                trace_samples = num_samples
                
            trace_size = 240 + (trace_samples * 4)
            if pos + trace_size > file_size:
                break
                
            traces.append({
                'pos': pos,
                'size': trace_size,
                'samples': trace_samples
            })
            
            pos += trace_size
            actual_traces += 1
            
        print(f"\nFile Analysis:")
        print(f"- File size: {file_size} bytes")
        print(f"- Standard trace size: {standard_trace_size} bytes")
        print(f"- Expected traces: {expected_traces}")
        print(f"- Actual traces found: {actual_traces}")
        
        # Write standardized file
        with open(output_file, 'wb') as outfile:
            # Update binary header
            binary_header[300:302] = struct.pack('>H', 2)  # Rev 2
            binary_header[20:22] = struct.pack('>H', num_samples)
            binary_header[24:26] = struct.pack('>H', 5)  # IEEE float
            binary_header[3212:3216] = struct.pack('>L', actual_traces)
            
            # Write headers
            outfile.write(textual_header)
            outfile.write(binary_header)
            
            # Process each trace
            for i, trace in enumerate(traces, 1):
                infile.seek(trace['pos'])
                
                # Read and update trace header
                trace_header = bytearray(infile.read(240))
                trace_header[114:116] = struct.pack('>H', num_samples)
                outfile.write(trace_header)
                
                # Read and standardize samples
                actual_samples = min(trace['samples'], num_samples)
                sample_bytes = infile.read(actual_samples * 4)
                
                # Convert and write samples
                for j in range(0, len(sample_bytes), 4):
                    sample_bytes_chunk = sample_bytes[j:j+4].ljust(4, b'\x00')
                    try:
                        if data_format == 1:
                            sample = struct.unpack('>h', sample_bytes_chunk[:2])[0]
                        elif data_format == 2:
                            sample = struct.unpack('>l', sample_bytes_chunk)[0]
                        elif data_format in (3, 5):
                            sample = struct.unpack('>f', sample_bytes_chunk)[0]
                        else:
                            sample = 0
                    except struct.error:
                        sample = 0
                        
                    outfile.write(struct.pack('>f', float(sample)))
                
                # Pad remaining samples if needed
                remaining_samples = num_samples - actual_samples
                if remaining_samples > 0:
                    outfile.write(b'\x00' * (remaining_samples * 4))
                
                if i % 1000 == 0:
                    print(f"Processed {i}/{actual_traces} traces")
def analyze_segy_file(file_path):
    """Detailed SEGY file analysis"""
    with open(file_path, 'rb') as file:
        # Basic file info
        file_size = os.path.getsize(file_path)
        print("\nSEG-Y File Analysis Report")
        print("=" * 50)
        print(f"File size: {file_size:,} bytes")

        # Read headers
        textual_header = file.read(3200)
        binary_header = file.read(400)

        # Get binary header details
        header_info = get_binary_header_details(binary_header)
        print("\nBinary Header Information:")
        print("-" * 30)
        for key, value in header_info.items():
            print(f"{key}: {value}")

        # Get revision type
        rev_type = get_segy_revision(binary_header)
        print(f"\nSEG-Y Format: {rev_type}")

        # Calculate trace information
        sample_interval = header_info['sample_interval']
        num_samples = header_info['num_samples']
        format_code = header_info['format_code']
        trace_data_size = num_samples * 4  # Standard size
        trace_size = 240 + trace_data_size
        expected_traces = (file_size - 3600) // trace_size

        print("\nTrace Structure Analysis:")
        print("-" * 30)
        print(f"Sample interval: {sample_interval} microseconds")
        print(f"Samples per trace: {num_samples}")
        print(f"Data format code: {format_code}")
        print(f"Expected trace size: {trace_size} bytes")
        print(f"Expected number of traces: {expected_traces:,}")

        # Analyze actual traces
        file.seek(3600)
        actual_traces = 0
        trace_sizes = set()
        inline_range = set()
        xline_range = set()

        while file.tell() < file_size:
            try:
                trace_start = file.tell()
                trace_header = file.read(240)
                if len(trace_header) != 240:
                    break

                # Get trace header values
                trace_samples = struct.unpack('>H', trace_header[114:116])[0]
                inline_num = struct.unpack('>H', trace_header[188:190])[0]
                xline_num = struct.unpack('>H', trace_header[192:194])[0]

                actual_size = 240 + (trace_samples * 4)
                trace_sizes.add(actual_size)
                inline_range.add(inline_num)
                xline_range.add(xline_num)

                # Skip trace data
                file.seek(trace_start + actual_size)
                actual_traces += 1

            except Exception as e:
                print(f"Error reading trace {actual_traces}: {str(e)}")
                break

        print("\nActual Trace Analysis:")
        print("-" * 30)
        print(f"Actual traces found: {actual_traces:,}")
        print(f"Unique trace sizes: {len(trace_sizes)}")
        if len(trace_sizes) > 1:
            print("WARNING: Non-uniform trace sizes detected!")
            print(f"Size variations: {sorted(trace_sizes)}")
        
        print("\nInline/Crossline Analysis:")
        print("-" * 30)
        print(f"Inline range: {min(inline_range)} to {max(inline_range)}")
        print(f"Crossline range: {min(xline_range)} to {max(xline_range)}")
        print(f"Grid dimensions: {len(inline_range)}x{len(xline_range)}")

        # Validation summary
        print("\nValidation Summary:")
        print("-" * 30)
        issues = []
        if len(trace_sizes) > 1:
            issues.append("Non-uniform trace sizes")
        if actual_traces != expected_traces:
            issues.append(f"Trace count mismatch (Expected: {expected_traces}, Found: {actual_traces})")
        if format_code not in [1, 2, 3, 4, 5, 8]:
            issues.append(f"Unusual data format code: {format_code}")
        
        if issues:
            print("Issues found:")
            for issue in issues:
                print(f"- {issue}")
        else:
            print("No major issues detected")
def analyze_segy_parameters(input_file):
    """Extract standard parameters from SEGY file analysis"""
    with open(input_file, 'rb') as file:
        # Read headers
        file.seek(3200)  # Skip textual header
        binary_header = file.read(400)
        
        # Get basic parameters
        header_info = get_binary_header_details(binary_header)
        num_samples = header_info['num_samples']
        sample_interval = header_info['sample_interval']
        format_code = header_info['format_code']
        
        # Calculate trace size
        trace_header_size = 240  # Standard SEG-Y trace header size
        sample_size = 4  # We'll convert everything to 4-byte IEEE float
        trace_data_size = num_samples * sample_size
        trace_size = trace_header_size + trace_data_size
        
        return {
            'num_samples': num_samples,
            'sample_interval': sample_interval,
            'format_code': format_code,
            'trace_size': trace_size,
            'trace_header_size': trace_header_size,
            'sample_size': sample_size
        }
def standardize_segy_for_pzero(input_file, output_file):
    """Standardize SEGY file specifically for PZero compatibility"""
    # Get parameters from analysis
    params = analyze_segy_parameters(input_file)
    num_samples = params['num_samples']
    trace_size = params['trace_size']
    sample_interval = params['sample_interval']
    
    print(f"Using analyzed parameters:")
    print(f"- Samples per trace: {num_samples}")
    print(f"- Trace size: {trace_size} bytes")
    print(f"- Sample interval: {sample_interval} μs")
    
    with open(input_file, 'rb') as infile, open(output_file, 'wb') as outfile:
        # Read headers
        textual_header = infile.read(3200)
        binary_header = bytearray(infile.read(400))
        
        # Standard parameters
        
        # Calculate grid dimensions for inline/crossline
        file_size = os.path.getsize(input_file)
        total_traces = (file_size - 3600) // trace_size
        grid_size = int(np.sqrt(total_traces))
        
        # Update binary header for PZero compatibility
        binary_header[20:22] = struct.pack('>H', num_samples)  # Samples per trace
        binary_header[24:26] = struct.pack('>H', 5)  # IEEE float
        binary_header[16:18] = struct.pack('>H', 4003)  # Sample interval
        binary_header[300:302] = struct.pack('>H', 2)  # SEG-Y Rev 2
        
        # Write headers
        outfile.write(textual_header)
        outfile.write(binary_header)
        
        # Process traces with PZero-specific headers
        pos = 3600
        trace_count = 0
        
        for inline in range(grid_size):
            for xline in range(grid_size):
                if pos >= file_size:
                    break
                    
                infile.seek(pos)
                trace_header = bytearray(infile.read(240))
                
                if len(trace_header) != 240:
                    break
                
                # Update trace header for PZero
                # Inline number (bytes 189-190)
                trace_header[188:190] = struct.pack('>H', inline + 1)
                
                # Crossline number (bytes 193-194)
                trace_header[192:194] = struct.pack('>H', xline + 1)
                
                # CDP X coordinate (bytes 181-184)
                trace_header[180:184] = struct.pack('>l', inline * 100)
                
                # CDP Y coordinate (bytes 185-188)
                trace_header[184:188] = struct.pack('>l', xline * 100)
                
                # Number of samples (bytes 115-116)
                trace_header[114:116] = struct.pack('>H', num_samples)
                
                # Sample interval (bytes 117-118)
                trace_header[116:118] = struct.pack('>H', 4003)
                
                outfile.write(trace_header)
                
                # Process trace data
                data_size = num_samples * 4
                data = infile.read(data_size)
                
                if len(data) < data_size:
                    data = data.ljust(data_size, b'\x00')
                elif len(data) > data_size:
                    data = data[:data_size]
                
                outfile.write(data)
                
                trace_count += 1
                pos = infile.tell()
                
                if trace_count % 1000 == 0:
                    print(f"Processed {trace_count}/{total_traces} traces")
        
        # Update final trace count
        print(f"\nStandardization completed:")
        print(f"- Total traces: {trace_count}")
        print(f"- Grid size: {grid_size}x{grid_size}")
        print(f"- Samples per trace: {num_samples}")

def convert_to_standard_segy(input_file, output_file, normalize=False, clip=False):
    try:
        print("Analyzing input file...")
        analyze_segy_file(input_file)
        
        print("\nStandardizing file for PZero...")
        standardize_segy_for_pzero(input_file, output_file)
        
        print("\nAnalyzing output file...")
        analyze_segy_file(output_file)
        return True
    except Exception as e:
        print(f"Error during conversion: {str(e)}")
        return False
        
def start_conversion():
    input_file = input_file_path.get()
    output_file = output_file_path.get()
    normalize = normalize_var.get()
    clip = clip_var.get()

    if not input_file or not os.path.exists(input_file):
        messagebox.showerror("Error", "Please select a valid input file.")
        return
    if not output_file:
        messagebox.showerror("Error", "Please select output file location.")
        return

    try:
        convert_to_standard_segy(input_file, output_file, normalize, clip)
        messagebox.showinfo("Success", "Conversion completed successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred:\n{e}")



def browse_output_file():
    filename = filedialog.asksaveasfilename(
        title="Save SEGY file as",
        filetypes=[("SEGY files", "*.segy *.sgy"), ("All files", "*.*")],
        defaultextension=".sgy"
    )
    if filename:
        output_file_path.set(filename)
def browse_input_file():
    filename = filedialog.askopenfilename(
        title="Select SEGY file",
        filetypes=[("SEGY files", "*.segy *.sgy"), ("All files", "*.*")]
    )
    if filename:
        input_file_path.set(filename)
def browse_output_dir():
    dirname = filedialog.askdirectory(title="Select Output Directory")
    if dirname:
        output_dir_path.set(dirname)

def main():
    global input_file_path, output_file_path
    global normalize_var, clip_var

    root = tk.Tk()
    root.title("SEGY File Converter")

    # Initialize variables
    input_file_path = tk.StringVar()
    output_file_path = tk.StringVar()
    normalize_var = tk.BooleanVar()
    clip_var = tk.BooleanVar()

    # Create and layout widgets
    tk.Label(root, text="Input file:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
    tk.Entry(root, textvariable=input_file_path, width=50).grid(row=0, column=1, padx=5)
    tk.Button(root, text="Browse...", command=browse_input_file).grid(row=0, column=2, padx=5)

    tk.Label(root, text="Output file:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
    tk.Entry(root, textvariable=output_file_path, width=50).grid(row=1, column=1, padx=5)
    tk.Button(root, text="Browse...", command=browse_output_file).grid(row=1, column=2, padx=5)

    # Options frame
    options_frame = tk.LabelFrame(root, text="Options", padx=5, pady=5)
    options_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

    tk.Checkbutton(options_frame, text="Normalize data", variable=normalize_var).pack(side="left", padx=5)
    tk.Checkbutton(options_frame, text="Clip outliers", variable=clip_var).pack(side="left", padx=5)

    # Convert button
    tk.Button(root, text="Convert", command=start_conversion).grid(row=3, column=0, columnspan=3, pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()