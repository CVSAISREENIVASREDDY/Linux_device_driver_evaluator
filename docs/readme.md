The system is designed as a pipeline that takes a high-level prompt for a Linux device driver, generates C code using multiple AI models, and then subjects the generated code to a series of evaluations.

How to run the pipeline :

    git clone https://github.com/cvsaisreenivasreddy/linux_device_driver_evaluator.git
    cd linux_device_driver_evaluator/Linux_device_driver_evaluator-main  

    python3 -m venv .venv
    source .venv/bin/activate

    pip install requirements.txt 

    Create a file named .env and setup your api key 
    API="YOUR_GEMINI_API_KEY" 

    python3 score.py   

Note:
    Execution Requirement
    Important: This tool builds Linux kernel modules and must be run in a Linux environment.
    If you are on Windows or macOS, please use a virtual machine (e.g., VirtualBox, Multipass, or WSL 2) to run the code. 
    