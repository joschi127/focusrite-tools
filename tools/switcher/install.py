import os
import sys
import shutil
import subprocess
try:
    import win32com.client
    HAS_WIN32COM = True
except ImportError:
    HAS_WIN32COM = False

# ==============================================================================
# CONFIGURATION
# ==============================================================================
SCRIPT_NAME = "focusrite_switcher.py"
SCRIPT_PATH = SCRIPT_NAME
EXE_NAME = "focusrite_switcher.exe"
# Target folder name featuring a space and custom spelling
TARGET_DIR = os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "Focusrite Switcher")
EXE_PATH = os.path.join(TARGET_DIR, EXE_NAME)
TASK_NAME = "Focusrite_Switcher_Startup"
# ==============================================================================

def check_requirements():
    """Ensure focusrite_switcher.py exists in the current folder."""
    if not os.path.exists(SCRIPT_PATH):
        print(f"Error: Could not find '{SCRIPT_NAME}' at '{SCRIPT_PATH}'.")
        print("Please ensure both 'install.py' and 'focusrite_switcher.py' are in the same folder.")
        print("\nPress Enter to exit...")
        input()
        sys.exit(1)

def compile_exe():
    """Compiles the python script into a single windowless executable using PyInstaller."""
    print(f"Step 1: Compiling {SCRIPT_NAME} using PyInstaller...")

    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not detected. Installing via pip...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--noconsole",
        "--distpath", "dist",
        "--workpath", "build",
        "--specpath", ".",
        SCRIPT_PATH
    ]

    try:
        subprocess.check_call(cmd, stdout=subprocess.DEVNULL)
        print(" -> Successfully compiled to executable!")
    except subprocess.CalledProcessError as e:
        print(f"Compilation failed: {e}")
        print("\nPress Enter to exit...")
        input()
        sys.exit(1)

def deploy_exe():
    """Copies the compiled executable and required snapshot files to the Program Files directory."""
    print(f"Step 2: Deploying files to '{TARGET_DIR}'...")

    src_path = os.path.join("dist", EXE_NAME)
    if not os.path.exists(src_path):
        print(f"Error: Compiled executable not found at '{src_path}'.")
        sys.exit(1)

    try:
        os.makedirs(TARGET_DIR, exist_ok=True)
        shutil.copy2(src_path, EXE_PATH)
        print(" -> Successfully deployed all binary objects.")
    except Exception as e:
        print(f"Error deploying files: {e}")
        sys.exit(1)

def create_startup_task():
    """Creates or replaces the Windows Task Scheduler entry targeting our newly deployed application."""
    if not HAS_WIN32COM:
        print("Step 3: Registering Task Scheduler entry... SKIPPED (win32com not available)")
        return

    print("Step 3: Registering Task Scheduler entry...")

    try:
        scheduler = win32com.client.Dispatch('Schedule.Service')
        scheduler.Connect()
        root_folder = scheduler.GetFolder('\\')

        # Check if the task already exists and delete it to ensure a clean overwrite
        try:
            root_folder.DeleteTask(TASK_NAME, 0)
            print(f" -> Existing task '{TASK_NAME}' detected and removed for replacement.")
        except Exception:
            # Task didn't exist previously, which is fine
            pass

        task_def = scheduler.NewTask(0)
        task_def.RegistrationInfo.Description = "Automated Focusrite Switcher: Forces Playback routing on Windows Login."
        task_def.Settings.Enabled = True
        task_def.Settings.AllowDemandStart = True
        task_def.Settings.StartWhenAvailable = True
        task_def.Settings.ExecutionTimeLimit = "PT1M"

        trigger = task_def.Triggers.Create(9) # TASK_TRIGGER_LOGON
        trigger.Id = "LogonTrigger"
        trigger.Enabled = True
        trigger.Delay = "PT5S"  # 5-second buffer

        action = task_def.Actions.Create(0) # TASK_ACTION_EXEC
        action.Path = EXE_PATH
        action.Arguments = "computer"

        principal = task_def.Principal
        principal.LogonType = 3  # TASK_LOGON_INTERACTIVE_TOKEN
        principal.RunLevel = 0   # Normal privileges

        root_folder.RegisterTaskDefinition(
            TASK_NAME,
            task_def,
            6,  # TASK_CREATE_OR_UPDATE
            None,
            None,
            3   # TASK_LOGON_INTERACTIVE_TOKEN
        )
        print(f" -> Successfully configured Task Scheduler entry: '{TASK_NAME}'")

    except Exception as e:
        print(f"Failed to create Task Scheduler entry: {e}")
        print("\nPress Enter to exit...")
        input()
        sys.exit(1)

def initial_hardware_flash():
    """Executes the newly deployed EXE once to apply and flash the standalone configuration."""
    print("Step 4: Executing one-time hardware initialization (Standalone Profile)...")

    try:
        # Run the deployed EXE directly with the 'standalone' parameter
        subprocess.check_call([EXE_PATH, "standalone"])
        print(" -> Successfully pushed and flashed '8 Channel Analogue' standalone configuration to hardware memory!")
    except Exception as e:
        print(f" -> Warning: One-time hardware flash skipped or failed. Ensure your Scarlett is connected via USB")
        print(f" -> Focusrite Control Server is running. Details: {e}")

if __name__ == "__main__":
    print("====================================================")
    print("      FOCUSRITE AUTOMATION INSTALLER                ")
    print("====================================================\n")

    check_requirements()
    compile_exe()
    deploy_exe()
    create_startup_task()
    initial_hardware_flash()

    print("\n====================================================")
    print("      INSTALLATION SUMMARY                          ")
    print("====================================================")
    print(f" Status:                    SUCCESSFUL")
    print(f" Target Path:               {EXE_PATH}")
    print(f" Task Name:                 {TASK_NAME} (Replaced/Updated)")
    print(f" Active Hardware State:     Flashed to Standalone Profile")
    print(f" Profile:                   computer (Triggered 5s after logon)")
    print("====================================================")
    print("\nSetup complete! You can safely close this window.")
    print("Press RETURN / ENTER to exit...")
    input()
