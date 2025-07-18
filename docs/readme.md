# README

The system is designed as a pipeline that takes a high-level prompt for a Linux device driver, generates C code using multiple AI models, and then subjects the generated code to a series of evaluations.

## How to run the pipeline:

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/cvsaisreenivasreddy/linux_device_driver_evaluator.git](https://github.com/cvsaisreenivasreddy/linux_device_driver_evaluator.git)
    cd linux_device_driver_evaluator/Linux_device_driver_evaluator-main
    ```
2.  **Create and activate your virtual environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```
3.  **Install required packages:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Create a file named `.env` and set up your API key:**
    ```
    API="YOUR_GEMINI_API_KEY"
    ```
5.  **Finally run:**
    ```bash 
    python get_responses.py
    python score.py
    ```

## Note:

**Execution Requirement**

**Important**: This tool builds Linux kernel modules and must be run in a Linux environment.
If you are on Windows or macOS, please use a virtual machine (e.g., VirtualBox, Multipass, or WSL 2) to run the code.

**The json results which are existing in the evaluators folder are generated on dummy driver codes given to test the each evaluator individually**
**The file evaluation results is original results file evaluated on 2 models for 3 prompts**  

## AI Usage: 
* I used chatgpt and gemini 2.5 pro for understanding the best evaluation process,code snippets and functions
* Github copilot autofilled the code sometimes 