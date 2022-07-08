# Robotic 3D Printing on Knitted Formwork

**Quick links:** [compas docs](https://compas-dev.github.io/main/) | [compas_fab docs](https://gramaziokohler.github.io/compas_fab/latest/)

## Requirements for Form-Finding

* [Rhinoceros 3D 7.0](https://www.rhino3d.com/): Update Rhino to the newest version
* Equilib (install EQlib and EQlib-Mkl via the Rhino Package Manager)
* [Karamba 3D](https://www.karamba3d.com/download/): Download the file and install the FREE version 

## Requirements

* [Rhinoceros 3D 7.0](https://www.rhino3d.com/)
* [Anaconda Python Distribution](https://www.anaconda.com/download/): 3.x
* Git: [official command-line client](https://git-scm.com/) or visual GUI (e.g. [Github Desktop](https://desktop.github.com/) or [SourceTree](https://www.sourcetreeapp.com/))
* [VS Code](https://code.visualstudio.com/) with the following `Extensions`:
  * `Python` (official extension)
  * `EditorConfig for VS Code` (optional)
  * `Docker` (official extension, optional)

## Set-up and Installation

### 1. Setting up the Anaconda environment with COMPAS

#### Execute the commands below in Anaconda Prompt as Administator:
	
    (base) conda config --add channels conda-forge
    (base) conda create -n robknit compas_fab --yes
    (base) conda activate robknit
    
#### Verify Installation
    (robknit) pip show compas_fab

####
    Name: compas-fab
    Version: 0.xx
    Summary: Robotic fabrication package for the COMPAS Framework
    ...

#### Install on Rhino

    (robknit) python -m compas_rhino.install -v 7.0


### 2. Installation of Dependencies

    (robknit) conda install git

### 3. Cloning and installing the Course Repository

* Create a workspace directory: C:\Users\YOUR_USERNAME\workspace
* Open Github Desktop, clone the [robotic_knitcrete](https://github.com/augmentedfabricationlab/robotic_knitcrete) repository into you workspace folder 
* Install within your env (in editable mode):

    (robknit) cd C:\Users\YOUR_USERNAME\workspace
    (robknit) python -m pip install -e robotic_knitcrete
    (robknit) python -m compas_rhino.install -p robotic_knitcrete -v 7.0

### 4. Notes on RPC:

Careful: RPC (Remote Procedure Call) for calling numpy functions from within Rhino, is using the CPython Interpreter of the latest installed environment, not defined specifically. If another interpreter should be used, this can be defined when creating the Proxy object.

### Credits


