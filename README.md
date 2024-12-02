# SEGY File Converter


## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
  - [Launching the Application](#launching-the-application)
  - [GUI Overview](#gui-overview)
  - [Conversion Process](#conversion-process)
- [Functionality](#functionality)
  - [SEGY File Validation](#segy-file-validation)
  - [Standardization for PZero Compatibility](#standardization-for-pzero-compatibility)
  - [Trace Analysis](#trace-analysis)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [License](#license)
- [Contributing](#contributing)
- [Acknowledgements](#acknowledgements)
- [Contact](#contact)

## Introduction

The **SEGY File Converter** is a user-friendly Python application designed to validate and standardize SEGY (Standard for the Exchange of Geophysical Data) files. Whether you're a geophysicist, data analyst, or developer working with seismic data, this tool ensures your SEGY files adhere to industry standards, specifically tailoring them for PZero compatibility.

## Features

- **Graphical User Interface (GUI):** Intuitive interface built with Tkinter for easy file selection and conversion.
- **Comprehensive SEGY Validation:** Checks file integrity, trace consistency, and header correctness.
- **Standardization for PZero:** Converts non-standard SEGY files to the SEG-Y Rev 2 format compatible with PZero software.
- **Detailed Analysis Reports:** Provides in-depth information about the SEGY file structure, trace counts, and potential issues.
- **Error Handling:** Robust mechanisms to handle and report errors during the conversion process.

## Requirements

- **Operating System:** Windows, macOS, or Linux
- **Python Version:** Python 3.6 or higher
- **Dependencies:**
  - `numpy`
  - `tkinter` (usually included with Python)
  
## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/yourusername/segy-file-converter.git
   cd segy-file-converter
   ```

2. **Create a Virtual Environment (Optional but Recommended):**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Required Dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

   *If `requirements.txt` is not provided, install dependencies manually:*

   ```bash
   pip install numpy
   ```

4. **Ensure Tkinter is Installed:**

   Tkinter usually comes pre-installed with Python. To verify, run:

   ```python
   python -m tkinter
   ```

   A small window should appear. If not, install Tkinter:

   - **Ubuntu/Debian:**

     ```bash
     sudo apt-get install python3-tk
     ```

   - **macOS:**

     Tkinter is included with Python installations from [python.org](https://www.python.org/).

   - **Windows:**

     Tkinter is included with the standard Python installer.

## Usage

### Launching the Application

Navigate to the directory containing the `segy_converter.py` script and run:

```bash
python segy_converter.py
```

### GUI Overview

Upon launching, the application window presents the following components:

1. **Input File Selection:**
   - **Label:** "Input file:"
   - **Entry Field:** Displays the path to the selected SEGY file.
   - **Browse Button:** Opens a file dialog to select the SEGY file.

2. **Output File Selection:**
   - **Label:** "Output file:"
   - **Entry Field:** Displays the desired path for the standardized SEGY file.
   - **Browse Button:** Opens a save dialog to specify the output file location and name.

3. **Options:**
   - **Normalize Data:** Checkbox to normalize the seismic data.
   - **Clip Outliers:** Checkbox to clip outlier values in the data.

4. **Convert Button:**
   - Initiates the conversion and standardization process.

### Conversion Process

1. **Select Input File:**
   - Click the "Browse..." button next to "Input file" to select the non-standard SEGY file you wish to convert.

2. **Specify Output File:**
   - Click the "Browse..." button next to "Output file" to choose where to save the standardized SEGY file. Ensure the file extension is `.segy` or `.sgy`.

3. **Choose Options (Optional):**
   - **Normalize Data:** If checked, the seismic data will be normalized.
   - **Clip Outliers:** If checked, extreme values in the data will be clipped to reduce noise.

4. **Start Conversion:**
   - Click the "Convert" button. A progress message will appear upon successful completion or display an error message if issues arise.

## Functionality

### SEGY File Validation

Before standardization, the application performs a thorough validation of the SEGY file:

- **Header Verification:** Checks both textual (3200 bytes) and binary (400 bytes) headers for correctness and standard compliance.
- **Trace Consistency:** Ensures that all traces have uniform sizes and the expected number of traces matches the file size.
- **Format Code Check:** Validates the data sample format codes to ensure compatibility.

### Standardization for PZero Compatibility

The core functionality involves converting non-standard SEGY files into the SEG-Y Rev 2 format tailored for PZero software:

- **Header Updates:** Modifies binary headers to set the revision number, sample interval, data format, and other essential fields.
- **Trace Header Adjustments:** Updates inline and crossline numbers, CDP coordinates, and sample information in each trace header.
- **Data Formatting:** Converts all data samples to 4-byte IEEE floating-point format, ensuring consistency across the dataset.

### Trace Analysis

Provides detailed insights into the trace structure of the SEGY file:

- **Trace Count:** Compares expected versus actual number of traces.
- **Trace Sizes:** Detects and reports non-uniform trace sizes.
- **Inline/Crossline Ranges:** Analyzes the range and grid dimensions of inline and crossline numbers.

## Examples

### Example 1: Standardizing a SEGY File

1. **Select Input File:**

   ![Input File Selection](https://example.com/input_file_selection.png)

2. **Specify Output File:**

   ![Output File Selection](https://example.com/output_file_selection.png)

3. **Choose Options:**

   ![Options Selection](https://example.com/options_selection.png)

4. **Conversion Success:**

   ![Conversion Success](https://example.com/conversion_success.png)

### Example 2: Handling Errors

If the selected SEGY file is corrupted or does not conform to expected standards, an error message will appear:

![Error Message](https://example.com/error_message.png)

## Troubleshooting

- **Tkinter Not Found:**
  - Ensure Tkinter is installed. Refer to the [Installation](#installation) section.

- **Permission Denied Errors:**
  - Run the application with appropriate permissions or choose output directories where you have write access.

- **Unsupported SEGY Format Codes:**
  - The application currently supports standard data format codes (1, 2, 3, 4, 5, 8). If your SEGY file uses a different format code, consider converting it to a supported format before using this tool.

- **Conversion Takes Too Long:**
  - For very large SEGY files, the conversion process might be time-consuming. Ensure your system has sufficient resources and consider processing smaller batches if possible.

- **Inconsistent Trace Sizes:**
  - The application will report non-uniform trace sizes. Ensure your SEGY file is correctly formatted or use preprocessing tools to rectify trace inconsistencies.

## License

This project is licensed under the [GNPU](LICENSE). You are free to use, modify, and distribute this software as per the terms of the license.

## Contributing

Contributions are welcome! If you encounter bugs or have feature requests, please open an issue or submit a pull request.

1. **Fork the Repository**
2. **Create a Feature Branch**

   ```bash
   git checkout -b feature/YourFeature
   ```

3. **Commit Your Changes**

   ```bash
   git commit -m "Add your feature"
   ```

4. **Push to the Branch**

   ```bash
   git push origin feature/YourFeature
   ```

5. **Open a Pull Request**

## Acknowledgements

- **Python Developers:** For creating and maintaining Python and its libraries.
- **Tkinter Community:** For providing comprehensive documentation and support for Tkinter.
- **SEGY Standards Committee:** For defining the SEGY format, facilitating data exchange in geophysics.

## Contact

For any questions, issues, or suggestions, please contact:

- **Email:** waqas.hussain@unimib.it
- **GitHub Issues:** [https://github.com/waqashussain117//segy-file-converter/issues](https://github.com/yourusername/segy-file-converter/issues)

