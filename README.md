# VasoTracker 2.2 - Blood Vessel Diameter Tracking Software (online and offline analysis)

The VasoTracker 2.2 software is a comprehensive software solution designed for the acquisition and analysis of blood vessel imaging data. It supports both live and pre-recorded video analysis, making it adaptable for various experimental set ups. It was initially developed for pressure myography, but it works for many other types of imaging!

![til](https://github.com/VasoTracker/VasoTracker-2-Software/blob/main/VasoTracker%20GUI.gif)



## Table of Contents
- [What's New in v2.2](#whats-new-in-v22)
- [Key Features](#key-features)
- [Installation Instructions](#vasotracker-installation-instructions)
  - [Executable File](#option-1-installing-and-running-from-the-executable-file)
  - [From Source (Windows)](#option-2-installing-from-source-using-anaconda)
  - [macOS](#option-3-installing-on-macos)
- [License](#license)
- [Issues](#issues)

---

## What's New in v2.2 (January 2026)

* **Native OpenCV Camera Support:** Use any USB camera or webcam directly without configuration - just select "OpenCV" from the camera dropdown.
* **Automatic Micro-Manager Installation:** No more manual prerequisites - Micro-Manager components are automatically downloaded on first run.
* **Python 3.11:** Updated to Python 3.11 for improved performance and compatibility.
* **Background Arduino Polling:** Improved responsiveness when using Arduino-based pressure and temperature monitoring.
* **Large File Handling:** Automatic file splitting for long recordings to prevent oversized TIFF files.

---

## Key Features

* **Software Base:** Now using μManager 2.0.
* **Programming Language:** Updated to Python 3.11 for better performance and compatibility.
* **Live Data Acquisition:** Allows for the real-time display of pressurized arteries mounted in the VasoTracker vessel chamber.
* **Diameter Measurement:** Real-time measurement and display of both outer and inner artery diameters.
* **Multiple Tracking Algorithms:** Allow accurate tracking of brightfield or fluorscence imaging data.
* **Environmental Monitoring:** Continuously tracks bath temperature and intraluminal pressure.
* **Data Recording:** Live recording and graphing of artery diameters.
* **Experimental Tracking:** Facilitates the tracking of experimental manipulations, such as drug additions.
* **Advanced Tracking Options:** Includes multi-line diameter tracking and the ability to specify regions of interest (ROI).
* **Data Analysis:** Implements line averaging and statistical filtering to refine results.
* **Pressure Control:** Integrates with National Instruments DAQ boards, enabling automatic control of Living Systems PS-200 pressure servo systems.
* **Video Output:** Supports exporting data to .tiff files for further analysis.

---

## VasoTracker Installation Instructions

VasoTracker can be installed using either the standalone executable file for straightforward setup or from the source code for more advanced customization options. Below are the steps for both methods.

### Option 1: Installing and Running from the Executable File

***This method is recommended for most users.***

#### Steps:

1. **Download the latest VasoTracker release:**
   - Visit the [VasoTracker Releases Page](https://github.com/VasoTracker/VasoTracker-2/releases) and download the latest zip file for your operating system.

2. **Extract the Zip File:**
   - Locate the downloaded zip file on your computer.
   - Right-click the file and select "Extract All..." or use your preferred extraction software.
   - Choose a destination folder to extract the files and confirm the action.

3. **Run VasoTracker:**
   - Navigate to the extracted folder.
   - Double-click the executable file to start the application.
   - **On first run**, VasoTracker will automatically download and install the required Micro-Manager components. This may take a few minutes.

#### Using Webcams and USB Cameras

VasoTracker supports Basler and Thorlabs cameras out of the box. For webcams and USB cameras, you have two options:

**Option 1: Native OpenCV (Recommended)**
- Simply select **"OpenCV"** from the camera dropdown
- Works immediately with any USB camera or webcam
- No configuration required

**Option 2: Micro-Manager Configuration (Advanced)**

For cameras requiring specific Micro-Manager device adapters:

1. **Open Micro-Manager** (automatically installed by VasoTracker):
   ```
   C:\Users\<YourName>\AppData\Local\pymmcore-plus\pymmcore-plus\mm\<version>\ImageJ.exe
   ```

2. **Create a hardware configuration:**
   - Go to **Devices > Hardware Configuration Wizard**
   - Add your camera device
   - Complete the wizard and save the configuration

3. **Save the config file:**
   - Save as `MMConfig.cfg` in your VasoTracker folder

4. **Select your camera in VasoTracker:**
   - Choose "MMConfig" as your camera type

### Option 2: Installing from Source Using Anaconda

***For users who need more control over the installation environment or wish to contribute to the software development.***

#### Steps:

1. **Clone the Repository:**
   - Clone the VasoTracker repository to your local machine using:
     ```
     git clone https://github.com/VasoTracker/VasoTracker-2-Software.git
     ```

2. **Set Up the Anaconda Environment:**
   - Navigate to the directory where you cloned the repository.
   - Use the provided `environment.yml` file to create the VasoTracker Anaconda environment:
     ```
     conda env create -f environment.yml
     ```

3. **Activate the Environment:**
   - Activate the newly created environment:
     ```
     conda activate vasotracker2
     ```

4. **Install Micro-Manager Components:**
   - Install the required Micro-Manager device adapters:
     ```
     mmcore install
     ```

5. **Run VasoTracker:**
   - Navigate to the vasotracker_2 folder and run:
     ```
     cd vasotracker_2
     python vasotracker_2.py
     ```

This approach ensures you have a development environment configured with all necessary dependencies, allowing you to modify or use VasoTracker immediately.

---

### Option 3: Installing on macOS

***VasoTracker runs from source on macOS. The macOS version supports all core features including live and offline vessel tracking, Arduino-based temperature/pressure monitoring, and USB/webcam cameras via OpenCV. National Instruments DAQmx pressure control is not available on macOS.***

#### Prerequisites

- **Anaconda or Miniconda** — [Download here](https://www.anaconda.com/download)
- **Tkinter for Python 3.11** — install via Homebrew if missing:
  ```
  brew install python-tk@3.11
  ```

#### Steps

1. **Clone the Repository:**
   ```
   git clone https://github.com/VasoTracker/VasoTracker-2-Software.git
   cd VasoTracker-2-Software
   ```

2. **Create the macOS Conda Environment:**
   ```
   conda env create -f vasotracker_2/environment_macos.yml
   conda activate vasotracker2
   ```

3. **Install Micro-Manager Components:**
   ```
   mmcore install
   ```

4. **Run VasoTracker:**
   ```
   cd vasotracker_2
   python vasotracker_2.py
   ```

#### macOS-Specific Notes

- **Camera permissions:** On first launch, macOS will ask for camera access. Go to **System Settings → Privacy & Security → Camera** and enable access for Terminal (or your Python environment) if the camera does not appear.

- **Arduino permissions:** Plug in your Arduino before launching VasoTracker. On macOS the device will appear as `/dev/cu.usbmodem*`. No extra drivers are needed for most Arduino boards. If the port is not detected, ensure the correct USB driver is installed (e.g., CH340 driver for some clone boards).

- **Pressure control (NI-DAQmx):** The National Instruments DAQmx library and the associated PyDAQmx Python package are Windows-only. Automatic pressure control via NI DAQ hardware is therefore not available on macOS. All other features work normally.

- **Window icon:** The `.ICO` icon format is not supported on macOS; this is handled automatically and does not affect functionality.

#### Building a macOS App Bundle (Advanced)

To package VasoTracker as a standalone `.app` for distribution:

1. Activate the `vasotracker2` conda environment.
2. From the `vasotracker_2` folder, run:
   ```
   pyinstaller vasotracker_2_macos.spec
   ```
3. The built application will be in `dist/VasoTracker_<version>.app`.

---

## License

Distributed under the terms of the [The 3-Clause BSD License]

"VasoTracker" is free and open source software

---

## Issues

If you encounter any problems, please [file an issue] along with a detailed description.

[μManager 2.0]: https://micro-manager.org/
[The 3-Clause BSD License]: http://opensource.org/licenses/BSD-3-Clause

#### Added Fund

Sometimes, a little bit of Pac-Man or Space Invaders is required. We included these games courtesy of:

   - [Whoever created PacManCode](https://pacmancode.com/)
   - [Lee Rob on GitHub](https://github.com/leerob/space-invaders)
