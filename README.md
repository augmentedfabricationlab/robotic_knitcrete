# UR Robot Simulation and Control Environment

**Quick links:** [compas docs](https://compas-dev.github.io/main/) | [compas_fab docs](https://gramaziokohler.github.io/compas_fab/latest/)

## Requirements

* [Rhinoceros 3D 7.0](https://www.rhino3d.com/)
* [Anaconda Python Distribution](https://www.anaconda.com/download/): 3.x
* [Docker Community Edition](https://www.docker.com/get-started): Download it for [Windows Pro](https://store.docker.com/editions/community/docker-ce-desktop-windows). Leave "switch Linux containers to Windows containers" disabled.
* X11 Server: On Windows use [XMing](https://sourceforge.net/projects/xming/), on Mac use [XQuartz](https://www.xquartz.org/) (see details [here](https://medium.com/@mreichelt/how-to-show-x11-windows-within-docker-on-mac-50759f4b65cb)).
* Git: [official command-line client](https://git-scm.com/) or visual GUI (e.g. [Github Desktop](https://desktop.github.com/) or [SourceTree](https://www.sourcetreeapp.com/))
* [VS Code](https://code.visualstudio.com/) with the following `Extensions`:
  * `Python` (official extension)
  * `EditorConfig for VS Code` (optional)
  * `Docker` (official extension, optional)

## Set-up and Installation

### 1. Setting up the Anaconda environment with COMPAS

#### Execute the commands below in Anaconda Prompt as Administator:
	
    (base) conda config --add channels conda-forge
    (base) conda create -n your_env_name compas_fab --yes
    (base) conda activate your_env_name
    
#### Verify Installation
    (your_env_name) pip show compas_fab

####
    Name: compas-fab
    Version: 0.xx
    Summary: Robotic fabrication package for the COMPAS Framework
    ...

#### Install on Rhino

    (your_env_name) python -m compas_rhino.install -v 7.0


### 2. Installation of Dependencies

    (your_env_name) conda install git

#### AM Information Model
    
    (your_env_name) python -m pip install git+https://github.com/augmentedfabricationlab/am_information_model@master#egg=am_information_model
    (your_env_name) python -m compas_rhino.install -p am_information_model -v 7.0

#### UR Fabrication Control
    
    (your_env_name) python -m pip install git+https://github.com/augmentedfabricationlab/ur_fabrication_control@master#egg=ur_fabrication_control
    (your_env_name) python -m compas_rhino.install -p ur_fabrication_control -v 7.0


### 3. Cloning and installing the Course Repository

* Create a workspace directory: C:\Users\YOUR_USERNAME\workspace
* Open Github Desktop, clone the [robotic_knitcrete](https://github.com/augmentedfabricationlab/robotic_knitcrete) repository into you workspace folder 
* Install within your env (in editable mode):

    (your_env_name) pip install -e your_filepath_to_robotic_knitcrete
    (your_env_name) python -m compas_rhino.install -p robotic_knitcrete -v 7.0

### 4. Notes on RPC:

Careful: RPC (Remote Procedure Call) for calling numpy functions from within Rhino, is using the CPython Interpreter of the latest installed environment, not defined specifically. If another interpreter should be used, this can be defined when creating the Proxy object.

### Credits


